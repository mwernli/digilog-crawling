
CREATE TABLE digilog.crawl(
    id          serial      NOT NULL PRIMARY KEY,
    inserted_at timestamp   DEFAULT now(),
    top_url     varchar     NOT NULL
);

CREATE TABLE digilog.crawl_result(
    id          serial      NOT NULL PRIMARY KEY,
    inserted_at timestamp   DEFAULT now(),
    crawl_id    int         NOT NULL REFERENCES crawl(id),
    url         varchar     NOT NULL,
    link_text   varchar     NOT NULL,
    parent      int         REFERENCES crawl_result(id),
    mongo_id	varchar     DEFAULT NULL,
    UNIQUE (crawl_id, url)
);
