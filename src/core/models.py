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

    create_date = models.DateTimeField(auto_now_add=True)
    update_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'Profile of {self.user}'
