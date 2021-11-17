DROP TABLE IF EXISTS digilog.crawl_analysis;
CREATE TABLE IF NOT EXISTS digilog.crawl_analysis
(
    id 					int     NOT NULL PRIMARY KEY,
    crawl_id 			int		NOT NULL
    mongo_analysis_id 	varchar NOT NULL
);