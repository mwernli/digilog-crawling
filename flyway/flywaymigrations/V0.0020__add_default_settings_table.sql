DROP TABLE IF EXISTS digilog.default_scrapy_settings;
CREATE TABLE IF NOT EXISTS digilog.default_scrapy_settings (
    key   varchar NOT NULL,
    settings jsonb NOT NULL,
    UNIQUE (key)
);

INSERT INTO default_scrapy_settings (key, settings)
VALUES ('DEBUG_DEFAULT', '{
  "AUTOTHROTTLE_DEBUG": true,
  "AUTOTHROTTLE_ENABLED": true,
  "AUTOTHROTTLE_MAX_DELAY": 30,
  "AUTOTHROTTLE_START_DELAY": 0.5,
  "AUTOTHROTTLE_TARGET_CONCURRENCY": 8,
  "CLOSESPIDER_TIMEOUT": 900,
  "DEPTH_LIMIT": 2,
  "DOWNLOAD_DELAY": 0.1,
  "DOWNLOAD_MAXSIZE": 1048576,
  "DOWNLOAD_TIMEOUT": 15,
  "USER_AGENT": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.149 Safari/537.36"
}');