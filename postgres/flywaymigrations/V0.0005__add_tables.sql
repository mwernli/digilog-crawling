CREATE TABLE digilog.loc_gov_ch(
	id					serial	NOT NULL PRIMARY KEY,
	url 				varchar,
	status			int	NOT NULL,
	latitude_n	decimal	NOT NULL,
	latitude_e	decimal	NOT NULL,
	population	int,
	elevation		varchar,
	area				varchar,
	postalCode	varchar,
	gdekt				varchar,
	gdebznr			int,
	gdenr				int,
	gdename			varchar,
	gdenamk			varchar,
	gdebzna			varchar,
	gdektna			varchar,
	gdemutdat		varchar
);
