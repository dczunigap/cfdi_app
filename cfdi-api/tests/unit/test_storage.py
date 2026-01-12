from pathlib import Path

from app.adapters.outbound.files.pdf_storage import LocalPdfStorage


def test_local_pdf_storage_save_and_read(tmp_path: Path):
    storage = LocalPdfStorage(tmp_path)
    filename = "test.pdf"
    data = b"pdf-data"

    storage.save(filename, data)
    assert storage.read(filename) == data
