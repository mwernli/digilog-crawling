#!/bin/bash
docker run --name digilog-analysis-queue-processor -t --rm --network digilog-data-network gerbejon/analysis_queued:1.0.1
