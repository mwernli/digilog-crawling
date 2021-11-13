# digilog-crawling
Crawler &amp; Data Storage for the digilog project

## Setup
After the first pull to the server run
```
cd web/
docker build -t digilogweb3 -
cd ..
docker-compose up -d
cd scrapy/
docker build -t scrapy .
```

After every pull, run the following commands from the repository's root directory:
```
docker-compose up -d
cd scrapy/
docker build -t scrapy .
```
The command `docker-compose up -d` will start the postgres-DB container (`digilog-postgres`) and the mongoDB-Container (`digilog-mongodb`). Find the exposed ports by running `docker ps` or check the file `docker-compose.yaml`. This file also includes the login information for the databases.
Additionally, the command applies migrations for the Postgres-DB using [flyway](https://github.com/flyway/flyway-docker).
All three containers will be connected to the same Docker-bridge network `digilog-data-network`.

The Dockerfile in the scrapy-folder is used for building an image which can run the scrapy crawler. The folder scrapy/digilog is the root folder of a scrapy project called digilog and will be mounted into the container at runtime. This means the image does not have to be rebuilt when making changes to the code.

## Flyway migrations
To make changes to the postgres schema or add masterdata follow these steps:
1. Create an SQL-File containing your migration in the folder `postgres/flywaymigrations/`.
2. Name the file in this pattern: `V0.XXXX__name_describing_your_script.sql`, where XXXX is the next migration number (four digits with padded zeros). The migration number must be strictly increasing and larger than any migration numbers already present in the folder.
3. Run `docker-compose up -d` in the project root directory to apply your migrations to the postgres-DB.

### Important notes about flyway migrations
* **Never** touch any of the existing migration files that have already been applied. Flyway will notice the change refuse to apply any further migrations until the issue is resolved manually.
* **Never** rename any of the existing migration files, for the same reason as above. The order of the migration files is determined by the filenames and must never change once applied.
* Make changes to schema and masterdata only through flyway migrations. This way, the postgres database can be setup anew on any machine where the project should run. It also guarantees that future migrations commited by other users will work on your local development database and the database on the server.
* Before pushing migrations to the upstream, make sure your local repository is up to date. Otherwise the order of migration files might not be correct anymore.

## Connecting to the PostgreSQL-DB

Run the following command to connect to the PostgreSQL-DB:
```
docker exec -it digilog-postgres psql postgresql://digilog@localhost/digilog
```
## Logging
All logs go to Kibana via Dockers fluentd-driver. Navigate to http://localhost:5601 to inspect the logs. Filter for 
@log_name to see the log output of a container of a specific image (postgres-db, flyway, mongo-db, scrapy).
## Crawling
### Running a crawl
Use the scrapy-image built above to run a crawl of a webpage like so:
```
docker run --rm <MODE> -v "$PWD/digilog":/src --network digilog-data-network --log-driver fluentd --log-opt fluentd-address="localhost:24224" --log-opt tag="scrapy" scrapy simple <URL>
```
where `<MODE>` is one of the following (see also [official docker documentation](https://docs.docker.com/engine/reference/run/)):
* `-d` will run the container in the background. Check the status of the running container with `docker ps`, or use `docker attach` to connect to the container and check the generated debug output.
* `-it` will run the container in interactive mode and will print all generated output directly on your console.

Note that the `<URL>` must include the protocol (http[s]://).

Additionally, any further configuration settings can be passed to scrapy with the syntax `-s SETTING_KEY1=value1 SETTING_KEY2=value2`, as documented [here](https://docs.scrapy.org/en/latest/topics/settings.html).
For example, use `-s DEPTH_LIMIT=3` to limit the depth of the crawl on large websites.

You can also use the convenience script in the scrapy folder like this:
```
./simple_crawl.sh MODE URL
```
e.g.
```
./simple_crawl.sh -d http://quotes.toscrape.com/
```
The script applies a DEPTH_LIMIT of 2.
### Crawling results
Each crawl will generate a unique record in the `crawl` table including its url and a timestamp. Then, each crawled URL will generate a record in the `crawl_result` table, including the URL, the text of the link on the page a reference to the `crawl` and to its parent page (also in `crawl_result`). The column `mongo_id` contains the `ObjectId` of the mongo-DB-Document where the actual content of the webpage is stored (database `digilog`, collection `simpleresults`). Some metadata like the `crawl_id` and `result_id` from postgres are also stored for convenience.

### Spiders
#### simple
The `simple` spider stores the raw html and raw text (html tags removed with [BeautifulSoup](https://beautiful-soup-4.readthedocs.io/en/latest/)) of each crawled web page. Only URLs from the same domain as the domain of the input URL are considered. Duplicate URLs are ignored (scrapy default).
