#!/bin/bash

# Configuration
SONARR_URL="http://10.0.0.10:8989/api/v3"
API_KEY="a03c86b6292c4bd48cd5e3b84e5a4702"

echo "Fetching shows with missing episodes..."

# First, get the series list with titles
curl -s -X GET "${SONARR_URL}/series" \
     -H "X-Api-Key: ${API_KEY}" \
     -H "Content-Type: application/json" \
     > series.json

# Get missing episodes with series IDs
curl -s -X GET "${SONARR_URL}/wanted/missing?pageSize=1000" \
     -H "X-Api-Key: ${API_KEY}" \
     -H "Content-Type: application/json" \
     > missing.json

# Combine the data and count missing episodes per show
jq -s '.[0] as $series | .[1].records as $missing | 
  $missing | map(.seriesId) | 
  group_by(.) | 
  map({
    seriesId: .[0],
    count: length,
    title: ($series[] | select(.id == .[0]).title)
  }) | 
  sort_by(-.count) | 
  .[] | "\(.count) \(.title)"' series.json missing.json

# Clean up temporary files
rm -f series.json missing.json
