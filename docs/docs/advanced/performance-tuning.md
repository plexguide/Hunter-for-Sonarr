---
sidebar_position: 1
---

# Performance Tuning

Huntarr is designed to be efficient, but there are several ways to optimize its performance based on your specific environment. This guide provides advanced settings and techniques to ensure Huntarr operates smoothly while minimizing resource usage.

## Understanding Resource Usage

Huntarr's resource consumption is primarily influenced by:

1. **API Request Frequency**: How often Huntarr polls your *arr applications
2. **Hunt Volume**: The number of items processed in each cycle
3. **Command Monitoring**: How often Huntarr checks the status of commands
4. **Metadata Operations**: Whether Huntarr refreshes metadata for each item

## CPU Optimization

### Reduce API Load

The most effective way to reduce CPU usage is to optimize API interactions:

```yaml
# Recommended low-CPU settings
hunt_missing: 5            # Process fewer items per cycle
hunt_upgrades: 5           # Process fewer upgrade items per cycle
sleep_duration: 1800       # Longer sleep between cycles (30 minutes)
command_wait_delay: 2      # Check command status less frequently
command_wait_attempts: 300 # Fewer status checks
skip_refresh: true         # Skip metadata refresh operations
```

### Stagger Operations

For systems running multiple *arr applications:

- Enable only one or two *arr connections at a time
- Run Huntarr on a schedule rather than continuously
- Use different sleep durations for each type of operation

## Memory Optimization

### Reduce State Data Size

Huntarr maintains state to avoid reprocessing the same items:

- Periodically clear the state files if memory usage grows
- Set lower hunt values to reduce the amount of state data

### Container Memory Limits

When running in Docker, you can limit Huntarr's memory usage:

```bash
docker run -d --name huntarr \
  --restart always \
  --memory=256m \
  --memory-swap=256m \
  -p 9705:9705 \
  -v /your-path/huntarr:/config \
  -e TZ=America/New_York \
  huntarr/huntarr:latest
```

Or in Docker Compose:

```yaml
services:
  huntarr:
    image: huntarr/huntarr:latest
    container_name: huntarr
    restart: always
    mem_limit: 256m
    memswap_limit: 256m
    ports:
      - "9705:9705"
    volumes:
      - /your-path/huntarr:/config
    environment:
      - TZ=America/New_York
```

## Disk I/O Optimization

### Minimize Metadata Operations

Metadata operations can cause significant disk activity in your *arr applications:

- Always enable `skip_refresh` to prevent metadata refreshes
- Reduce the frequency of hunting cycles with a longer `sleep_duration`

### Optimize Log Management

For systems with limited I/O capacity:

- Set a lower log retention period
- Use an external log management solution
- Mount the `/config/logs` directory to a separate volume with better I/O characteristics

## Network Optimization

### Reduce API Traffic

Huntarr can generate significant API traffic to your *arr applications:

- Increase `sleep_duration` to reduce the frequency of API calls
- Lower `hunt_missing` and `hunt_upgrades` values to reduce per-cycle traffic
- Set an appropriate `api_hourly_cap` to limit overall traffic

### Optimize for High-Latency Connections

If your *arr applications are on a different network or have high latency:

- Increase `universal_api_timeout` to allow more time for API responses
- Use longer `command_wait_delay` values
- Consider running Huntarr on the same network as your *arr applications

## Multi-Instance Performance

When running multiple Huntarr instances:

- Distribute connections to different *arr applications across instances
- Use staggered `sleep_duration` values to prevent simultaneous processing
- Assign different resource limits based on the importance of each instance

## Docker Host Tuning

For advanced users, optimize the Docker host for better performance:

- Use a high-performance filesystem for the configuration volume
- Allocate sufficient CPU resources for consistent performance
- Consider using host networking mode for better network performance

## Performance Monitoring

### Built-in Monitoring

Huntarr provides:

- API usage statistics in the dashboard
- Detailed logs of operations and timing

### External Monitoring

For more comprehensive monitoring:

- Use container monitoring tools like Prometheus and Grafana
- Monitor system resource usage with tools like Netdata or Glances
- Set up alerts for excessive resource usage 