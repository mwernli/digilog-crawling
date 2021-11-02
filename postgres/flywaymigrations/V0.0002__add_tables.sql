CREATE TABLE digilog.local_gov_ch(
	id		serial	NOT NULL PRIMARY KEY,
	status		int	NOT NULL,
	latitude_N	decimal	NOT NULL,
	latitude_E	decimal	NOT NULL,
	population	int,
	elevation	varchar,
	area		varchar,
	postalCode	varchar
);
