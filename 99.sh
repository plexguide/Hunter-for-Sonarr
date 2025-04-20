#!/bin/bash

# Configuration
SONARR_URL="http://10.0.0.10:8989/api/v3"
API_KEY="a03c86b6292c4bd48cd5e3b84e5a4702"

# Let's first get the series endpoint to see all shows
echo "Fetching series list to match with missing episodes..."

# Get all series IDs and titles
declare -A series_map
while IFS='|' read -r id title; do
    series_map["$id"]="$title"
done < <(curl -s -X GET "${SONARR_URL}/series" \
     -H "X-Api-Key: ${API_KEY}" \
     -H "Content-Type: application/json" \
     | jq -r '.[] | "\(.id)|\(.title)"')

# Now get missing episodes and match with series
echo -e "\nFinding shows with missing episodes..."
declare -A missing_counts

# Fetch missing episodes with series info
curl -s -X GET "${SONARR_URL}/wanted/missing?pageSize=1000" \
     -H "X-Api-Key: ${API_KEY}" \
     -H "Content-Type: application/json" \
     | jq -r '.records[] | .seriesId' | while read -r series_id; do
    if [ -n "${series_map[$series_id]}" ]; then
        show_name="${series_map[$series_id]}"
        if [ -z "${missing_counts[$show_name]}" ]; then
            missing_counts["$show_name"]=1
        else
            missing_counts["$show_name"]=$((missing_counts["$show_name"] + 1))
        fi
    fi
done

# Display results
echo "----------------------------------------"
echo "Shows with missing episodes:"
echo "----------------------------------------"

for show in "${!missing_counts[@]}"; do
    printf "%4d %s\n" "${missing_counts[$show]}" "$show"
done | sort -nr
