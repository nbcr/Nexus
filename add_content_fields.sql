-- Add new fields to content_items table
-- Run this with: psql -U your_user -d your_database -f add_content_fields.sql

-- Add new columns
ALTER TABLE content_items ADD COLUMN IF NOT EXISTS title VARCHAR(500);
ALTER TABLE content_items ADD COLUMN IF NOT EXISTS description TEXT;
ALTER TABLE content_items ADD COLUMN IF NOT EXISTS category VARCHAR(100);
ALTER TABLE content_items ADD COLUMN IF NOT EXISTS tags JSON DEFAULT '[]';

-- Set default values for existing rows
UPDATE content_items SET title = 'Untitled' WHERE title IS NULL;
UPDATE content_items SET tags = '[]' WHERE tags IS NULL;

-- Verify the changes
SELECT column_name, data_type, is_nullable 
FROM information_schema.columns 
WHERE table_name = 'content_items' 
ORDER BY ordinal_position;
