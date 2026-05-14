-- ==============================================================================
-- CUSTOM PROMPT EDITOR MIGRATION
-- Run this in the Supabase SQL Editor
-- ==============================================================================

-- Add custom prompt fields to the businesses table
ALTER TABLE businesses ADD COLUMN IF NOT EXISTS agent_name TEXT DEFAULT 'AI Assistant';
ALTER TABLE businesses ADD COLUMN IF NOT EXISTS greeting TEXT DEFAULT '';
ALTER TABLE businesses ADD COLUMN IF NOT EXISTS business_description TEXT DEFAULT '';
ALTER TABLE businesses ADD COLUMN IF NOT EXISTS products_services TEXT DEFAULT '';
ALTER TABLE businesses ADD COLUMN IF NOT EXISTS payment_info TEXT DEFAULT '';
ALTER TABLE businesses ADD COLUMN IF NOT EXISTS business_hours TEXT DEFAULT '';
ALTER TABLE businesses ADD COLUMN IF NOT EXISTS custom_rules TEXT DEFAULT '';
ALTER TABLE businesses ADD COLUMN IF NOT EXISTS tone TEXT DEFAULT 'friendly';
