-- =============================================================================
-- SAAS WHATSAPP PIVOT MIGRATION
-- =============================================================================
-- Run this in your Supabase SQL Editor (supabase.com → SQL Editor → New Query)
-- This adds per-business WhatsApp credentials and a product catalog with images.
-- =============================================================================

-- 1. Add WhatsApp API credential columns to businesses table
ALTER TABLE businesses ADD COLUMN IF NOT EXISTS meta_access_token TEXT DEFAULT '';
ALTER TABLE businesses ADD COLUMN IF NOT EXISTS meta_phone_number_id TEXT DEFAULT '';
ALTER TABLE businesses ADD COLUMN IF NOT EXISTS meta_verify_token TEXT DEFAULT '';
ALTER TABLE businesses ADD COLUMN IF NOT EXISTS webhook_connected BOOLEAN DEFAULT FALSE;
ALTER TABLE businesses ADD COLUMN IF NOT EXISTS webhook_verified_at TIMESTAMPTZ;

-- 2. Create products table for product catalog with images
CREATE TABLE IF NOT EXISTS products (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    business_id UUID NOT NULL REFERENCES businesses(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    description TEXT DEFAULT '',
    price TEXT DEFAULT '',
    image_url TEXT DEFAULT '',
    category TEXT DEFAULT '',
    is_available BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- 3. Enable RLS on products table
ALTER TABLE products ENABLE ROW LEVEL SECURITY;

-- 4. RLS Policy: Business owners can only manage their own products
CREATE POLICY "Users can manage their own products"
    ON products FOR ALL
    USING (business_id IN (SELECT id FROM businesses WHERE owner_id = auth.uid()));

-- 5. Allow the service role (backend) to read all products (needed for AI prompt building)
-- The service role key used by the backend bypasses RLS by default, so no extra policy needed.

-- =============================================================================
-- DONE! After running this, go to Supabase Dashboard → Storage → Create a new
-- bucket called "product-images" and set it to PUBLIC.
-- =============================================================================
