# Performance Tuning

> Optimize Huntarr for your specific environment and usage patterns

## Understanding Performance Factors

Huntarr's performance is influenced by several key factors:

1. **System Resources**: CPU, memory, and disk I/O available to Huntarr
2. **Network Conditions**: Latency and bandwidth to your *arr applications
3. ***Arr Application Performance**: How quickly your *arr applications respond to API requests
4. **Library Size**: Total number of media items being managed
5. **Concurrent Operations**: Number of simultaneous searches and connections

This guide will help you optimize these factors for your specific environment.

## Resource Optimization

### System Requirements

Huntarr's requirements vary based on your library size and activity level:

| Library Size | Recommended CPU | Recommended RAM | Storage |
|--------------|----------------|-----------------|---------|
| Small (<1000 items) | 1 CPU core | 512MB | 1GB |
| Medium (1000-5000 items) | 2 CPU cores | 1GB | 2GB |
| Large (5000+ items) | 4 CPU cores | 2GB+ | 5GB+ |

### Docker Resource Allocation

If running in Docker, consider setting explicit resource limits:

```yaml
version: '3'
services:
  huntarr:
    # ... other configuration ...
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M
```

This ensures Huntarr has enough resources while preventing it from consuming everything.

## Search Configuration Optimization

### Search Volume Settings

Adjust the number of items searched per cycle based on your system capabilities:

| System Capability | Missing Items | Upgrade Items | Sleep Duration |
|-------------------|---------------|---------------|----------------|
| Low-end (e.g., Raspberry Pi) | 1-2 | 0-1 | 15-30 minutes |
| Mid-range (e.g., NAS) | 3-5 | 1-3 | 10-15 minutes |
| High-end (e.g., Server) | 5-10 | 3-5 | 5-10 minutes |

### Processing Order

Prioritize your most important applications:

1. Set higher search counts for important apps
2. Set lower search counts for less critical apps
3. Consider using scheduling to allocate dedicated time slots

## API Rate Limiting

### Optimal API Cap Settings

Balance between performance and rate-limiting risks:

| Scenario | Recommended API Cap |
|----------|---------------------|
| Self-hosted *arr applications | 30-60 per hour |
| Remote/shared *arr instances | 15-30 per hour |
| Public/restricted instances | 5-15 per hour |

### Connection Timeouts

Adjust timeout settings based on network conditions:

- **Fast local network**: 30-60 seconds
- **Average internet connection**: 90-120 seconds
- **Slow/unreliable connection**: 180+ seconds

## Database and State Optimization

### Stateful Management Tuning

Optimize how Huntarr tracks processed media:

- **High performance systems**: 3-5 days reset interval
- **Balanced systems**: 7 days reset interval
- **Resource-constrained systems**: 10-14 days reset interval

### Database Maintenance

For long-term performance:

1. Periodically restart Huntarr to clear cached data
2. Consider regular database vacuum operations
3. Monitor disk space for log growth

## Scheduling Strategies

### Time-Based Resource Allocation

Create schedules that optimize resource usage:

| Time Period | Suggested Activity |
|-------------|-------------------|
| Off-peak hours (night) | Heavy searching (missing + upgrades) |
| Medium usage hours | Moderate searching (missing only) |
| Peak usage hours | Minimal activity or paused |

### Device-Specific Scheduling

Adapt scheduling to your device type:

- **Always-on servers**: Distribute load throughout the day
- **NAS devices**: Run intensive tasks during low-usage hours
- **Desktop/part-time systems**: Concentrate activity during powered-on hours

## Network Optimization

### Reducing Network Overhead

Minimize network impact:

1. Run Huntarr on the same network as your *arr applications
2. Consider running everything on the same machine when possible
3. Adjust sleep durations based on network latency

### SSL Considerations

Balance security with performance:

- Enable SSL verification for internet-exposed services
- Consider disabling SSL verification for local network services if using self-signed certificates
- Implement proper certificates rather than disabling verification when possible

## Advanced Techniques

### Docker Compose Network Optimization

For Docker setups, use internal networks:

```yaml
version: '3'
services:
  huntarr:
    # ... other configuration ...
    networks:
      - arr_network
  
  # Define the other services in the same docker-compose
  sonarr:
    # ... sonarr configuration ...
    networks:
      - arr_network
      
networks:
  arr_network:
    driver: bridge
```

This keeps traffic between containers on an internal network for better performance.

### Multi-Threading Configuration

For systems with many CPU cores:

- Increase the number of items processed per cycle
- Reduce sleep durations
- Consider running multiple cycles in parallel (advanced users only)

## Monitoring Performance

### Key Metrics to Watch

Track these indicators to assess performance:

1. **CPU and Memory Usage**: Should remain stable
2. **API Usage**: Monitor the API counters in the dashboard
3. **Successful Searches**: Track "Searches Triggered" vs error rates
4. **Processing Time**: Check logs for search duration patterns

### Log Level Adjustment

Optimize logging for your needs:

- **Debug Mode OFF**: Better performance, less detail
- **Debug Mode ON**: More detailed logging, slightly higher resource usage

## Troubleshooting Performance Issues

### High CPU Usage

If CPU usage is excessive:

1. Reduce items searched per cycle
2. Increase sleep duration
3. Check for network issues causing retries

### Memory Leaks

If memory usage grows continuously:

1. Restart Huntarr regularly
2. Update to the latest version
3. Consider running in a container with memory limits

## Real-World Configurations

### Raspberry Pi Setup

```yaml
# Config for resource-limited devices
sonarr:
  hunt_missing_items: 1
  hunt_upgrade_items: 0
  sleep_duration: 1800  # 30 minutes
  hourly_cap: 15
```

### NAS Configuration

```yaml
# Balanced config for NAS devices
radarr:
  hunt_missing_movies: 3
  hunt_upgrade_movies: 1
  sleep_duration: 900  # 15 minutes
  hourly_cap: 30
```

### High-Performance Server

```yaml
# Performance config for dedicated servers
sonarr:
  hunt_missing_items: 10
  hunt_upgrade_items: 5
  sleep_duration: 300  # 5 minutes
  hourly_cap: 60
```

## Next Steps

After optimizing performance, consider exploring:

- [Scheduling](../guides/scheduling.md) for more advanced time management
- [Multi-Instance Setup](../guides/multi-instance.md) for specialized configurations
- [Swaparr Integration](../guides/swaparr.md) for managing stalled downloads 