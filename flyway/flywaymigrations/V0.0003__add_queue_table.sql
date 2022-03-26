DROP INDEX IF EXISTS status_prio_index;
DROP TABLE IF EXISTS digilog.crawling_queue;
DROP TYPE IF EXISTS digilog.queue_status;

CREATE TYPE digilog.queue_status AS enum ('NEW', 'IN_PROGRESS', 'DONE', 'ERROR');

CREATE TABLE digilog.crawling_queue
(
    id          serial       NOT NULL PRIMARY KEY,
    top_url     varchar      NOT NULL,
    status      queue_status NOT NULL,
    priority    int          NOT NULL,
    inserted_at timestamp    NOT NULL,
    updated_at  timestamp    NOT NULL,
    reason      varchar      NOT NULL
);

CREATE INDEX status_prio_index ON digilog.crawling_queue (status, priority);