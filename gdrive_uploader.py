"""
gdrive_uploader.py — Faz upload de um arquivo para o Google Drive via API v3.

Autenticação via OAuth 2.0:
  - Na primeira execução, abre o navegador para autorização.
  - As credenciais são salvas em token.json para execuções futuras.
"""

import logging
import os
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

logger = logging.getLogger(__name__)

# Escopo necessário para upload/leitura de arquivos
SCOPES = ["https://www.googleapis.com/auth/drive.file"]

CREDENTIALS_FILE = os.getenv("GDRIVE_CREDENTIALS_FILE", "credentials.json")
TOKEN_FILE = os.getenv("GDRIVE_TOKEN_FILE", "token.json")


def _get_credentials() -> Credentials:
    """Obtém (ou renova) as credenciais OAuth do Google Drive."""
    creds = None

    if Path(TOKEN_FILE).exists():
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            logger.info("Renovando token do Google Drive…")
            creds.refresh(Request())
        else:
            logger.info("Iniciando fluxo de autenticação OAuth do Google Drive…")
            if not Path(CREDENTIALS_FILE).exists():
                raise FileNotFoundError(
                    f"Arquivo de credenciais não encontrado: {CREDENTIALS_FILE}\n"
                    "Baixe o credentials.json no Google Cloud Console e coloque na raiz do projeto."
                )
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)

        # Salva o token para próximas execuções
        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())
        logger.info("Token salvo em %s", TOKEN_FILE)

    return creds


def upload_to_drive(file_path: Path, folder_id: str) -> str:
    """
    Faz upload de um arquivo para o Google Drive.

    Args:
        file_path: Caminho local do arquivo a enviar.
        folder_id: ID da pasta de destino no Google Drive.

    Returns:
        Link direto para o arquivo no Google Drive.

    Raises:
        RuntimeError: Em caso de falha no upload.
    """
    try:
        creds = _get_credentials()
        service = build("drive", "v3", credentials=creds)

        file_metadata = {
            "name": file_path.name,
            "parents": [folder_id],
        }

        media = MediaFileUpload(
            str(file_path),
            mimetype="application/zip",
            resumable=True,  # Upload retomável para arquivos grandes
            chunksize=5 * 1024 * 1024,  # 5 MB por chunk
        )

        logger.info("Iniciando upload para o Google Drive (%s)…", file_path.name)

        request = service.files().create(
            body=file_metadata,
            media_body=media,
            fields="id, webViewLink",
        )

        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                logger.info("  Progresso Drive: %d%%", int(status.progress() * 100))

        file_id = response.get("id")
        web_link = response.get("webViewLink", f"https://drive.google.com/file/d/{file_id}/view")

        logger.info("Upload Drive concluído. ID: %s", file_id)
        return web_link

    except Exception as exc:
        raise RuntimeError(f"Falha no upload para o Google Drive: {exc}") from exc
