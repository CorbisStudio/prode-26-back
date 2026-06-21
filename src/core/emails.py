from email.mime.image import MIMEImage
from smtplib import SMTPException

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags


class EmailProde:
    """
    Wrapper de envío de mails (mismo mecanismo que `EmailPAC` de PAC):
    renderiza un template HTML, genera la versión texto con `strip_tags`
    y envía. El template vive en `core/templates/email/`.

    Soporta imágenes inline por CID (`inline_images={'logo': '/ruta/al.png'}`):
    la imagen viaja adjunta dentro del mail y se referencia en el HTML como
    `src="cid:logo"`, así se ve siempre (sin depender de imágenes remotas).
    """

    def __init__(
        self,
        subject: str,
        recipient_list: list[str],
        context: dict,
        template: str,
        from_email: str | None = None,
        inline_images: dict | None = None,
    ) -> None:
        self.__subject = subject
        self.__recipient_list = recipient_list
        self.__context = context
        self.__template = template
        self.__from_email = from_email or settings.DEFAULT_FROM_EMAIL
        self.__inline_images = inline_images or {}

    def __get_template_path(self) -> str:
        """El template se busca en core/templates/email/<template>."""
        return f'email/{self.__template}'

    def send(self) -> None:
        html_rendered = render_to_string(
            template_name=self.__get_template_path(),
            context=self.__context,
        )
        txt_rendered = strip_tags(html_rendered)

        msg = EmailMultiAlternatives(
            subject=self.__subject,
            body=txt_rendered,
            from_email=self.__from_email,
            to=self.__recipient_list,
        )
        msg.attach_alternative(html_rendered, 'text/html')

        # Imágenes inline (CID): el HTML y las imágenes van en un multipart/related.
        if self.__inline_images:
            msg.mixed_subtype = 'related'
            for cid, path in self.__inline_images.items():
                if not path:
                    continue
                with open(path, 'rb') as fh:
                    img = MIMEImage(fh.read())
                img.add_header('Content-ID', f'<{cid}>')
                img.add_header('Content-Disposition', 'inline', filename=cid)
                msg.attach(img)

        try:
            msg.send(fail_silently=False)
        except SMTPException as error:
            # Se loguea y se re-lanza para que el task de Celery pueda reintentar.
            print(f'[EmailProde] Error enviando mail: {error}')
            raise
