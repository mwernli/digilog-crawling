docker run --rm "$1" -v "$PWD/digilog":/src --network digilog-data-network --log-driver fluentd --log-opt fluentd-address="localhost:24224" --log-opt tag="scrapy" scrapy $2
