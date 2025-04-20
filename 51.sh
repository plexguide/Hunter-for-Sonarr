#!/bin/bash

# Configuration
SONARR_URL="http://10.0.0.10:8989/api/v3"
API_KEY="a03c86b6292c4bd48cd5e3b84e5a4702"

# First, let's try to find the correct path for series titles
echo "Finding shows with missing episodes..."

# Method 1: Try to get series title directly
curl -s -X GET "${SONARR_URL}/wanted/missing?pageSize=100" \
     -H "X-Api-Key: ${API_KEY}" \
     -H "Content-Type: application/json" \
     | jq -r '.records[] | .series.title // .title // .seriesTitle // .seriesObject.title // .show.title' | sort | uniq -c | sort -nr

# If that doesn't work, let's try a more comprehensive approach
echo -e "\nAlternate method:"
curl -s -X GET "${SONARR_URL}/wanted/missing?pageSize=100" \
     -H "X-Api-Key: ${API_KEY}" \
     -H "Content-Type: application/json" \
     | jq -r '.records[] | select(.series) | .series.title?' | sort | uniq -c | sort -nr
