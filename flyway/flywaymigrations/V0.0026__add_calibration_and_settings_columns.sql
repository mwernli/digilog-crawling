ALTER TABLE municipality
    DROP COLUMN IF EXISTS recommended_settings;

ALTER TABLE municipality
    ADD COLUMN IF NOT EXISTS recommended_settings varchar REFERENCES default_scrapy_settings (key) DEFAULT NULL;

ALTER TABLE municipality
    DROP COLUMN IF EXISTS do_not_crawl;
ALTER TABLE municipality
    ADD COLUMN IF NOT EXISTS do_not_crawl bool NOT NULL DEFAULT FALSE;

DROP INDEX IF EXISTS municipality_calibration_idx;

DROP TABLE IF EXISTS municipality_calibration;
CREATE TABLE IF NOT EXISTS municipality_calibration (
    id                    bigserial NOT NULL PRIMARY KEY,
    municipality_id       int       NOT NULL REFERENCES municipality (id),
    calibration_queue_id  int       NOT NULL REFERENCES crawling_queue (id),
    settings_key          varchar   NOT NULL REFERENCES default_scrapy_settings (key),
    analysed              bool      NOT NULL DEFAULT FALSE,
    manual_check_required bool      NOT NULL DEFAULT FALSE
);
CREATE INDEX IF NOT EXISTS municipality_calibration_idx ON municipality_calibration (municipality_id, analysed);

INSERT INTO municipality_calibration (municipality_id, calibration_queue_id, settings_key, analysed)
SELECT m.id AS municipality_id, MAX(q.id) AS last_calibration_queue_id, 'CALIBRATE' AS settings_key, FALSE AS analysed
FROM municipality m
         JOIN municipality_to_queue_entry mq ON mq.municipality_id = m.id
         JOIN crawling_queue q ON q.id = mq.queue_id AND q.crawl_type = 'calibration'
GROUP BY m.id;

INSERT INTO default_scrapy_settings (key, settings)
VALUES ('CALIBRATE_MEDIUM_FAST', '{
  "USER_AGENT": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.149 Safari/537.36",
  "DEPTH_LIMIT": 2,
  "DOWNLOAD_DELAY": 0.5,
  "DOWNLOAD_MAXSIZE": 1048576,
  "DOWNLOAD_TIMEOUT": 20,
  "AUTOTHROTTLE_DEBUG": false,
  "CLOSESPIDER_TIMEOUT": 30,
  "AUTOTHROTTLE_ENABLED": true,
  "AUTOTHROTTLE_MAX_DELAY": 30,
  "AUTOTHROTTLE_START_DELAY": 0.5,
  "AUTOTHROTTLE_TARGET_CONCURRENCY": 4
}')
ON CONFLICT (key) DO UPDATE SET settings = excluded.settings;

INSERT INTO default_scrapy_settings (key, settings)
VALUES ('CALIBRATE_MEDIUM', '{
  "USER_AGENT": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.149 Safari/537.36",
  "DEPTH_LIMIT": 2,
  "DOWNLOAD_DELAY": 0.75,
  "DOWNLOAD_MAXSIZE": 1048576,
  "DOWNLOAD_TIMEOUT": 20,
  "AUTOTHROTTLE_DEBUG": false,
  "CLOSESPIDER_TIMEOUT": 30,
  "AUTOTHROTTLE_ENABLED": true,
  "AUTOTHROTTLE_MAX_DELAY": 30,
  "AUTOTHROTTLE_START_DELAY": 1,
  "AUTOTHROTTLE_TARGET_CONCURRENCY": 2
}')
ON CONFLICT (key) DO UPDATE SET settings = excluded.settings;

INSERT INTO default_scrapy_settings (key, settings)
VALUES ('CALIBRATE_MEDIUM_SLOW', '{
  "USER_AGENT": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.149 Safari/537.36",
  "DEPTH_LIMIT": 2,
  "DOWNLOAD_DELAY": 1,
  "DOWNLOAD_MAXSIZE": 1048576,
  "DOWNLOAD_TIMEOUT": 20,
  "AUTOTHROTTLE_DEBUG": false,
  "CLOSESPIDER_TIMEOUT": 30,
  "AUTOTHROTTLE_ENABLED": true,
  "AUTOTHROTTLE_MAX_DELAY": 30,
  "AUTOTHROTTLE_START_DELAY": 1,
  "AUTOTHROTTLE_TARGET_CONCURRENCY": 1
}')
ON CONFLICT (key) DO UPDATE SET settings = excluded.settings;


INSERT INTO default_scrapy_settings (key, settings)
VALUES ('CALIBRATE_SLOW', '{
  "USER_AGENT": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.149 Safari/537.36",
  "DEPTH_LIMIT": 2,
  "DOWNLOAD_DELAY": 2,
  "DOWNLOAD_MAXSIZE": 1048576,
  "DOWNLOAD_TIMEOUT": 20,
  "AUTOTHROTTLE_DEBUG": false,
  "CLOSESPIDER_TIMEOUT": 30,
  "AUTOTHROTTLE_ENABLED": true,
  "AUTOTHROTTLE_MAX_DELAY": 30,
  "AUTOTHROTTLE_START_DELAY": 2,
  "AUTOTHROTTLE_TARGET_CONCURRENCY": 1
}')
ON CONFLICT (key) DO UPDATE SET settings = excluded.settings;


INSERT INTO default_scrapy_settings (key, settings)
VALUES ('CRAWL_FAST', '{
  "USER_AGENT": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.149 Safari/537.36",
  "DEPTH_LIMIT": 2,
  "DOWNLOAD_DELAY": 0.1,
  "DOWNLOAD_MAXSIZE": 1048576,
  "DOWNLOAD_TIMEOUT": 10,
  "AUTOTHROTTLE_DEBUG": false,
  "CLOSESPIDER_TIMEOUT": 30,
  "AUTOTHROTTLE_ENABLED": true,
  "AUTOTHROTTLE_MAX_DELAY": 30,
  "AUTOTHROTTLE_START_DELAY": 0.5,
  "AUTOTHROTTLE_TARGET_CONCURRENCY": 8
}')
ON CONFLICT (key) DO UPDATE SET settings = excluded.settings;

INSERT INTO default_scrapy_settings (key, settings)
VALUES ('CRAWL_MEDIUM_FAST', '{
  "USER_AGENT": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.149 Safari/537.36",
  "DEPTH_LIMIT": 2,
  "DOWNLOAD_DELAY": 0.5,
  "DOWNLOAD_MAXSIZE": 1048576,
  "DOWNLOAD_TIMEOUT": 20,
  "AUTOTHROTTLE_DEBUG": false,
  "AUTOTHROTTLE_ENABLED": true,
  "AUTOTHROTTLE_MAX_DELAY": 30,
  "AUTOTHROTTLE_START_DELAY": 0.5,
  "AUTOTHROTTLE_TARGET_CONCURRENCY": 4
}')
ON CONFLICT (key) DO UPDATE SET settings = excluded.settings;

INSERT INTO default_scrapy_settings (key, settings)
VALUES ('CRAWL_MEDIUM', '{
  "USER_AGENT": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.149 Safari/537.36",
  "DEPTH_LIMIT": 2,
  "DOWNLOAD_DELAY": 0.75,
  "DOWNLOAD_MAXSIZE": 1048576,
  "DOWNLOAD_TIMEOUT": 20,
  "AUTOTHROTTLE_DEBUG": false,
  "AUTOTHROTTLE_ENABLED": true,
  "AUTOTHROTTLE_MAX_DELAY": 30,
  "AUTOTHROTTLE_START_DELAY": 1,
  "AUTOTHROTTLE_TARGET_CONCURRENCY": 2
}')
ON CONFLICT (key) DO UPDATE SET settings = excluded.settings;

INSERT INTO default_scrapy_settings (key, settings)
VALUES ('CRAWL_MEDIUM_SLOW', '{
  "USER_AGENT": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.149 Safari/537.36",
  "DEPTH_LIMIT": 2,
  "DOWNLOAD_DELAY": 1,
  "DOWNLOAD_MAXSIZE": 1048576,
  "DOWNLOAD_TIMEOUT": 20,
  "AUTOTHROTTLE_DEBUG": false,
  "AUTOTHROTTLE_ENABLED": true,
  "AUTOTHROTTLE_MAX_DELAY": 30,
  "AUTOTHROTTLE_START_DELAY": 1,
  "AUTOTHROTTLE_TARGET_CONCURRENCY": 1
}')
ON CONFLICT (key) DO UPDATE SET settings = excluded.settings;


INSERT INTO default_scrapy_settings (key, settings)
VALUES ('CRAWL_SLOW', '{
  "USER_AGENT": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.149 Safari/537.36",
  "DEPTH_LIMIT": 2,
  "DOWNLOAD_DELAY": 2,
  "DOWNLOAD_MAXSIZE": 1048576,
  "DOWNLOAD_TIMEOUT": 20,
  "AUTOTHROTTLE_DEBUG": false,
  "AUTOTHROTTLE_ENABLED": true,
  "AUTOTHROTTLE_MAX_DELAY": 30,
  "AUTOTHROTTLE_START_DELAY": 2,
  "AUTOTHROTTLE_TARGET_CONCURRENCY": 1
}')
ON CONFLICT (key) DO UPDATE SET settings = excluded.settings;