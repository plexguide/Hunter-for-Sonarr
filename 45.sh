#!/bin/bash

# Try different JSON paths to find the correct one
echo "Method 1: .series.title"
curl -s -X GET "http://10.0.0.10:8989/api/v3/wanted/missing?pageSize=5" \
     -H "X-Api-Key: a03c86b6292c4bd48cd5e3b84e5a4702" \
     -H "Content-Type: application/json" \
     | jq -r '.records[] | .series.title'

echo -e "\nMethod 2: .series.title?"
curl -s -X GET "http://10.0.0.10:8989/api/v3/wanted/missing?pageSize=5" \
     -H "X-Api-Key: a03c86b6292c4bd48cd5e3b84e5a4702" \
     -H "Content-Type: application/json" \
     | jq -r '.records[] | .series.title?'

echo -e "\nMethod 3: series object keys"
curl -s -X GET "http://10.0.0.10:8989/api/v3/wanted/missing?pageSize=5" \
     -H "X-Api-Key: a03c86b6292c4bd48cd5e3b84e5a4702" \
     -H "Content-Type: application/json" \
     | jq -r '.records[0].series | keys[]'

echo -e "\nMethod 4: Debug full structure"
curl -s -X GET "http://10.0.0.10:8989/api/v3/wanted/missing?pageSize=1" \
     -H "X-Api-Key: a03c86b6292c4bd48cd5e3b84e5a4702" \
     -H "Content-Type: application/json" \
     | jq '. | { record_count: (.records | length), first_record: .records[0] }'
