docker \
  run \
  --rm \
  -d \
  -v "$PWD/digilog":/src \
  --network digilog-data-network \
  --log-driver fluentd \
  --log-opt fluentd-address="localhost:24224" \
  --log-opt tag="scrapy" \
  --entrypoint python \
  scrapy \
  /src/queue_processor.py