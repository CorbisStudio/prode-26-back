from django.conf import settings
from django.db import models


class SiteSetting(models.Model):
    email_backend = models.CharField(
        max_length=200, default='django.core.mail.backends.smtp.EmailBackend'
    )
    email_host = models.CharField(max_length=200, blank=True)
    email_port = models.IntegerField(default=587)
    email_use_tls = models.BooleanField(default=True)
    email_use_ssl = models.BooleanField(default=False)
    email_host_user = models.CharField(max_length=200, blank=True)
    email_host_password = models.CharField(max_length=200, blank=True)
    default_from_email = models.CharField(max_length=200, blank=True)
    football_data_token = models.CharField(max_length=200, blank=True)
    football_data_base_url = models.URLField(default='https://api.football-data.org/v4/')
    world_cup_competition_code = models.CharField(max_length=20, default='WC')

    class Meta:
        verbose_name = 'Site Setting'
        verbose_name_plural = 'Site Settings'

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def get(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


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
