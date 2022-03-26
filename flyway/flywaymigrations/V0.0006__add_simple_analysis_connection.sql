-- V0.00006__add_simple_analysis_connection.sql
DROP TABLE IF EXISTS digilog.crawl_analysis;
CREATE TABLE IF NOT EXISTS digilog.crawl_analysis
(
    crawl_id       int     NOT NULL PRIMARY KEY REFERENCES crawl (id) ON DELETE CASCADE,
    mongo_analysis_id varchar NOT NULL
);