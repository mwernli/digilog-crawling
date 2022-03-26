DROP TABLE IF EXISTS digilog.crawl_stats;
CREATE TABLE IF NOT EXISTS digilog.crawl_stats
(
    crawl_id       int     NOT NULL PRIMARY KEY REFERENCES crawl (id) ON DELETE CASCADE,
    mongo_stats_id varchar NOT NULL
);