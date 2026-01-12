from datetime import datetime

from app.utils.json import serialize_to_json


def test_serialize_to_json_encodes_datetime():
    payload = {"ts": datetime(2025, 1, 1, 12, 0, 0)}
    result = serialize_to_json(payload)
    assert "2025-01-01T12:00:00" in result
