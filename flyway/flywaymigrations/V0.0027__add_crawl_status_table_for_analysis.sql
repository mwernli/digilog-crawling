CREATE TABLE IF NOT EXISTS digilog.digilog.crawl_run_status
(
    crawl_id int NOT NULL REFERENCES digilog.digilog.crawl (id),
    status   varchar
);