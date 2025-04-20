#!/bin/bash

# Simple script to get shows with missing episodes
curl -s -X GET "http://10.0.0.10:8989/api/v3/wanted/missing?pageSize=1000" \
     -H "X-Api-Key: a03c86b6292c4bd48cd5e3b84e5a4702" \
     -H "Content-Type: application/json" \
     | jq -r '.records[] | {seriesId, seriesTitle: .series.title} | select(.seriesTitle != null) | .seriesTitle' | sort | uniq -c | sort -nr
