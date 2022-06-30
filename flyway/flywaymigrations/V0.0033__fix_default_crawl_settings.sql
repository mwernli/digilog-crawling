UPDATE default_scrapy_settings s
SET settings = s.settings - 'CLOSESPIDER_TIMEOUT'
WHERE key like 'CRAWL%';