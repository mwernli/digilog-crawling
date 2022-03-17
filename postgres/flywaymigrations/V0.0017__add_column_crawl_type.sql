ALTER TABLE crawl
ADD crawl_type varchar NOT NULL;

ALTER TABLE crawling_queue
ADD crawl_type varchar NOT NULL;