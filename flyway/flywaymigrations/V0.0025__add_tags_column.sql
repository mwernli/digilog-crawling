ALTER TABLE crawling_queue
    DROP COLUMN IF EXISTS tags;
ALTER TABLE crawling_queue
    ADD COLUMN IF NOT EXISTS tags varchar[] NOT NULL DEFAULT '{}'::varchar[];

UPDATE crawling_queue
SET tags = '{"CALIBRATION", "INITIAL"}'
WHERE crawl_type = 'calibration'
  AND inserted_at < '2022-05-16T00:00:00'