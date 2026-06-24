import logging

from celery import shared_task
from django.contrib.auth import get_user_model

from .emails import EmailProde

logger = logging.getLogger(__name__)

User = get_user_model()


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_activation_email(self, user_id, code):
    """
    Envía el mail de activación con el código (OTP) al usuario recién registrado.
    Async: se encola desde RegisterView. Reintenta hasta 3 veces si el SMTP falla.
    El logo de Corbis se incrusta inline (CID) para que se vea siempre.
    """
    from django.contrib.staticfiles import finders

    user = User.objects.filter(pk=user_id).first()
    if not user:
        logger.warning('send_activation_email: user %s no existe', user_id)
        return

    logo_path = finders.find('email/logo-corbis.png')

    try:
        EmailProde(
            # subject='Tu código de activación · Prode Mundial',
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
        raise self.retry(exc=exc)
