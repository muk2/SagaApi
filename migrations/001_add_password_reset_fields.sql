-- Migration: Add password reset fields to user_account table
-- Date: 2026-01-28
-- Description: Adds reset_token and reset_token_expires fields for password reset functionality

ALTER TABLE saga.user_account
ADD COLUMN IF NOT EXISTS reset_token VARCHAR(255),
ADD COLUMN IF NOT EXISTS reset_token_expires TIMESTAMP WITH TIME ZONE;

-- Create index on reset_token for faster lookups
CREATE INDEX IF NOT EXISTS idx_user_account_reset_token ON saga.user_account(reset_token);
