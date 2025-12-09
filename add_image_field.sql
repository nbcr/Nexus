-- Add local_image_path column if it doesn't exist
ALTER TABLE content_items
ADD COLUMN IF NOT EXISTS local_image_path VARCHAR(255);

-- Update alembic_version to mark migration as applied
INSERT INTO alembic_version (version_num) VALUES ('010')
ON CONFLICT DO NOTHING;
