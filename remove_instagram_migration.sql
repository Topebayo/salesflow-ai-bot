-- Migration: Remove unused legacy Instagram columns from businesses table
-- Run this script in your Supabase SQL Editor to clean up your database schema.

ALTER TABLE businesses 
DROP COLUMN IF EXISTS instagram_page_id,
DROP COLUMN IF EXISTS instagram_access_token,
DROP COLUMN IF EXISTS instagram_verify_token,
DROP COLUMN IF EXISTS instagram_webhook_connected,
DROP COLUMN IF EXISTS instagram_webhook_verified_at;
