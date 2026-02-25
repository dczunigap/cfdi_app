from __future__ import annotations

import io
import os

from minio import Minio
from minio.error import S3Error

from app.ports.pdf_storage import PdfStorage


class PdfStorageR2(PdfStorage):
    def __init__(
        self,
        endpoint: str | None = None,
        access_key: str | None = None,
        secret_key: str | None = None,
        bucket: str | None = None,
        region: str | None = None,
        secure: bool | None = None,
        prefix: str | None = None,
    ) -> None:
        self._endpoint = endpoint or os.getenv("R2_ENDPOINT", "")
        self._access_key = access_key or os.getenv("R2_ACCESS_KEY", "")
        self._secret_key = secret_key or os.getenv("R2_SECRET_KEY", "")
        self._bucket = bucket or os.getenv("PDF_R2_BUCKET") or os.getenv("R2_BUCKET", "")
        self._region = region or os.getenv("R2_REGION") or "auto"
        self._prefix = (prefix or os.getenv("PDF_R2_PREFIX") or "pdfs").strip("/")
        if not self._endpoint or not self._access_key or not self._secret_key or not self._bucket:
            raise ValueError(
                "R2 config incompleta (R2_ENDPOINT/R2_ACCESS_KEY/R2_SECRET_KEY/PDF_R2_BUCKET|R2_BUCKET)."
            )

        if secure is None:
            secure = not self._endpoint.startswith("http://")
        endpoint_no_scheme = self._endpoint.replace("http://", "").replace("https://", "")

        self._client = Minio(
            endpoint=endpoint_no_scheme,
            access_key=self._access_key,
            secret_key=self._secret_key,
            secure=secure,
            region=self._region,
        )

    def _key(self, filename: str) -> str:
        if not self._prefix:
            return filename
        return f"{self._prefix}/{filename}"

    def save(self, filename: str, data: bytes) -> str:
        key = self._key(filename)
        try:
            self._client.put_object(
                bucket_name=self._bucket,
                object_name=key,
                data=io.BytesIO(data),
                length=len(data),
                content_type="application/pdf",
            )
        except S3Error as exc:
            raise RuntimeError(f"Error subiendo PDF a R2: {exc}") from exc
        return key

    def read(self, filename: str) -> bytes:
        key = self._key(filename)
        try:
            response = self._client.get_object(self._bucket, key)
            try:
                return response.read()
            finally:
                response.close()
                response.release_conn()
        except S3Error as exc:
            if exc.code in {"NoSuchKey", "NoSuchObject"}:
                raise FileNotFoundError(f"PDF no encontrado: {key}") from exc
            raise RuntimeError(f"Error leyendo PDF de R2: {exc}") from exc

    def delete(self, filename: str) -> None:
        key = self._key(filename)
        try:
            self._client.remove_object(self._bucket, key)
        except S3Error as exc:
            if exc.code in {"NoSuchKey", "NoSuchObject"}:
                return
            raise RuntimeError(f"Error eliminando PDF de R2: {exc}") from exc
