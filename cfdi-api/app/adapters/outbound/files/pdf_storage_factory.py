from __future__ import annotations

import os
from pathlib import Path

from app.adapters.outbound.files.pdf_storage import LocalPdfStorage
from app.core.config import settings
from app.ports.pdf_storage import PdfStorage


def build_pdf_storage() -> PdfStorage:
    backend = (os.getenv("PDF_STORAGE_BACKEND") or "fs").strip().lower()
    if backend == "r2":
        from app.adapters.outbound.r2.pdf_storage_r2 import PdfStorageR2

        return PdfStorageR2()
    return LocalPdfStorage(Path(settings.pdf_upload_dir))
