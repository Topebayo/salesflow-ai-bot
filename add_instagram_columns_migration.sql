-- =============================================================================
-- SAAS INSTAGRAM INTEGRATION MIGRATION
-- =============================================================================
-- Run this in your Supabase SQL Editor (supabase.com → SQL Editor → New Query)
-- This adds credentials and connection state columns for Instagram DMs.
-- =============================================================================

-- 1. Add Instagram integration columns to businesses table
ALTER TABLE businesses ADD COLUMN IF NOT EXISTS instagram_page_id TEXT DEFAULT '';
ALTER TABLE businesses ADD COLUMN IF NOT EXISTS instagram_access_token TEXT DEFAULT '';
ALTER TABLE businesses ADD COLUMN IF NOT EXISTS instagram_verify_token TEXT DEFAULT '';
ALTER TABLE businesses ADD COLUMN IF NOT EXISTS instagram_webhook_connected BOOLEAN DEFAULT FALSE;
ALTER TABLE businesses ADD COLUMN IF NOT EXISTS instagram_webhook_verified_at TIMESTAMPTZ;
