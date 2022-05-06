# digilog-crawling
Crawler &amp; Data Storage for the digilog project

## Setup
After the very first pull, run the following command in the project root directory:
```
docker-compose up -d
```
This will take a while because docker has to download all the images needed to run the project. After the download,
docker will automatically start all containers, including [flyway](https://github.com/flyway/flyway-docker) to migrate the database.
When starting the system for the first time you also need to create an index in Kibana in order to view the logs (see Logging section).

After every subsequent pull, some containers may have to be rebuilt, depending on what has changed. For example, after 
changes to the web application, rebuild the container using the following command:
```
docker-compose up -d --build web
```
In some cases, e.g. a pure code change, it might suffice to restart the container without rebuilding it:
```
docker restart <container-name>
```
Check the status of the system by running `docker ps`.
You should see seven digilog-containers running:
* digilog-web
* digilog-postgres
* digilog-crawl-queue-processor
* digilog-mongodb
* digilog-kibana
* digilog-fluentd
* digilog-elasticsearch

If a container is missing there was probably a problem while starting it. To find the exit code, use `docker ps -a`.
To find potential error messages, use `docker logs <container-name>`.
 
`docker ps` also displays the exposed ports for each container, accessible at `localhost:<port>`. You can also check the file `docker-compose.yaml`. This file includes the login information for the databases.

The Dockerfile in the scrapy-folder is used for building an image which can run the scrapy crawler. The folder scrapy/digilog is the root folder of a scrapy project called digilog and will be mounted into the container at runtime. This means the image does not have to be rebuilt when making changes to the code (but the container may have to be restarted).

## Flyway migrations
To make changes to the postgres schema or add masterdata follow these steps:
1. Create an SQL-File containing your migration in the folder `postgres/flywaymigrations/`.
2. Name the file in this pattern: `V0.XXXX__name_describing_your_script.sql`, where XXXX is the next migration number (four digits with padded zeros). The migration number must be strictly increasing and larger than any migration numbers already present in the folder.
3. Run `docker-compose up -d --build flyway` in the project root directory to apply your migrations to the postgres-DB.

### Important notes about flyway migrations
* **Never** touch any of the existing migration files that have already been applied. Flyway will notice the change and refuse to apply any further migrations until the issue is resolved manually.
* **Never** rename any of the existing migration files, for the same reason as above. The order of the migration files is determined by the filenames and must never change once applied.
* Make changes to schema and masterdata only through flyway migrations. This way, the postgres database can be setup anew on any machine where the project should run. It also guarantees that future migrations commited by other users will work on your local development database and the database on the server.
* Before pushing migrations to the upstream, make sure your local repository is up to date. Otherwise the order of migration files might not be correct anymore.

## Connecting to the PostgreSQL-DB

Run the following command to connect to the PostgreSQL-DB:
```
docker exec -it digilog-postgres psql postgresql://digilog@localhost/digilog
```
## Logging
All logs go to Kibana via Dockers fluentd-driver. Navigate to http://localhost:5601 to inspect the logs (choose Analytics -> Discover from the menu).

After an initial setup, you need to create an index pattern so Kibana knows which data to display.
If this is the case a button labelled "Create index pattern" should be visible after navigating to Analytics -> Discover.
Click this button and enter `fluentd-*` as the index pattern name and click "next step". Choose `@timestamp` in the dropdown and then click "Create index pattern".

Filter for @log_name to see the log output of a container of a specific image (postgres-db, flyway, mongo-db, scrapy).
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
For example, use `-s DEPTH_LIMIT=3` to limit the depth of the crawl on large websites. A full list of all possible settings can be found in the scrapy documentation [here](https://docs.scrapy.org/en/latest/topics/settings.html#built-in-settings-reference).


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
Each crawl will generate a unique record in the `crawl` table including its url and a timestamp. Then, each crawled URL will generate a record in the `crawl_result` table, including the URL, the text of the link on the page a reference to the `crawl` and to its parent page (also in `crawl_result`). The column `mongo_id` contains the `ObjectId` of the mongo-DB-Document where the actual content of the webpage is stored (database `digilog`, collection `simpleresults`). Note that page contents may not be available for every entry in `crawl_result`. Some metadata like the `crawl_id` and `result_id` from postgres are also stored for convenience.

### Spiders
#### simple
The `simple` spider stores the raw html and raw text (html tags removed with [BeautifulSoup](https://beautiful-soup-4.readthedocs.io/en/latest/)) of each crawled web page. Only URLs from the same domain as the domain of the input URL are considered. Duplicate URLs are ignored (scrapy default).

####
## Analysis
### all
The `analysis` image starts an analysis container which analysis all crawls which have not been analysed yet. Thus it checks the Postgres table `crawl_analysis`. In the column `crawl_id` all crawls executed so far ar shown. If the crawls have already been analyzed, the id of the MongoDB of the analysis collection is also stored. If the value is NULL, the analysis is still pending. The container analyzes all crawls which do not have a MongoDB Id. A container can be started by simply running `run_analysis.sh`. 
### single crawl
The `analysis_single` images allows to start an analysis on a specific crawl. Therefore a crawl id must be given when running the container. A container can be started when running the script `run_analysis_crawl.sh`. 
