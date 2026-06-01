-- ==============================================================================
-- ADD INSPECTION FEE MIGRATION
-- Run this in the Supabase SQL Editor to support inspection fees for real estate agents
-- ==============================================================================

ALTER TABLE businesses ADD COLUMN IF NOT EXISTS inspection_fee TEXT DEFAULT '0';
