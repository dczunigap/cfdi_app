from __future__ import annotations

import json
from datetime import date, datetime
from typing import Any, Optional


def json_default_encoder(obj: Any) -> str:
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    return str(obj)


def serialize_to_json(obj: Any, ensure_ascii: bool = False, indent: Optional[int] = 2) -> str:
    return json.dumps(obj, ensure_ascii=ensure_ascii, indent=indent, default=json_default_encoder)
