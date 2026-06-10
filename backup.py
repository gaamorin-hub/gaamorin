"""
Sistema de Backup Automatizado
Compacta pastas, envia para Google Drive e AWS S3, notifica por e-mail.
"""

import os
import sys
import logging
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

from compressor import compress_folders
from gdrive_uploader import upload_to_drive
from s3_uploader import upload_to_s3
from notifier import send_email

# Carrega variáveis de ambiente
load_dotenv()

# ─── Configuração de Logging ───────────────────────────────────────────────────

LOG_DIR = Path(os.getenv("LOG_DIR", "logs"))
LOG_DIR.mkdir(parents=True, exist_ok=True)

LOG_FILE = LOG_DIR / f"backup_{datetime.now().strftime('%Y%m%d')}.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)


# ─── Helpers ──────────────────────────────────────────────────────────────────

def load_config() -> dict:
    """Lê e valida todas as configurações necessárias."""
    folders_raw = os.getenv("BACKUP_FOLDERS", "")
    folders = [f.strip() for f in folders_raw.split(",") if f.strip()]

    if not folders:
        raise ValueError("BACKUP_FOLDERS não configurado ou vazio no .env")

    required = [
        "GDRIVE_FOLDER_ID",
        "AWS_ACCESS_KEY_ID",
        "AWS_SECRET_ACCESS_KEY",
        "AWS_S3_BUCKET",
        "EMAIL_SENDER",
        "EMAIL_RECIPIENT",
        "EMAIL_SMTP_HOST",
        "EMAIL_SMTP_PASSWORD",
    ]
    missing = [k for k in required if not os.getenv(k)]
    if missing:
        raise ValueError(f"Variáveis de ambiente ausentes: {', '.join(missing)}")

    return {
        "folders": folders,
        "output_dir": Path(os.getenv("OUTPUT_DIR", "backups")),
        "gdrive_folder_id": os.getenv("GDRIVE_FOLDER_ID"),
        "aws_bucket": os.getenv("AWS_S3_BUCKET"),
        "aws_region": os.getenv("AWS_REGION", "us-east-1"),
        "email_sender": os.getenv("EMAIL_SENDER"),
        "email_recipient": os.getenv("EMAIL_RECIPIENT"),
        "smtp_host": os.getenv("EMAIL_SMTP_HOST"),
        "smtp_port": int(os.getenv("EMAIL_SMTP_PORT", "587")),
        "smtp_password": os.getenv("EMAIL_SMTP_PASSWORD"),
    }


# ─── Pipeline Principal ────────────────────────────────────────────────────────

def run_backup():
    started_at = datetime.now()
    logger.info("=" * 60)
    logger.info("INÍCIO DO BACKUP  —  %s", started_at.strftime("%Y-%m-%d %H:%M:%S"))
    logger.info("=" * 60)

    config = None
    zip_path = None

    try:
        # 1. Configurações
        logger.info("[1/5] Carregando configurações…")
        config = load_config()
        config["output_dir"].mkdir(parents=True, exist_ok=True)
        logger.info("      Pastas a compactar: %s", config["folders"])

        # 2. Compactação
        logger.info("[2/5] Compactando pastas…")
        zip_path = compress_folders(config["folders"], config["output_dir"])
        zip_size_mb = zip_path.stat().st_size / (1024 * 1024)
        logger.info("      Arquivo criado: %s (%.2f MB)", zip_path.name, zip_size_mb)

        # 3. Upload Google Drive
        logger.info("[3/5] Enviando para o Google Drive…")
        gdrive_link = upload_to_drive(zip_path, config["gdrive_folder_id"])
        logger.info("      Link Drive: %s", gdrive_link)

        # 4. Upload AWS S3
        logger.info("[4/5] Enviando para o AWS S3…")
        s3_link = upload_to_s3(
            zip_path,
            config["aws_bucket"],
            config["aws_region"],
        )
        logger.info("      Link S3: %s", s3_link)

        # 5. Notificação de sucesso
        logger.info("[5/5] Enviando e-mail de sucesso…")
        send_email(
            smtp_host=config["smtp_host"],
            smtp_port=config["smtp_port"],
            sender=config["email_sender"],
            password=config["smtp_password"],
            recipient=config["email_recipient"],
            subject=f"✅ Backup Automatizado — Sucesso [{started_at.strftime('%Y-%m-%d %H:%M')}]",
            body=_build_success_body(
                folders=config["folders"],
                zip_name=zip_path.name,
                zip_size_mb=zip_size_mb,
                gdrive_link=gdrive_link,
                s3_link=s3_link,
                started_at=started_at,
            ),
        )

        elapsed = (datetime.now() - started_at).total_seconds()
        logger.info("=" * 60)
        logger.info("BACKUP CONCLUÍDO COM SUCESSO em %.1f s", elapsed)
        logger.info("=" * 60)

    except Exception as exc:
        logger.error("FALHA NO BACKUP: %s", exc, exc_info=True)

        # Tenta enviar e-mail de falha
        if config:
            try:
                send_email(
                    smtp_host=config["smtp_host"],
                    smtp_port=config["smtp_port"],
                    sender=config["email_sender"],
                    password=config["smtp_password"],
                    recipient=config["email_recipient"],
                    subject=f"❌ Backup Automatizado — FALHA [{started_at.strftime('%Y-%m-%d %H:%M')}]",
                    body=_build_failure_body(str(exc), started_at),
                )
                logger.info("E-mail de falha enviado.")
            except Exception as mail_exc:
                logger.error("Não foi possível enviar e-mail de falha: %s", mail_exc)

        sys.exit(1)


# ─── Templates de E-mail ──────────────────────────────────────────────────────

def _build_success_body(folders, zip_name, zip_size_mb, gdrive_link, s3_link, started_at) -> str:
    folders_list = "\n".join(f"  • {f}" for f in folders)
    return f"""Olá,

O backup automatizado foi concluído com êxito.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 DETALHES DO BACKUP
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Data/hora de início : {started_at.strftime("%Y-%m-%d %H:%M:%S")}
Arquivo gerado      : {zip_name}
Tamanho             : {zip_size_mb:.2f} MB

Pastas incluídas:
{folders_list}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 DESTINOS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Google Drive : {gdrive_link}
AWS S3       : {s3_link}

Atenciosamente,
Sistema de Backup Automatizado
"""


def _build_failure_body(error_msg: str, started_at: datetime) -> str:
    return f"""Olá,

O backup automatizado iniciado em {started_at.strftime("%Y-%m-%d %H:%M:%S")} FALHOU.

Erro registrado:
{error_msg}

Por favor, verifique o arquivo de log para mais detalhes.

Atenciosamente,
Sistema de Backup Automatizado
"""


if __name__ == "__main__":
    run_backup()
