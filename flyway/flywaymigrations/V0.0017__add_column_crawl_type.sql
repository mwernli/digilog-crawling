ALTER TABLE crawl
ADD COLUMN IF NOT EXISTS crawl_type varchar NOT NULL DEFAULT '';

ALTER TABLE crawling_queue
ADD COLUMN IF NOT EXISTS crawl_type varchar NOT NULL DEFAULT '';