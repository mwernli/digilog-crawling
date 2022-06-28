CREATE TABLE IF NOT EXISTS digilog.digilog.crawl_run_status
(
    crawl_id int NOT NULL PRIMARY KEY REFERENCES crawl (id) ON DELETE CASCADE,
    status   varchar,
    UNIQUE (crawl_id)
);