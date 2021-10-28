#!/bin/bash
docker run --name web -d --rm -p 80:80 --network digilog-data-network digilogweb3
