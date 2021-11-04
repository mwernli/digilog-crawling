-- V0.0002_add_gov_tables.sql
CREATE TABLE digilog.loc_gov_ch(
	id			serial	NOT NULL PRIMARY KEY,
	url 		varchar,
	status		int,
	latitude_n	decimal,
	longitude_e	decimal,
	population	int,
	elevation	varchar,
	area		varchar,
	postalcode	varchar,
	gdekt		varchar,
	gdebznr		int,
	gdenr		int,
	gdename		varchar,
	gdenamk		varchar,
	gdebzna		varchar,
	gdektna		varchar,
	gdemutdat	varchar
);
