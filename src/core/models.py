from django.conf import settings
from django.db import models


class UserProfile(models.Model):
    """
    Perfil extendido del usuario. Guarda la URL de la foto de perfil
    (equivalente a `frank_profile_picture_url` de Employee en PAC).
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profile',
    )
    profile_picture_url = models.CharField(max_length=200, blank=True, null=True)
    # Se pone en True cuando el usuario se loguea al menos una vez.
    # El ranking sólo muestra participantes (evita listar a quienes nunca entran).
    is_participant = models.BooleanField(
        default=False, db_index=True, verbose_name='Participa (se logueó)',
    )

    # Código de activación de cuenta (OTP de 6 dígitos) enviado por mail al registrarse.
    activation_code = models.CharField(max_length=6, blank=True, null=True)
    activation_code_expires = models.DateTimeField(null=True, blank=True)
    activation_attempts = models.PositiveSmallIntegerField(default=0)

    create_date = models.DateTimeField(auto_now_add=True)
    update_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'Profile of {self.user}'
