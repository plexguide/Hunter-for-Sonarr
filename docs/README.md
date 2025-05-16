# Huntarr Documentation

> The Intelligent Media Hunter for your *arr Stack

![Version](https://img.shields.io/badge/Version-6.5.17-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

## What is Huntarr?

Huntarr is an intelligent media hunting tool designed to work with your existing *arr stack (Sonarr, Radarr, Lidarr, Readarr, and Whisparr). It automatically searches for missing and upgradable media in your libraries, substantially improving your media collection without manual intervention.

<div class="app-icon-grid">
  <div class="app-icon-card">
    <img src="assets/img/sonarr.png" alt="Sonarr">
    <h4>Sonarr</h4>
    <p>TV Series</p>
  </div>
  <div class="app-icon-card">
    <img src="assets/img/radarr.png" alt="Radarr">
    <h4>Radarr</h4>
    <p>Movies</p>
  </div>
  <div class="app-icon-card">
    <img src="assets/img/lidarr.png" alt="Lidarr">
    <h4>Lidarr</h4>
    <p>Music</p>
  </div>
  <div class="app-icon-card">
    <img src="assets/img/readarr.png" alt="Readarr">
    <h4>Readarr</h4>
    <p>Books</p>
  </div>
  <div class="app-icon-card">
    <img src="assets/img/whisparr.png" alt="Whisparr">
    <h4>Whisparr</h4>
    <p>Adult Content</p>
  </div>
</div>

## Key Features

<ul class="feature-list">
  <li>Automated hunting for missing media items</li>
  <li>Quality upgrades for existing content</li>
  <li>Multi-instance support for each app</li>
  <li>Advanced scheduling with calendar view</li>
  <li>Intelligent API rate limiting to prevent bans</li>
  <li>Stateful management to track processed media</li>
  <li>Easy to use web interface</li>
  <li>Docker and native installation support</li>
  <li>Detailed logging and media tracking</li>
</ul>

## Quick Start

```bash
# Pull the Docker image
docker pull plexguide/huntarr:latest

# Create and run container
docker run -d \
  --name=huntarr \
  -p 8123:8123 \
  -v /path/to/config:/config \
  --restart unless-stopped \
  plexguide/huntarr:latest
```

After installation, access the web interface at `http://your-ip:8123` and follow the setup wizard to connect your media applications.

## Why Huntarr?

Traditional *arr applications rely on RSS feeds and manual searches. Huntarr changes the game by:

- Automatically identifying and filling gaps in your media library
- Proactively searching for quality upgrades based on your profile settings
- Intelligently managing API requests to avoid rate limits
- Providing a unified interface to manage all your *arr apps

Whether you're a casual media collector or a serious data hoarder, Huntarr makes maintaining a complete, high-quality media library effortless.

<div class="card">
  <h3>💡 Pro Tips</h3>
  <ul>
    <li>Set up higher API rate limits for your local *arr instances than external ones</li>
    <li>Use the scheduling feature to run intensive tasks during off-hours</li>
    <li>Configure monitored-only option to focus on content you care about</li>
  </ul>
</div>

Ready to elevate your media management? Check out the [Installation](installation.md) guide to get started. 