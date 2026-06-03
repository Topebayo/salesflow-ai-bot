-- ==============================================================================
-- SANDBOX SESSIONS TABLE MIGRATION
-- Run this in the Supabase SQL Editor to persist Twilio Sandbox switcher sessions
-- ==============================================================================

CREATE TABLE IF NOT EXISTS sandbox_sessions (
    phone_number TEXT PRIMARY KEY,
    business_id UUID REFERENCES businesses(id) ON DELETE CASCADE,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Enable RLS
ALTER TABLE sandbox_sessions ENABLE ROW LEVEL SECURITY;

-- Enable Public read/write policy so that our API (which uses anon/service_role keys) can fetch/update sessions
CREATE POLICY "Allow all operations on sandbox_sessions" ON sandbox_sessions FOR ALL USING (true);
