"""
Setup HTML template content for Huntarr
This module contains the HTML template for the setup page as a string constant.
"""

SETUP_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Huntarr Setup</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='css/bootstrap.min.css') }}">
    <link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}">
</head>
<body class="bg-dark text-white">
    <nav class="navbar navbar-expand-lg navbar-dark bg-black mb-4">
        <div class="container">
            <a class="navbar-brand" href="/">Huntarr</a>
            <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav" aria-controls="navbarNav" aria-expanded="false" aria-label="Toggle navigation">
                <span class="navbar-toggler-icon"></span>
            </button>
            <div class="collapse navbar-collapse" id="navbarNav">
                <ul class="navbar-nav ml-auto">
                    <li class="nav-item">
                        <a class="nav-link active" href="/setup">Setup</a>
                    </li>
                </ul>
            </div>
        </div>
    </nav>

    <div class="container">
        <div class="row">
            <div class="col-md-8 offset-md-2">
                <div class="card bg-secondary text-white">
                    <div class="card-header bg-primary">
                        <h2 class="card-title">Welcome to Huntarr!</h2>
                    </div>
                    <div class="card-body">
                        <p class="lead">Please configure your Arr applications to get started.</p>
                        
                        <ul class="nav nav-tabs" id="appTabs" role="tablist">
                            <li class="nav-item" role="presentation">
                                <button class="nav-link active" id="sonarr-tab" data-bs-toggle="tab" data-bs-target="#sonarr" type="button" role="tab" aria-controls="sonarr" aria-selected="true">Sonarr</button>
                            </li>
                            <li class="nav-item" role="presentation">
                                <button class="nav-link" id="radarr-tab" data-bs-toggle="tab" data-bs-target="#radarr" type="button" role="tab" aria-controls="radarr" aria-selected="false">Radarr</button>
                            </li>
                            <li class="nav-item" role="presentation">
                                <button class="nav-link" id="lidarr-tab" data-bs-toggle="tab" data-bs-target="#lidarr" type="button" role="tab" aria-controls="lidarr" aria-selected="false">Lidarr</button>
                            </li>
                            <li class="nav-item" role="presentation">
                                <button class="nav-link" id="readarr-tab" data-bs-toggle="tab" data-bs-target="#readarr" type="button" role="tab" aria-controls="readarr" aria-selected="false">Readarr</button>
                            </li>
                            <li class="nav-item" role="presentation">
                                <button class="nav-link" id="settings-tab" data-bs-toggle="tab" data-bs-target="#settings" type="button" role="tab" aria-controls="settings" aria-selected="false">Settings</button>
                            </li>
                        </ul>
                        
                        <div class="tab-content py-3" id="appTabsContent">
                            <!-- Sonarr -->
                            <div class="tab-pane fade show active" id="sonarr" role="tabpanel" aria-labelledby="sonarr-tab">
                                <form id="sonarrForm" action="/api/settings/sonarr" method="POST">
                                    <div class="mb-3">
                                        <label for="sonarrUrl" class="form-label">Sonarr URL</label>
                                        <input type="url" class="form-control" id="sonarrUrl" name="api_url" placeholder="http://localhost:8989">
                                    </div>
                                    <div class="mb-3">
                                        <label for="sonarrApiKey" class="form-label">API Key</label>
                                        <input type="text" class="form-control" id="sonarrApiKey" name="api_key">
                                    </div>
                                    <div class="mb-3 form-check">
                                        <input type="checkbox" class="form-check-input" id="sonarrHuntMissing" name="hunt_missing" value="1" checked>
                                        <label class="form-check-label" for="sonarrHuntMissing">Hunt for missing series</label>
                                    </div>
                                    <div class="mb-3 form-check">
                                        <input type="checkbox" class="form-check-input" id="sonarrHuntUpgrade" name="hunt_upgrade" value="1">
                                        <label class="form-check-label" for="sonarrHuntUpgrade">Hunt for upgrades</label>
                                    </div>
                                    <button type="submit" class="btn btn-primary">Save Sonarr Settings</button>
                                </form>
                            </div>
                            
                            <!-- Radarr -->
                            <div class="tab-pane fade" id="radarr" role="tabpanel" aria-labelledby="radarr-tab">
                                <form id="radarrForm" action="/api/settings/radarr" method="POST">
                                    <div class="mb-3">
                                        <label for="radarrUrl" class="form-label">Radarr URL</label>
                                        <input type="url" class="form-control" id="radarrUrl" name="api_url" placeholder="http://localhost:7878">
                                    </div>
                                    <div class="mb-3">
                                        <label for="radarrApiKey" class="form-label">API Key</label>
                                        <input type="text" class="form-control" id="radarrApiKey" name="api_key">
                                    </div>
                                    <div class="mb-3 form-check">
                                        <input type="checkbox" class="form-check-input" id="radarrHuntMissing" name="hunt_missing" value="1" checked>
                                        <label class="form-check-label" for="radarrHuntMissing">Hunt for missing movies</label>
                                    </div>
                                    <div class="mb-3 form-check">
                                        <input type="checkbox" class="form-check-input" id="radarrHuntUpgrade" name="hunt_upgrade" value="1">
                                        <label class="form-check-label" for="radarrHuntUpgrade">Hunt for upgrades</label>
                                    </div>
                                    <button type="submit" class="btn btn-primary">Save Radarr Settings</button>
                                </form>
                            </div>
                            
                            <!-- Lidarr -->
                            <div class="tab-pane fade" id="lidarr" role="tabpanel" aria-labelledby="lidarr-tab">
                                <form id="lidarrForm" action="/api/settings/lidarr" method="POST">
                                    <div class="mb-3">
                                        <label for="lidarrUrl" class="form-label">Lidarr URL</label>
                                        <input type="url" class="form-control" id="lidarrUrl" name="api_url" placeholder="http://localhost:8686">
                                    </div>
                                    <div class="mb-3">
                                        <label for="lidarrApiKey" class="form-label">API Key</label>
                                        <input type="text" class="form-control" id="lidarrApiKey" name="api_key">
                                    </div>
                                    <div class="mb-3 form-check">
                                        <input type="checkbox" class="form-check-input" id="lidarrHuntMissing" name="hunt_missing" value="1" checked>
                                        <label class="form-check-label" for="lidarrHuntMissing">Hunt for missing music</label>
                                    </div>
                                    <div class="mb-3 form-check">
                                        <input type="checkbox" class="form-check-input" id="lidarrHuntUpgrade" name="hunt_upgrade" value="1">
                                        <label class="form-check-label" for="lidarrHuntUpgrade">Hunt for upgrades</label>
                                    </div>
                                    <button type="submit" class="btn btn-primary">Save Lidarr Settings</button>
                                </form>
                            </div>
                            
                            <!-- Readarr -->
                            <div class="tab-pane fade" id="readarr" role="tabpanel" aria-labelledby="readarr-tab">
                                <form id="readarrForm" action="/api/settings/readarr" method="POST">
                                    <div class="mb-3">
                                        <label for="readarrUrl" class="form-label">Readarr URL</label>
                                        <input type="url" class="form-control" id="readarrUrl" name="api_url" placeholder="http://localhost:8787">
                                    </div>
                                    <div class="mb-3">
                                        <label for="readarrApiKey" class="form-label">API Key</label>
                                        <input type="text" class="form-control" id="readarrApiKey" name="api_key">
                                    </div>
                                    <div class="mb-3 form-check">
                                        <input type="checkbox" class="form-check-input" id="readarrHuntMissing" name="hunt_missing" value="1" checked>
                                        <label class="form-check-label" for="readarrHuntMissing">Hunt for missing books</label>
                                    </div>
                                    <div class="mb-3 form-check">
                                        <input type="checkbox" class="form-check-input" id="readarrHuntUpgrade" name="hunt_upgrade" value="1">
                                        <label class="form-check-label" for="readarrHuntUpgrade">Hunt for upgrades</label>
                                    </div>
                                    <button type="submit" class="btn btn-primary">Save Readarr Settings</button>
                                </form>
                            </div>
                            
                            <!-- General Settings -->
                            <div class="tab-pane fade" id="settings" role="tabpanel" aria-labelledby="settings-tab">
                                <form id="generalForm" action="/api/settings/general" method="POST">
                                    <div class="mb-3">
                                        <label for="sleepDuration" class="form-label">Sleep Duration (seconds)</label>
                                        <input type="number" class="form-control" id="sleepDuration" name="sleep_duration" value="900" min="60">
                                        <div class="form-text text-light">Time between hunt cycles.</div>
                                    </div>
                                    <div class="mb-3">
                                        <label for="stateResetInterval" class="form-label">State Reset Interval (hours)</label>
                                        <input type="number" class="form-control" id="stateResetInterval" name="state_reset_interval" value="168" min="1">
                                        <div class="form-text text-light">How often to reset the hunt state.</div>
                                    </div>
                                    <div class="mb-3 form-check">
                                        <input type="checkbox" class="form-check-input" id="monitoredOnly" name="monitored_only" value="1" checked>
                                        <label class="form-check-label" for="monitoredOnly">Only process monitored items</label>
                                    </div>
                                    <div class="mb-3 form-check">
                                        <input type="checkbox" class="form-check-input" id="debugMode" name="debug_mode" value="1">
                                        <label class="form-check-label" for="debugMode">Debug Mode</label>
                                    </div>
                                    <button type="submit" class="btn btn-primary">Save General Settings</button>
                                </form>
                            </div>
                        </div>
                    </div>
                    <div class="card-footer">
                        <div class="text-center">
                            <a href="/" class="btn btn-success">Go to Dashboard</a>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <footer class="mt-5 text-center">
        <div class="container">
            <p>Huntarr &copy; 2023-2025</p>
        </div>
    </footer>

    <script src="{{ url_for('static', filename='js/bootstrap.bundle.min.js') }}"></script>
    <script>
        // Save form data to settings
        document.querySelectorAll('form').forEach(form => {
            form.addEventListener('submit', function(e) {
                e.preventDefault();
                const formData = new FormData(this);
                const jsonData = {};
                
                formData.forEach((value, key) => {
                    if (key === 'hunt_missing' || key === 'hunt_upgrade' || key === 'monitored_only' || key === 'debug_mode') {
                        jsonData[key] = value === '1';
                    } else if (key === 'sleep_duration' || key === 'state_reset_interval') {
                        jsonData[key] = parseInt(value);
                    } else {
                        jsonData[key] = value;
                    }
                });
                
                fetch(this.action, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(jsonData)
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        alert('Settings saved successfully!');
                    } else {
                        alert('Error saving settings: ' + data.error);
                    }
                })
                .catch(error => {
                    alert('Error saving settings: ' + error);
                });
            });
        });
        
        // Load existing settings
        window.addEventListener('DOMContentLoaded', () => {
            const loadSettings = (appType) => {
                fetch(`/api/settings/${appType}`)
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        const settings = data.data;
                        for (const key in settings) {
                            const elem = document.querySelector(`#${appType}Form [name="${key}"]`);
                            if (elem) {
                                if (elem.type === 'checkbox') {
                                    elem.checked = settings[key];
                                } else {
                                    elem.value = settings[key];
                                }
                            }
                        }
                    }
                })
                .catch(error => console.error(`Error loading ${appType} settings:`, error));
            };
            
            loadSettings('sonarr');
            loadSettings('radarr');
            loadSettings('lidarr');
            loadSettings('readarr');
            loadSettings('general');
        });
    </script>
</body>
</html>"""

INDEX_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Huntarr Dashboard</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='css/bootstrap.min.css') }}">
    <link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}">
</head>
<body class="bg-dark text-white">
    <nav class="navbar navbar-expand-lg navbar-dark bg-black mb-4">
        <div class="container">
            <a class="navbar-brand" href="/">Huntarr</a>
            <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav" aria-controls="navbarNav" aria-expanded="false" aria-label="Toggle navigation">
                <span class="navbar-toggler-icon"></span>
            </button>
            <div class="collapse navbar-collapse" id="navbarNav">
                <ul class="navbar-nav ml-auto">
                    <li class="nav-item">
                        <a class="nav-link" href="/setup">Setup</a>
                    </li>
                </ul>
            </div>
        </div>
    </nav>

    <div class="container">
        <div class="row">
            <div class="col-md-12">
                <div class="card bg-secondary text-white mb-4">
                    <div class="card-header bg-primary">
                        <h2 class="card-title">Huntarr Dashboard</h2>
                    </div>
                    <div class="card-body">
                        <div class="row">
                            <div class="col-md-3 mb-4">
                                <div class="card text-white bg-dark h-100">
                                    <div class="card-header">Sonarr</div>
                                    <div class="card-body">
                                        <h5 class="card-title" id="sonarrStatus">Not Configured</h5>
                                        <p class="card-text" id="sonarrInfo">Configure in Setup</p>
                                    </div>
                                </div>
                            </div>
                            <div class="col-md-3 mb-4">
                                <div class="card text-white bg-dark h-100">
                                    <div class="card-header">Radarr</div>
                                    <div class="card-body">
                                        <h5 class="card-title" id="radarrStatus">Not Configured</h5>
                                        <p class="card-text" id="radarrInfo">Configure in Setup</p>
                                    </div>
                                </div>
                            </div>
                            <div class="col-md-3 mb-4">
                                <div class="card text-white bg-dark h-100">
                                    <div class="card-header">Lidarr</div>
                                    <div class="card-body">
                                        <h5 class="card-title" id="lidarrStatus">Not Configured</h5>
                                        <p class="card-text" id="lidarrInfo">Configure in Setup</p>
                                    </div>
                                </div>
                            </div>
                            <div class="col-md-3 mb-4">
                                <div class="card text-white bg-dark h-100">
                                    <div class="card-header">Readarr</div>
                                    <div class="card-body">
                                        <h5 class="card-title" id="readarrStatus">Not Configured</h5>
                                        <p class="card-text" id="readarrInfo">Configure in Setup</p>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="card bg-secondary text-white mb-4">
                    <div class="card-header bg-primary">
                        <h3 class="card-title">Recent Activity</h3>
                    </div>
                    <div class="card-body">
                        <div class="table-responsive">
                            <table class="table table-dark table-hover">
                                <thead>
                                    <tr>
                                        <th>Time</th>
                                        <th>App</th>
                                        <th>Action</th>
                                        <th>Item</th>
                                    </tr>
                                </thead>
                                <tbody id="activityTable">
                                    <tr>
                                        <td colspan="4" class="text-center">No recent activity</td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
                
                <div class="card bg-secondary text-white mb-4">
                    <div class="card-header bg-primary">
                        <h3 class="card-title">System Status</h3>
                    </div>
                    <div class="card-body">
                        <div class="row">
                            <div class="col-md-4">
                                <div class="card text-white bg-dark mb-3">
                                    <div class="card-header">Server Status</div>
                                    <div class="card-body">
                                        <h5 class="card-title" id="serverStatus">Running</h5>
                                        <p class="card-text" id="serverUptime">Uptime: Loading...</p>
                                    </div>
                                </div>
                            </div>
                            <div class="col-md-4">
                                <div class="card text-white bg-dark mb-3">
                                    <div class="card-header">Items Processed</div>
                                    <div class="card-body">
                                        <h5 class="card-title" id="itemsProcessed">0</h5>
                                        <p class="card-text">Since last reset</p>
                                    </div>
                                </div>
                            </div>
                            <div class="col-md-4">
                                <div class="card text-white bg-dark mb-3">
                                    <div class="card-header">Download Queue</div>
                                    <div class="card-body">
                                        <h5 class="card-title" id="downloadQueue">0</h5>
                                        <p class="card-text">Items in download queue</p>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <footer class="mt-5 text-center">
        <div class="container">
            <p>Huntarr &copy; 2023-2025</p>
        </div>
    </footer>

    <script src="{{ url_for('static', filename='js/bootstrap.bundle.min.js') }}"></script>
    <script>
        // Function to load app status
        function updateAppStatus() {
            fetch('/api/status')
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    const status = data.data;
                    
                    // Update app statuses
                    ['sonarr', 'radarr', 'lidarr', 'readarr'].forEach(app => {
                        const appStatus = document.getElementById(`${app}Status`);
                        const appInfo = document.getElementById(`${app}Info`);
                        
                        if (status[app] && status[app].configured) {
                            appStatus.textContent = status[app].enabled ? 'Active' : 'Disabled';
                            appInfo.textContent = `Items: ${status[app].items_processed || 0}`;
                        } else {
                            appStatus.textContent = 'Not Configured';
                            appInfo.textContent = 'Configure in Setup';
                        }
                    });
                    
                    // Update system status
                    document.getElementById('serverUptime').textContent = `Uptime: ${status.uptime || 'Unknown'}`;
                    document.getElementById('itemsProcessed').textContent = status.total_processed || 0;
                    document.getElementById('downloadQueue').textContent = status.download_queue || 0;
                    
                    // Update activity table
                    const activityTable = document.getElementById('activityTable');
                    if (status.recent_activity && status.recent_activity.length > 0) {
                        activityTable.innerHTML = '';
                        status.recent_activity.forEach(activity => {
                            activityTable.innerHTML += `
                                <tr>
                                    <td>${activity.time}</td>
                                    <td>${activity.app}</td>
                                    <td>${activity.action}</td>
                                    <td>${activity.item}</td>
                                </tr>
                            `;
                        });
                    } else {
                        activityTable.innerHTML = '<tr><td colspan="4" class="text-center">No recent activity</td></tr>';
                    }
                }
            })
            .catch(error => console.error('Error fetching status:', error));
        }
        
        // Update status every 10 seconds
        updateAppStatus();
        setInterval(updateAppStatus, 10000);
    </script>
</body>
</html>"""

def extract_templates(templates_dir):
    """Extract template HTML content to the templates directory"""
    import os
    
    # Create the template files
    templates = {
        "setup.html": SETUP_HTML,
        "index.html": INDEX_HTML
    }
    
    for filename, content in templates.items():
        file_path = os.path.join(templates_dir, filename)
        try:
            with open(file_path, 'w') as f:
                f.write(content)
            print(f"Created template: {file_path}")
        except Exception as e:
            print(f"Error creating template {filename}: {str(e)}")
    
    # Create minimal CSS file
    static_dir = os.path.dirname(os.path.dirname(templates_dir))
    static_dir = os.path.join(static_dir, "static")
    css_dir = os.path.join(static_dir, "css")
    
    try:
        if not os.path.exists(css_dir):
            os.makedirs(css_dir)
            
        css_file = os.path.join(css_dir, "style.css")
        with open(css_file, 'w') as f:
            f.write("""
/* Custom styles for Huntarr */
body {
    background-color: #121212;
    color: #f8f9fa;
}
.bg-black {
    background-color: #000;
}
.card-header {
    font-weight: bold;
}
""")
        print(f"Created CSS file: {css_file}")
        
    except Exception as e:
        print(f"Error creating CSS file: {str(e)}") 