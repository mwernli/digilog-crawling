#!/bin/bash
docker run --name digilog-analysis-queue-processor -t --rm --network digilog-data-network analysis_queued
