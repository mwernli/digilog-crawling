ALTER TABLE crawling_queue DROP COLUMN IF EXISTS scrapy_settings;
ALTER TABLE crawling_queue ADD COLUMN IF NOT EXISTS scrapy_settings jsonb NOT NULL DEFAULT '{"DEPTH_LIMIT": 2}';