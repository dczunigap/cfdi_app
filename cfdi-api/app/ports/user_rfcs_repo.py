from __future__ import annotations

from typing import Protocol


class UserRfcsRepository(Protocol):
    def is_allowed(self, user_id: int, rfc: str) -> bool:
        ...

    def add(self, user_id: int, rfc: str) -> None:
        ...

    def remove(self, user_id: int, rfc: str) -> None:
        ...

    def list_by_user(self, user_id: int) -> list[str]:
        ...
