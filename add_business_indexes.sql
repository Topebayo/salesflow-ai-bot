-- SQL Script to add multi-tenant indexing to SalesFlow AI
-- Run this in the Supabase SQL Editor to prevent full table scans when scaling

CREATE INDEX IF NOT EXISTS idx_contacts_business_id ON contacts(business_id);
CREATE INDEX IF NOT EXISTS idx_conversations_business_id ON conversations(business_id);
