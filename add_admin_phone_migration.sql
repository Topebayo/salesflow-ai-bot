-- SQL Schema Migration: Add admin_phone to businesses table
-- This stores the registered business owner's personal WhatsApp number
-- so only they can execute administrative slash commands (/handoff, /handon).

ALTER TABLE public.businesses ADD COLUMN IF NOT EXISTS admin_phone TEXT DEFAULT '';
