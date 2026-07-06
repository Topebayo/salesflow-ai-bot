-- ==============================================================================
-- SUPABASE SECURITY PATCH: ENABLE ROW LEVEL SECURITY (RLS) FOR ALL TABLES
-- Run this in your Supabase SQL Editor (supabase.com -> SQL Editor -> New Query)
-- ==============================================================================

-- 1. Enable RLS on all project tables
ALTER TABLE IF EXISTS businesses ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS contacts ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS orders ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS products ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS sandbox_sessions ENABLE ROW LEVEL SECURITY;

-- 2. Create policies if they do not exist
DO $$
BEGIN
    -- Businesses Policy: Owners can manage their own business profiles
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'businesses' AND policyname = 'Users can view their own business') THEN
        CREATE POLICY "Users can view their own business" ON businesses FOR ALL USING (auth.uid() = owner_id);
    END IF;

    -- Contacts Policy: Owners can view contacts belonging to their businesses
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'contacts' AND policyname = 'Users can view their business contacts') THEN
        CREATE POLICY "Users can view their business contacts" ON contacts FOR ALL USING (business_id IN (SELECT id FROM businesses WHERE owner_id = auth.uid()));
    END IF;

    -- Conversations Policy: Owners can view chat history for their businesses
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'conversations' AND policyname = 'Users can view their business conversations') THEN
        CREATE POLICY "Users can view their business conversations" ON conversations FOR ALL USING (business_id IN (SELECT id FROM businesses WHERE owner_id = auth.uid()));
    END IF;

    -- Orders Policy: Owners can view orders placed with their businesses
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'orders' AND policyname = 'Users can view their business orders') THEN
        CREATE POLICY "Users can view their business orders" ON orders FOR ALL USING (business_id IN (SELECT id FROM businesses WHERE owner_id = auth.uid()));
    END IF;

    -- Products Policy: Owners can manage products in their catalogs
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'products' AND policyname = 'Users can manage their own products') THEN
        CREATE POLICY "Users can manage their own products" ON products FOR ALL USING (business_id IN (SELECT id FROM businesses WHERE owner_id = auth.uid()));
    END IF;

    -- Sandbox Sessions Policy: Owners can manage sandbox sessions for their businesses
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'sandbox_sessions' AND policyname = 'Users can manage their business sandbox sessions') THEN
        CREATE POLICY "Users can manage their business sandbox sessions" ON sandbox_sessions FOR ALL USING (business_id IN (SELECT id FROM businesses WHERE owner_id = auth.uid()));
    END IF;
END
$$;
