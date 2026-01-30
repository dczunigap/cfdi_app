from __future__ import annotations

import io
import os

from minio import Minio
from minio.error import S3Error

from app.ports.sat_storage import SatStorage


class SatStorageR2(SatStorage):
    def __init__(
        self,
        endpoint: str | None = None,
        access_key: str | None = None,
        secret_key: str | None = None,
        bucket: str | None = None,
        region: str | None = None,
        secure: bool | None = None,
    ) -> None:
        self._endpoint = endpoint or os.getenv("R2_ENDPOINT", "")
        self._access_key = access_key or os.getenv("R2_ACCESS_KEY", "")
        self._secret_key = secret_key or os.getenv("R2_SECRET_KEY", "")
        self._bucket = bucket or os.getenv("R2_BUCKET", "")
        self._region = region or os.getenv("R2_REGION") or "auto"
        if not self._endpoint or not self._access_key or not self._secret_key or not self._bucket:
            raise ValueError("R2 config incompleta (R2_ENDPOINT/R2_ACCESS_KEY/R2_SECRET_KEY/R2_BUCKET).")

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

    def save_zip(self, rfc: str, id_paquete: str, content: bytes) -> str:
        key = f"{rfc}/{id_paquete}.zip"
        try:
            self._client.put_object(
                bucket_name=self._bucket,
                object_name=key,
                data=io.BytesIO(content),
                length=len(content),
                content_type="application/zip",
            )
        except S3Error as exc:
            raise RuntimeError(f"Error subiendo ZIP a R2: {exc}") from exc
        return key

    def open_zip(self, rfc: str, id_paquete: str) -> bytes:
        key = f"{rfc}/{id_paquete}.zip"
        try:
            response = self._client.get_object(self._bucket, key)
            try:
                return response.read()
            finally:
                response.close()
                response.release_conn()
        except S3Error as exc:
            raise RuntimeError(f"Error leyendo ZIP de R2: {exc}") from exc
