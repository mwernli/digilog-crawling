DROP TABLE IF EXISTS digilog.queue_crawl;
CREATE TABLE digilog.queue_crawl
(
    queue_id int NOT NULL REFERENCES digilog.crawling_queue (id),
    crawl_id int NOT NULL REFERENCES digilog.crawl (id),
    UNIQUE (queue_id, crawl_id)
);