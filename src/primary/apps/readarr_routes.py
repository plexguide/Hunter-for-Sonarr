#!/usr/bin/env python3

from flask import Blueprint, request, jsonify
import datetime, os, requests
from src.primary import keys_manager

readarr_bp = Blueprint('readarr', __name__)

LOG_FILE = "/tmp/huntarr-logs/huntarr.log"

@readarr_bp.route('/test-connection', methods=['POST'])
def test_connection():
    """Test connection to a Readarr API instance"""
    data = request.json
    api_url = data.get('api_url')
    api_key = data.get('api_key')

    if not api_url or not api_key:
        return jsonify({"success": False, "message": "API URL and API Key are required"}), 400

    headers = {'X-Api-Key': api_key}
    url = f"{api_url.rstrip('/')}/api/v1/system/status"
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        # This is similar to: curl -H "X-Api-Key: api-key" http://ip-address/api/v1/system/status
        response = requests.get(url, headers=headers, timeout=10)
        
        # Check status code explicitly
        if response.status_code == 401:
            with open(LOG_FILE, 'a') as f:
                f.write(f"{timestamp} - readarr - ERROR - Connection test failed: 401 Unauthorized - Invalid API key\n")
            return jsonify({"success": False, "message": "Unauthorized - Invalid API key"}), 401
        
        response.raise_for_status()
        
        # Test if response is valid JSON
        try:
            response_data = response.json()
            
            # Save the API keys only if connection test is successful
            keys_manager.save_api_keys("readarr", api_url, api_key)
            
            with open(LOG_FILE, 'a') as f:
                f.write(f"{timestamp} - readarr - INFO - Connection test successful: {api_url}\n")
                
            return jsonify({
                "success": True, 
                "message": "Successfully connected to Readarr API",
                "data": response_data
            })
            
        except ValueError:
            with open(LOG_FILE, 'a') as f:
                f.write(f"{timestamp} - readarr - ERROR - Invalid JSON response from Readarr API\n")
            return jsonify({"success": False, "message": "Invalid JSON response from Readarr API"}), 500
            
    except requests.exceptions.RequestException as e:
        error_message = str(e)
        with open(LOG_FILE, 'a') as f:
            f.write(f"{timestamp} - readarr - ERROR - Connection test failed: {api_url} - {error_message}\n")
        
        return jsonify({"success": False, "message": f"Connection failed: {error_message}"}), 500
