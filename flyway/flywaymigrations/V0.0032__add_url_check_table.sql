DROP TABLE IF EXISTS digilog.url_check;
CREATE TABLE IF NOT EXISTS digilog.url_check (
    url        text      NOT NULL PRIMARY KEY,
    last_check timestamp NOT NULL,
    outcome    varchar   NOT NULL,
    attempts   int       NOT NULL
);