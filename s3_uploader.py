"""
s3_uploader.py — Faz upload de um arquivo para um bucket AWS S3.

Autenticação via variáveis de ambiente:
  AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY (e opcionalmente AWS_SESSION_TOKEN).
"""

import logging
import os
from pathlib import Path

import boto3
from boto3.s3.transfer import TransferConfig
from botocore.exceptions import ClientError, NoCredentialsError

logger = logging.getLogger(__name__)


class _ProgressLogger:
    """Callback de progresso para o upload multipart do S3."""

    def __init__(self, filename: str, total: int):
        self._filename = filename
        self._total = total
        self._seen = 0
        self._last_reported = -1

    def __call__(self, bytes_amount: int):
        self._seen += bytes_amount
        pct = int(self._seen / self._total * 100)
        if pct // 10 != self._last_reported // 10:
            logger.info("  Progresso S3: %d%%", pct)
            self._last_reported = pct


def upload_to_s3(file_path: Path, bucket: str, region: str = "us-east-1") -> str:
    """
    Faz upload de um arquivo para o AWS S3 com suporte a multipart.

    Args:
        file_path: Caminho local do arquivo a enviar.
        bucket:    Nome do bucket S3 de destino.
        region:    Região AWS (padrão: us-east-1).

    Returns:
        URL pública ou link de console para o objeto no S3.

    Raises:
        RuntimeError: Em caso de falha no upload.
    """
    s3_key = f"backups/{file_path.name}"

    try:
        session = boto3.Session(
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            aws_session_token=os.getenv("AWS_SESSION_TOKEN"),  # opcional
            region_name=region,
        )
        s3_client = session.client("s3")

        file_size = file_path.stat().st_size

        # Configuração de multipart: ativa para arquivos > 8 MB
        transfer_config = TransferConfig(
            multipart_threshold=8 * 1024 * 1024,
            max_concurrency=4,
            multipart_chunksize=8 * 1024 * 1024,
            use_threads=True,
        )

        logger.info("Iniciando upload para S3: s3://%s/%s", bucket, s3_key)

        s3_client.upload_file(
            Filename=str(file_path),
            Bucket=bucket,
            Key=s3_key,
            Config=transfer_config,
            Callback=_ProgressLogger(file_path.name, file_size),
        )

        # Gera URL pre-assinada válida por 7 dias (sem tornar o objeto público)
        presigned_url = s3_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket, "Key": s3_key},
            ExpiresIn=7 * 24 * 3600,
        )

        logger.info("Upload S3 concluído: s3://%s/%s", bucket, s3_key)
        return presigned_url

    except NoCredentialsError as exc:
        raise RuntimeError(
            "Credenciais AWS não encontradas. Verifique AWS_ACCESS_KEY_ID e AWS_SECRET_ACCESS_KEY."
        ) from exc
    except ClientError as exc:
        raise RuntimeError(f"Erro da API AWS S3: {exc}") from exc
    except Exception as exc:
        raise RuntimeError(f"Falha no upload para o S3: {exc}") from exc
