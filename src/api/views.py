import secrets

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from django.utils import timezone

from rest_framework import serializers, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from core.tasks import send_activation_email

User = get_user_model()

# Grupo al que se suma a todo usuario auto-registrado al activar su cuenta.
REGISTRATION_GROUP_NAME = 'CLIENT'


def _gen_activation_code():
    """Código de activación numérico de 6 dígitos (000000–999999)."""
    return f'{secrets.randbelow(10 ** 6):06d}'


def _set_activation_code(profile):
    """Genera y guarda un código nuevo en el perfil; lo devuelve."""
    code = _gen_activation_code()
    profile.activation_code = code
    profile.activation_code_expires = timezone.now() + timezone.timedelta(
        minutes=settings.ACTIVATION_CODE_TTL_MINUTES
    )
    profile.activation_attempts = 0
    profile.save(update_fields=[
        'activation_code', 'activation_code_expires', 'activation_attempts', 'update_date',
    ])
    return code


def _serialize_user(user):
    """Representación común del usuario, incluye la foto de perfil."""
    profile = getattr(user, 'profile', None)
    return {
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'is_staff': user.is_staff,
        'profile_picture_url': profile.profile_picture_url if profile else None,
        'groups': list(user.groups.values_list('name', flat=True)),
    }


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Login con email + password. Resuelve el email al usuario y delega
    en simplejwt. Incluye los datos del usuario en la respuesta.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Reemplaza el campo username por email en el body del login.
        self.fields['email'] = serializers.EmailField()
        self.fields.pop(self.username_field, None)

    @classmethod
    def get_token(cls, user):
        # Claims extra dentro del JWT de acceso/refresh.
        token = super().get_token(user)
        token['groups'] = list(user.groups.values_list('name', flat=True))
        return token

    def validate(self, attrs):
        email = attrs.pop('email', None)
        try:
            user_obj = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            raise serializers.ValidationError(
                'No active account found with the given credentials'
            )
        except User.MultipleObjectsReturned:
            user_obj = User.objects.filter(email__iexact=email).order_by('id').first()

        attrs[self.username_field] = user_obj.get_username()
        data = super().validate(attrs)

        # Marcar al usuario como participante en su primer login → aparece en el ranking.
        from core.models import UserProfile
        profile, _ = UserProfile.objects.get_or_create(user=self.user)
        if not profile.is_participant:
            profile.is_participant = True
            profile.save(update_fields=['is_participant', 'update_date'])

        data['user'] = _serialize_user(self.user)
        return data


class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Login con email + password.
    Devuelve access token, refresh token y datos básicos del usuario.
    """
    serializer_class = CustomTokenObtainPairSerializer
    permission_classes = [AllowAny]


class HelloWorldView(APIView):
    """
    Retorna un saludo simple.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({'message': 'HOLA MUNDO'}, status=status.HTTP_200_OK)


class ProfileView(APIView):
    """
    Devuelve los datos del usuario autenticado.
    Requiere header: Authorization: Bearer <access_token>
    """
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        responses={
            200: openapi.Response(
                description="Datos del usuario autenticado",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'id':                  openapi.Schema(type=openapi.TYPE_INTEGER),
                        'username':            openapi.Schema(type=openapi.TYPE_STRING),
                        'email':               openapi.Schema(type=openapi.TYPE_STRING),
                        'first_name':          openapi.Schema(type=openapi.TYPE_STRING),
                        'last_name':           openapi.Schema(type=openapi.TYPE_STRING),
                        'is_staff':            openapi.Schema(type=openapi.TYPE_BOOLEAN),
                        'profile_picture_url': openapi.Schema(type=openapi.TYPE_STRING),
                        'groups':              openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Items(type=openapi.TYPE_STRING)),
                    },
                ),
            ),
        }
    )
    def get(self, request):
        return Response(_serialize_user(request.user))


def _issue_login_tokens(user):
    """Tokens definitivos (access + refresh con el claim `groups`) + datos del user."""
    refresh = CustomTokenObtainPairSerializer.get_token(user)
    return {
        'access': str(refresh.access_token),
        'refresh': str(refresh),
        'user': _serialize_user(user),
    }


# ── Auto-registro con activación por email ──────────────────────────────────────

class RegisterSerializer(serializers.Serializer):
    """Valida los datos del auto-registro: Nombre, Correo y Contraseña."""
    first_name = serializers.CharField(max_length=150, label='Nombre')
    email = serializers.EmailField(label='Correo')
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})

    def validate_email(self, value):
        return value.strip().lower()

    def validate_password(self, value):
        try:
            validate_password(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages))
        return value


class RegisterView(APIView):
    """
    Auto-registro de un usuario nuevo.

    POST /api/register/  { first_name, email, password }

    Crea el usuario `is_active=False` y le manda un mail con un código de
    activación de 6 dígitos. Si el email ya existe y está activo → 400.
    Si existe pero está inactivo → regenera el código y reenvía el mail.
    """
    permission_classes = [AllowAny]

    @swagger_auto_schema(request_body=RegisterSerializer)
    def post(self, request):
        from core.models import UserProfile

        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        email = data['email']

        existing = User.objects.filter(email__iexact=email).first()
        if existing:
            if existing.is_active:
                return Response(
                    {'detail': 'Ya existe una cuenta activa con ese correo.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            # Cuenta pendiente de activar → regenera el código y reenvía el mail.
            profile, _ = UserProfile.objects.get_or_create(user=existing)
            code = _set_activation_code(profile)
            send_activation_email.delay(existing.id, code)
            return Response(
                {'detail': 'Esa cuenta ya estaba registrada. Te reenviamos un código nuevo.'},
                status=status.HTTP_200_OK,
            )

        with transaction.atomic():
            user = User(
                username=email,
                email=email,
                first_name=data['first_name'],
                is_active=False,
            )
            user.set_password(data['password'])
            user.save()
            profile, _ = UserProfile.objects.get_or_create(user=user)
            code = _set_activation_code(profile)

        send_activation_email.delay(user.id, code)

        return Response(
            {'detail': 'Registro exitoso. Te enviamos un código a tu correo para activar la cuenta.'},
            status=status.HTTP_201_CREATED,
        )


class ActivateSerializer(serializers.Serializer):
    """Valida el cuerpo de la activación: correo + código de 6 dígitos."""
    email = serializers.EmailField(label='Correo')
    code = serializers.RegexField(r'^\d{6}$', label='Código')

    def validate_email(self, value):
        return value.strip().lower()


class ActivateView(APIView):
    """
    Activa la cuenta a partir del código del mail.

    POST /api/activate/  { email, code }

    Verifica el código (no vencido, intentos disponibles, coincide), pone
    `is_active=True`, suma al usuario al grupo CLIENT y lo marca como
    participante. Devuelve los tokens definitivos (access + refresh).
    """
    permission_classes = [AllowAny]

    @swagger_auto_schema(request_body=ActivateSerializer)
    def post(self, request):
        from core.models import UserProfile

        serializer = ActivateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        code = serializer.validated_data['code']

        invalid = Response(
            {'detail': 'Correo o código incorrecto.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

        user = User.objects.filter(email__iexact=email).first()
        if not user:
            return invalid

        # Nunca emitir tokens sin verificar el código (evita bypass de cuentas activas).
        if user.is_active:
            return Response(
                {'detail': 'La cuenta ya está activa. Iniciá sesión.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        profile, _ = UserProfile.objects.get_or_create(user=user)

        if not profile.activation_code or not profile.activation_code_expires:
            return invalid

        if timezone.now() > profile.activation_code_expires:
            return Response(
                {'detail': 'El código venció. Pedí uno nuevo desde la app.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if profile.activation_attempts >= settings.ACTIVATION_MAX_ATTEMPTS:
            return Response(
                {'detail': 'Demasiados intentos. Pedí un código nuevo desde la app.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if code != profile.activation_code:
            profile.activation_attempts += 1
            profile.save(update_fields=['activation_attempts', 'update_date'])
            restantes = max(0, settings.ACTIVATION_MAX_ATTEMPTS - profile.activation_attempts)
            return Response(
                {'detail': f'Código incorrecto. Te quedan {restantes} intento(s).'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Código correcto → activar.
        with transaction.atomic():
            user.is_active = True
            user.save(update_fields=['is_active'])

            group, _ = Group.objects.get_or_create(name=REGISTRATION_GROUP_NAME)
            user.groups.add(group)

            profile.is_participant = True
            profile.activation_code = None
            profile.activation_code_expires = None
            profile.activation_attempts = 0
            profile.save(update_fields=[
                'is_participant', 'activation_code', 'activation_code_expires',
                'activation_attempts', 'update_date',
            ])

        return Response(_issue_login_tokens(user), status=status.HTTP_200_OK)
