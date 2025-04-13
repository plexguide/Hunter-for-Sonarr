from flask import Blueprint, request, jsonify
import datetime, os, requests
from primary import keys_manager

readarr_bp = Blueprint('readarr', __name__)

LOG_FILE = "/tmp/huntarr-logs/huntarr.log"

@readarr_bp.route('/test-connection', methods=['POST'])
def test_connection():
    """Test connection to a Readarr API instance"""
    data = request.json
    api_url = data.get('api_url')
    api_key = data.get('api_key')
    if not api_url or not api_key:
        return jsonify({"success": False, "message": "Missing API URL or API key"}), 400

    # For Readarr, use api/v1
    api_base = "api/v1"
    url = f"{api_url}/{api_base}/system/status"
    headers = {
        "X-Api-Key": api_key,
        "Content-Type": "application/json"
    }
    
    # Log the connection attempt
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, 'a') as f:
        f.write(f"{timestamp} - readarr - INFO - Testing connection to: {api_url}\n")
    
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
            
        # Provide more specific error messages for common issues
        if "NewConnectionError" in error_message or "ConnectionError" in error_message:
            return jsonify({"success": False, "message": f"Cannot connect to Readarr at {api_url} - Check if the service is running and URL is correct"}), 500
        elif "Timeout" in error_message:
            return jsonify({"success": False, "message": "Connection timed out - Readarr is taking too long to respond"}), 500
        else:
            return jsonify({"success": False, "message": error_message}), 500
