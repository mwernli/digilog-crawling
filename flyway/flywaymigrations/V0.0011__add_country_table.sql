DROP TABLE IF EXISTS digilog.digilog.country;
CREATE TABLE IF NOT EXISTS digilog.digilog.country
(
    code    varchar(2) NOT NULL PRIMARY KEY,
    name_en varchar    NOT NULL,
    name_de varchar    NOT NULL,
    UNIQUE (code)
);

INSERT INTO digilog.country VALUES ('CH', 'Switzerland', 'Schweiz');