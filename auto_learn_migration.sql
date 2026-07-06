-- Migration script: Add auto-learned knowledge column to businesses table
ALTER TABLE businesses ADD COLUMN IF NOT EXISTS auto_learned_knowledge TEXT DEFAULT '';
