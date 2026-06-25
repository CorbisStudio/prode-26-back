import logging

from django.contrib.auth import get_user_model
from django.contrib.staticfiles import finders

from .emails import EmailProde

logger = logging.getLogger(__name__)

User = get_user_model()


def send_activation_email(user_id, code):
    user = User.objects.filter(pk=user_id).first()
    if not user:
        logger.warning('send_activation_email: user %s no existe', user_id)
        return

    logo_path = finders.find('email/logo-corbis.png')

    try:
        EmailProde(
            subject='Your activation code · Prediction Game Mundial',
            recipient_list=[user.email],
            context={
                'first_name': user.first_name or user.username,
                'code': code,
                'logo_url': 'cid:logo',
            },
            template='activation.html',
            inline_images={'logo': logo_path},
        ).send()
        logger.info('send_activation_email: mail enviado a %s', user.email)
    except Exception as exc:
        logger.error('send_activation_email: fallo enviando a %s: %s', user.email, exc)
