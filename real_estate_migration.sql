-- =============================================================================
-- REAL ESTATE MODE DATABASE MIGRATION SCRIPT
-- =============================================================================
-- Run this in your Supabase SQL Editor (supabase.com → SQL Editor → New Query)
-- This adds property specifications to products and qualification columns to contacts.
-- =============================================================================

-- 1. Add Property spec columns to products table
ALTER TABLE products ADD COLUMN IF NOT EXISTS bedrooms INTEGER DEFAULT 0;
ALTER TABLE products ADD COLUMN IF NOT EXISTS bathrooms INTEGER DEFAULT 0;
ALTER TABLE products ADD COLUMN IF NOT EXISTS property_type TEXT DEFAULT '';
ALTER TABLE products ADD COLUMN IF NOT EXISTS location TEXT DEFAULT '';
ALTER TABLE products ADD COLUMN IF NOT EXISTS virtual_tour_url TEXT DEFAULT '';

-- 2. Add Qualification columns to contacts table
ALTER TABLE contacts ADD COLUMN IF NOT EXISTS budget_min TEXT DEFAULT '';
ALTER TABLE contacts ADD COLUMN IF NOT EXISTS budget_max TEXT DEFAULT '';
ALTER TABLE contacts ADD COLUMN IF NOT EXISTS preferred_location TEXT DEFAULT '';
ALTER TABLE contacts ADD COLUMN IF NOT EXISTS search_status TEXT DEFAULT 'searching';
