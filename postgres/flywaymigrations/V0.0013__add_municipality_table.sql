DROP TABLE IF EXISTS digilog.digilog.municipality;
CREATE TABLE IF NOT EXISTS digilog.digilog.municipality
(
    id       serial  NOT NULL PRIMARY KEY,
    name_de  varchar NOT NULL,
    url      varchar NOT NULL,
    state_id int     NOT NULL REFERENCES state (id)
);

CREATE INDEX on municipality (state_id);