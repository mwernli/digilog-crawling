ALTER TABLE crawl
    ALTER COLUMN id SET DATA TYPE bigint;
ALTER SEQUENCE crawl_id_seq AS bigint;

ALTER TABLE crawl_analysis
    ALTER COLUMN id SET DATA TYPE bigint;
ALTER TABLE crawl_analysis
    ALTER COLUMN crawl_id SET DATA TYPE bigint;
ALTER SEQUENCE crawl_analysis_id_seq AS bigint;

ALTER TABLE crawl_result
    ALTER COLUMN id SET DATA TYPE bigint;
ALTER TABLE crawl_result
    ALTER COLUMN crawl_id SET DATA TYPE bigint;
ALTER SEQUENCE crawl_result_id_seq AS bigint;

ALTER TABLE crawl_stats
    ALTER COLUMN crawl_id SET DATA TYPE bigint;

ALTER TABLE crawling_queue
    ALTER COLUMN id SET DATA TYPE bigint;
ALTER SEQUENCE crawling_queue_id_seq AS bigint;

ALTER TABLE queue_crawl
    ALTER COLUMN crawl_id SET DATA TYPE bigint;
ALTER TABLE queue_crawl
    ALTER COLUMN queue_id SET DATA TYPE bigint;