CREATE TABLE IF NOT EXISTS digilog.digilog.crawl_run_status
(
    crawl_id int NOT NULL REFERENCES digilog.digilog.municipality (id),
    queue_id        int NOT NULL REFERENCES digilog.digilog.crawling_queue (id),
    UNIQUE (municipality_id, queue_id)
);