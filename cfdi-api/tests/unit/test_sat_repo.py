from __future__ import annotations

import unittest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.adapters.outbound.db.session import Base
from app.adapters.outbound.db.repositories.sat_credentials import SqlSatCredentialsRepository


class TestSatCredentialsRepository(unittest.TestCase):
    def setUp(self) -> None:
        engine = create_engine("sqlite:///:memory:", future=True)
        Base.metadata.create_all(bind=engine)
        self._Session = sessionmaker(bind=engine, future=True)

    def test_upsert_list_delete(self) -> None:
        with self._Session() as db:
            repo = SqlSatCredentialsRepository(db)
            repo.upsert("AAA010101AAA", b"pfx", "pwd")
            repo.upsert("BBB010101BBB", b"pfx2", None)
            rows = repo.list_all()
            self.assertEqual([r.rfc for r in rows], ["AAA010101AAA", "BBB010101BBB"])

            repo.delete("AAA010101AAA")
            remaining = repo.list_all()
            self.assertEqual([r.rfc for r in remaining], ["BBB010101BBB"])


if __name__ == "__main__":
    unittest.main()
