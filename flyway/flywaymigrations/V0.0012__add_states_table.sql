DROP TABLE IF EXISTS digilog.digilog.state;
CREATE TABLE IF NOT EXISTS digilog.digilog.state
(
    id           serial     NOT NULL PRIMARY KEY,
    name         varchar    NOT NULL,
    country_code varchar(2) NOT NULL REFERENCES country (code)
);

INSERT INTO digilog.state
VALUES (default, 'Zürich', 'CH'),
       (default, 'Bern', 'CH'),
       (default, 'Luzern', 'CH'),
       (default, 'Uri', 'CH'),
       (default, 'Schwyz', 'CH'),
       (default, 'Obwalden', 'CH'),
       (default, 'Nidwalden', 'CH'),
       (default, 'Glarus', 'CH'),
       (default, 'Zug', 'CH'),
       (default, 'Fribourg', 'CH'),
       (default, 'Solothurn', 'CH'),
       (default, 'Basel-Stadt', 'CH'),
       (default, 'Basel-Landschaft', 'CH'),
       (default, 'Schaffhausen', 'CH'),
       (default, 'Appenzell Ausserrhoden', 'CH'),
       (default, 'Appenzell Innerrhoden', 'CH'),
       (default, 'St. Gallen', 'CH'),
       (default, 'Graubünden', 'CH'),
       (default, 'Aargau', 'CH'),
       (default, 'Thurgau', 'CH'),
       (default, 'Ticino', 'CH'),
       (default, 'Vaud', 'CH'),
       (default, 'Valais', 'CH'),
       (default, 'Neuchâtel', 'CH'),
       (default, 'Genève', 'CH'),
       (default, 'Jura', 'CH');

CREATE INDEX ON state (country_code);
