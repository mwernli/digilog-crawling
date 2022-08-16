#!/bin/bash
docker build -t gerbejon/analysis_queued:1.0.3 -t gerbejon/analysis_queued:latest -f ./analysis_queued/Dockerfile .
docker push gerbejon/analysis_queued:1.0.3
docker push gerbejon/analysis_queued
