PRAGMA foreign_keys = OFF;
BEGIN TRANSACTION;

-- Normaliza user_rfcs.created_at a texto de fecha compatible con SQLAlchemy DateTime.
-- Cubre casos legacy: NULL, vacio, numerico (epoch) o texto no parseable.
UPDATE user_rfcs
SET created_at = CASE
    WHEN created_at IS NULL THEN CURRENT_TIMESTAMP
    WHEN typeof(created_at) IN ('integer', 'real') THEN COALESCE(datetime(created_at, 'unixepoch'), CURRENT_TIMESTAMP)
    WHEN typeof(created_at) = 'text' AND trim(created_at) = '' THEN CURRENT_TIMESTAMP
    WHEN typeof(created_at) = 'text' AND datetime(created_at) IS NOT NULL THEN datetime(created_at)
    ELSE CURRENT_TIMESTAMP
END;

COMMIT;
PRAGMA foreign_keys = ON;
