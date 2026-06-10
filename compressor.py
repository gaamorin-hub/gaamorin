"""
compressor.py — Compacta uma lista de pastas em um único arquivo .zip.
"""

import zipfile
import logging
from datetime import datetime
from pathlib import Path
from typing import List

logger = logging.getLogger(__name__)


def compress_folders(folders: List[str], output_dir: Path) -> Path:
    """
    Compacta todas as pastas informadas em um único arquivo .zip.

    Args:
        folders:    Lista de caminhos de pastas a compactar.
        output_dir: Diretório onde o .zip será salvo.

    Returns:
        Path do arquivo .zip criado.

    Raises:
        FileNotFoundError: Se alguma pasta não existir.
        RuntimeError: Se a compactação falhar.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_name = f"backup_{timestamp}.zip"
    zip_path = output_dir / zip_name

    # Valida existência das pastas antes de iniciar
    for folder in folders:
        p = Path(folder)
        if not p.exists():
            raise FileNotFoundError(f"Pasta não encontrada: {folder}")
        if not p.is_dir():
            raise NotADirectoryError(f"O caminho não é uma pasta: {folder}")

    logger.info("Criando arquivo ZIP: %s", zip_path)

    try:
        with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            for folder in folders:
                folder_path = Path(folder)
                logger.info("  Adicionando pasta: %s", folder_path)
                _add_folder_to_zip(zf, folder_path)

    except Exception as exc:
        # Remove arquivo parcial se algo der errado
        if zip_path.exists():
            zip_path.unlink()
        raise RuntimeError(f"Falha ao compactar pastas: {exc}") from exc

    logger.info("Compactação concluída: %s", zip_path)
    return zip_path


def _add_folder_to_zip(zf: zipfile.ZipFile, folder: Path) -> None:
    """Adiciona recursivamente todos os arquivos de uma pasta ao ZIP."""
    for file_path in folder.rglob("*"):
        if file_path.is_file():
            # arcname preserva o caminho relativo dentro do ZIP
            arcname = file_path.relative_to(folder.parent)
            zf.write(file_path, arcname)
            logger.debug("    + %s", arcname)
