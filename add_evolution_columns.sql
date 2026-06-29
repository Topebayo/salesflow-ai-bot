-- Migration: Add Evolution API columns to businesses table
-- This enables the QR-code-based WhatsApp onboarding flow

ALTER TABLE businesses
ADD COLUMN IF NOT EXISTS whatsapp_provider TEXT DEFAULT 'evolution',
ADD COLUMN IF NOT EXISTS evolution_instance_name TEXT,
ADD COLUMN IF NOT EXISTS evolution_apikey TEXT;

-- Create index for Evolution instance lookups (used by webhook routing)
CREATE INDEX IF NOT EXISTS idx_businesses_evolution_instance
ON businesses(evolution_instance_name)
WHERE evolution_instance_name IS NOT NULL;
