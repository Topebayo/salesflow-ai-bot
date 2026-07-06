-- Migration: Fix Security Advisor RLS Warning on sandbox_sessions
-- Run this script in your Supabase SQL Editor to secure the sandbox_sessions table and remove the warning.

-- 1. Drop the overly permissive "always true" policy
DROP POLICY IF EXISTS "Allow all operations on sandbox_sessions" ON sandbox_sessions;

-- 2. Create a secure policy restricted to business owners (matching all other tables)
CREATE POLICY "Users can manage their business sandbox sessions" 
ON sandbox_sessions 
FOR ALL 
USING (business_id IN (SELECT id FROM businesses WHERE owner_id = auth.uid()));
