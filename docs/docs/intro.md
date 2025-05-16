---
sidebar_position: 1
---

# Huntarr - Find Missing & Upgrade Media Items

![Huntarr Logo](/img/logo.png)

Huntarr is a specialized utility that automates discovering missing and upgrading your media collection.

## Key Features

### 1️⃣ Connect & Analyze

Huntarr connects to your Sonarr/Radarr/Lidarr/Readarr/Whisparr/Eros instances and analyzes your media libraries to identify both missing content and potential quality upgrades.

### 2️⃣ Hunt Missing Content

* 🔍 **Efficient Refreshing:** Skip metadata refresh to reduce disk I/O and database load
* 🔮 **Future-Aware:** Automatically skip content with future release dates
* 🎯 **Precise Control:** Configure exactly how many items to process per cycle
* 👀 **Monitored Only:** Focus only on content you've marked as monitored

### 3️⃣ Hunt Quality Upgrades

* ⬆️ **Quality Improvement:** Find content below your quality cutoff settings
* 📦 **Batch Processing:** Set specific numbers of upgrades to process per cycle
* 🚦 **Queue Management:** Automatically pauses when download queue exceeds your threshold
* ⏱️ **Command Monitoring:** Waits for commands to complete with consistent timeouts

### 4️⃣ API Management

* 🛡️ **Rate Protection:** Hourly caps prevent overloading your indexers
* ⏲️ **Universal Timeouts:** Consistent API timeouts (120s) across all applications
* 🔄 **Consistent Headers:** Identifies as Huntarr to all Arr applications
* 📊 **Intelligent Monitoring:** Visual indicators show API usage limits

### 5️⃣ Repeat & Rest

💤 Huntarr waits for your configured interval (adjustable in settings) before starting the next cycle, ensuring your indexers aren't overloaded while maintaining continuous improvement of your library.

## Getting Started

Ready to elevate your media collection management? Get started with Huntarr by following our [installation guide](installation).

## Supported Applications

| Application | Status          |
| ----------- | --------------- |
| Sonarr      | **✅ Ready**     |
| Radarr      | **✅ Ready**     |
| Lidarr      | **✅ Ready**     |
| Readarr     | **✅ Ready**     |
| Whisparr v2 | **✅ Ready**     |
| Whisparr v3 | **✅ Ready**     |
| Bazarr      | **❌ Not Ready** | 