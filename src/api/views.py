from django.contrib.auth import get_user_model

from rest_framework import serializers
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

User = get_user_model()


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
        data['user'] = _serialize_user(self.user)
        return data


class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Login con email + password.
    Devuelve access token, refresh token y datos básicos del usuario.
    """
    serializer_class = CustomTokenObtainPairSerializer
    permission_classes = [AllowAny]


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
                    },
                ),
            ),
        }
    )
    def get(self, request):
        return Response(_serialize_user(request.user))
