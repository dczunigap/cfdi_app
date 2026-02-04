-- Add is_admin flag to users table (defaults to false)
ALTER TABLE users
  ADD COLUMN IF NOT EXISTS is_admin BOOLEAN NOT NULL DEFAULT 0;
