-- ==============================================================================
-- SAAS MULTI-TENANCY MIGRATION SCRIPT
-- Run this in the Supabase SQL Editor to upgrade the database
-- ==============================================================================

-- 1. Create Businesses Table (Tenants)
CREATE TABLE IF NOT EXISTS businesses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    owner_id UUID REFERENCES auth.users(id) ON DELETE CASCADE, -- Links to Supabase Auth
    name TEXT NOT NULL,
    whatsapp_number TEXT UNIQUE, -- The Twilio/Meta number connected to this business
    bot_mode TEXT DEFAULT 'retail',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Note: In a real migration, we would create a default business and assign existing records to it.
-- Since this is early staging, we will just add the columns. 
-- If you want to keep existing data, you'd insert a dummy business first:
-- INSERT INTO businesses (id, name, whatsapp_number) VALUES ('00000000-0000-0000-0000-000000000000', 'SalesFlow AI Default', '+14155238886') ON CONFLICT DO NOTHING;

-- 2. Update Contacts Table
-- We need to drop the primary key on phone_number because the same customer might chat with two different businesses
ALTER TABLE contacts DROP CONSTRAINT IF EXISTS contacts_pkey CASCADE;
ALTER TABLE contacts ADD COLUMN id UUID PRIMARY KEY DEFAULT gen_random_uuid();
ALTER TABLE contacts ADD COLUMN business_id UUID REFERENCES businesses(id) ON DELETE CASCADE;
-- A customer phone number should be unique PER business, not globally
ALTER TABLE contacts ADD CONSTRAINT unique_contact_per_business UNIQUE(business_id, phone_number);

-- 3. Update Conversations Table
ALTER TABLE conversations ADD COLUMN business_id UUID REFERENCES businesses(id) ON DELETE CASCADE;
-- Change foreign key to reference the new contact id instead of phone_number (optional but good practice for strict relational integrity)
-- For now, to keep it simple and backwards compatible with our python code, we'll keep it linked by phone_number but scoped by business_id.

-- 4. Update Orders Table
ALTER TABLE orders ADD COLUMN business_id UUID REFERENCES businesses(id) ON DELETE CASCADE;

-- 5. Enable Row Level Security (RLS)
-- This ensures Business A can NEVER read Business B's data
ALTER TABLE businesses ENABLE ROW LEVEL SECURITY;
ALTER TABLE contacts ENABLE ROW LEVEL SECURITY;
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE orders ENABLE ROW LEVEL SECURITY;

-- Create Policies (Only owners can see their own business data)
CREATE POLICY "Users can view their own business" ON businesses FOR ALL USING (auth.uid() = owner_id);
CREATE POLICY "Users can view their business contacts" ON contacts FOR ALL USING (business_id IN (SELECT id FROM businesses WHERE owner_id = auth.uid()));
CREATE POLICY "Users can view their business conversations" ON conversations FOR ALL USING (business_id IN (SELECT id FROM businesses WHERE owner_id = auth.uid()));
CREATE POLICY "Users can view their business orders" ON orders FOR ALL USING (business_id IN (SELECT id FROM businesses WHERE owner_id = auth.uid()));
