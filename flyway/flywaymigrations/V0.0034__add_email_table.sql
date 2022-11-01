DROP TABLE IF EXISTS digilog.municipality_email;
CREATE TABLE IF NOT EXISTS digilog.municipality_email (
    id        serial    NOT NULL PRIMARY KEY,
    municipality_id int REFERENCES municipality(id),
    last_crawl      int REFERENCES crawl(id),
    email           varchar 
);