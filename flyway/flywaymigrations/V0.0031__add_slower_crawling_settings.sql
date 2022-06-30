UPDATE default_scrapy_settings dss
SET settings = u.new_settings
FROM (
         SELECT key,
                JSONB_SET(
                        settings,
                        '{CONCURRENT_REQUESTS_PER_DOMAIN}',
                        TO_JSONB(
                                GREATEST(
                                        (settings ->> 'AUTOTHROTTLE_TARGET_CONCURRENCY')::int,
                                        1::int
                                    )
                            )
                    ) AS new_settings
         FROM default_scrapy_settings
     ) AS u
WHERE dss.key = u.key;

INSERT INTO default_scrapy_settings (key, settings)
VALUES ('CALIBRATE_SLOWEST', '{
  "USER_AGENT": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.149 Safari/537.36",
  "DEPTH_LIMIT": 2,
  "DOWNLOAD_DELAY": 4,
  "DOWNLOAD_MAXSIZE": 1048576,
  "DOWNLOAD_TIMEOUT": 25,
  "AUTOTHROTTLE_DEBUG": false,
  "CLOSESPIDER_TIMEOUT": 30,
  "AUTOTHROTTLE_ENABLED": true,
  "AUTOTHROTTLE_MAX_DELAY": 30,
  "AUTOTHROTTLE_START_DELAY": 4,
  "AUTOTHROTTLE_TARGET_CONCURRENCY": 0.75,
  "CONCURRENT_REQUESTS_PER_DOMAIN": 1
}'),
       ('CRAWL_SLOWEST', '{
         "USER_AGENT": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.149 Safari/537.36",
         "DEPTH_LIMIT": 2,
         "DOWNLOAD_DELAY": 4,
         "DOWNLOAD_MAXSIZE": 1048576,
         "DOWNLOAD_TIMEOUT": 25,
         "AUTOTHROTTLE_DEBUG": false,
         "AUTOTHROTTLE_ENABLED": true,
         "AUTOTHROTTLE_MAX_DELAY": 30,
         "AUTOTHROTTLE_START_DELAY": 4,
         "AUTOTHROTTLE_TARGET_CONCURRENCY": 0.75,
         "CONCURRENT_REQUESTS_PER_DOMAIN": 1
       }');