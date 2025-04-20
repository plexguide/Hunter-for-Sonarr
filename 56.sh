#!/bin/bash

# Configuration
SONARR_URL="http://10.0.0.10:8989/api/v3"  # Change this to your Sonarr URL
API_KEY="a03c86b6292c4bd48cd5e3b84e5a4702"                # Replace with your Sonarr API key
PAGE_SIZE=100                              # Adjust as needed

# Simple curl command to get shows with missing episodes
echo "Shows with missing episodes:"
echo "----------------------------------------"

# Fetch missing episodes endpoint
curl -s -X GET "${SONARR_URL}/wanted/missing?pageSize=${PAGE_SIZE}&sortKey=seriesTitle&sortDirection=ascending" \
     -H "X-Api-Key: ${API_KEY}" \
     -H "Content-Type: application/json" \
     | jq -r '.records[] | "\(.series.title) - S\(.seasonNumber)E\(.episodeNumber) (Aired: \(.airDateUtc // "Not aired yet"))"' \
     | sort -u | awk -F' - ' '{print $1}' | uniq -c | sort -nr
