#!/bin/bash

docker run -it --rm \
  -v "$PWD/src":/usr/src \
  --network digilog-data-network \
  --log-driver fluentd \
  --log-opt fluentd-address="localhost:24224" \
  --log-opt tag="scheduler" \
  scheduler "$@"