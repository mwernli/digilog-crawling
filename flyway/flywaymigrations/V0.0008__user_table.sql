DROP TABLE IF EXISTS digilog.user;
CREATE TABLE IF NOT EXISTS digilog.user
(
    id       serial  NOT NULL PRIMARY KEY,
    username varchar NOT NULL,
    email    varchar NOT NULL,
    pw_hash  varchar NOT NULL,
    UNIQUE (username),
    UNIQUE (email)
);