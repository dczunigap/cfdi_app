-- Adds status metadata and removes last_error in sat_descargas
-- Compatible with SQLite and PostgreSQL (Postgres uses DROP COLUMN)

-- 1) Add new columns
ALTER TABLE sat_descargas ADD COLUMN codigo_estado VARCHAR(20);
ALTER TABLE sat_descargas ADD COLUMN mensaje_estado TEXT;

-- 2) Drop old column
-- SQLite (>= 3.35.0) supports DROP COLUMN
ALTER TABLE sat_descargas DROP COLUMN last_error;
