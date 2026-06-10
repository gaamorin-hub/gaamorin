"""
notifier.py — Envia e-mails de notificação via SMTP com TLS.

Compatível com Gmail, Outlook, SendGrid e qualquer servidor SMTP padrão.
"""

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

logger = logging.getLogger(__name__)


def send_email(
    smtp_host: str,
    smtp_port: int,
    sender: str,
    password: str,
    recipient: str,
    subject: str,
    body: str,
) -> None:
    """
    Envia um e-mail via SMTP com STARTTLS.

    Args:
        smtp_host:  Servidor SMTP (ex.: smtp.gmail.com).
        smtp_port:  Porta SMTP (587 para TLS, 465 para SSL).
        sender:     Endereço de e-mail remetente.
        password:   Senha ou App Password do remetente.
        recipient:  Endereço de e-mail destinatário.
        subject:    Assunto do e-mail.
        body:       Corpo do e-mail (texto puro).

    Raises:
        RuntimeError: Se o envio falhar.
    """
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = recipient

    # Parte texto puro
    msg.attach(MIMEText(body, "plain", "utf-8"))

    # Parte HTML com formatação mínima (opcional, melhora leitura em clientes modernos)
    html_body = _to_html(body)
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    try:
        logger.info("Conectando ao servidor SMTP %s:%s…", smtp_host, smtp_port)

        if smtp_port == 465:
            # SSL direto
            with smtplib.SMTP_SSL(smtp_host, smtp_port) as server:
                server.login(sender, password)
                server.sendmail(sender, recipient, msg.as_string())
        else:
            # STARTTLS (porta 587 ou 25)
            with smtplib.SMTP(smtp_host, smtp_port) as server:
                server.ehlo()
                server.starttls()
                server.ehlo()
                server.login(sender, password)
                server.sendmail(sender, recipient, msg.as_string())

        logger.info("E-mail enviado para: %s", recipient)

    except smtplib.SMTPAuthenticationError as exc:
        raise RuntimeError(
            f"Falha de autenticação SMTP. Verifique EMAIL_SENDER e EMAIL_SMTP_PASSWORD.\n{exc}"
        ) from exc
    except smtplib.SMTPException as exc:
        raise RuntimeError(f"Erro SMTP ao enviar e-mail: {exc}") from exc
    except Exception as exc:
        raise RuntimeError(f"Falha inesperada ao enviar e-mail: {exc}") from exc


def _to_html(text: str) -> str:
    """Converte texto puro em HTML simples, preservando quebras de linha."""
    lines = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    html_lines = lines.replace("\n", "<br>\n")
    return f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    body {{ font-family: monospace; font-size: 14px; color: #222; padding: 20px; }}
    br  {{ line-height: 1.8; }}
  </style>
</head>
<body>{html_lines}</body>
</html>"""
