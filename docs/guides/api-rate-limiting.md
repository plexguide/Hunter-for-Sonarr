# API Rate Limiting Guide

> Understand and configure API rate limiting to protect your *arr applications while maximizing Huntarr's effectiveness

## Understanding API Rate Limiting

API rate limiting is a critical feature in Huntarr that controls how frequently Huntarr can make requests to your *arr applications. This feature:

- Prevents overwhelming your *arr applications with too many requests
- Helps avoid being rate-limited or blocked by external services
- Ensures sustainable, long-term operation of your media automation stack
- Balances performance with system stability

## How API Rate Limiting Works in Huntarr

Huntarr implements a "rolling window" approach to rate limiting:

1. **Hourly Caps**: Each *arr application has a configurable maximum number of API requests per hour
2. **Rolling Window**: Limits are calculated based on the last 60 minutes, not fixed clock hours
3. **Real-time Monitoring**: Current API usage is displayed on the dashboard
4. **Adaptive Behavior**: Huntarr automatically pauses when approaching limits

### Visual Indicators

On the Huntarr dashboard, each application displays its current API usage status:

- **Green**: API usage is within safe limits (< 70% of cap)
- **Yellow**: API usage is approaching limits (70-90% of cap)
- **Red**: API usage is at or near limits (> 90% of cap)

## Configuring API Rate Limits

### Accessing API Rate Limit Settings

For each application:

1. Go to **Settings**
2. Select the appropriate tab (Sonarr, Radarr, etc.)
3. Find the **API Cap - Hourly** setting
4. Adjust the value based on your needs

### Recommended Starting Values

| Application Type | Self-Hosted | Shared/Remote | Critical/Public |
|------------------|-------------|--------------|-----------------|
| Sonarr           | 30-60       | 15-30        | 5-15            |
| Radarr           | 30-60       | 15-30        | 5-15            |
| Lidarr           | 20-40       | 10-20        | 5-10            |
| Readarr          | 20-40       | 10-20        | 5-10            |
| Whisparr         | 15-30       | 8-15         | 3-8             |

### Understanding API Request Types

Not all operations consume the same number of API requests:

| Operation Type          | Typical API Requests |
|-------------------------|----------------------|
| Checking missing status | 1-2 per item         |
| Searching for upgrades  | 2-3 per item         |
| Triggering a search     | 1 per search         |
| Monitoring search       | 1-5 per search       |

This means a single "Missing Items to Search" setting of 10 might result in 30-40 API requests during one cycle.

## Advanced API Management

### Multi-Instance Rate Management

When using multiple instances of the same application (e.g., several Radarr instances):

1. Each instance gets its own API cap
2. Consider setting different caps based on priority
3. Use scheduling to distribute API usage across time

### Dynamic Rate Limiting

Huntarr supports dynamic or "adaptive" rate limiting:

- API usage is spread over time to avoid bursts
- If approaching the limit, Huntarr slows down request frequency
- When limits are reached, requests are deferred to the next cycle

### API Efficiency Strategies

To maximize efficiency with limited API requests:

1. **Prioritization**: Focus on missing content before upgrades
2. **Batching**: Process multiple items during lower-activity periods
3. **Strategic Scheduling**: Align with your *arr applications' own scheduled tasks
4. **Progressive Caps**: Start with conservative limits and increase gradually

## Preventing Rate Limit Issues

### Warning Signs of API Overuse

Watch for these indicators that your API limits may be too high:

- Error messages in logs about rate limiting
- Inconsistent/slow responses from your *arr applications
- Increased CPU/memory usage in your *arr applications
- Applications becoming unresponsive to manual actions

### Remedial Actions

If you encounter rate limiting issues:

1. **Immediate Action**: Temporarily pause Huntarr
2. **Short-term Fix**: Reduce API caps by 50%
3. **Medium-term Solution**: Implement more strategic scheduling
4. **Long-term Strategy**: Balance Huntarr settings with your hardware capabilities

## Real-World Rate Limiting Scenarios

### Small Home Server

For a Raspberry Pi or low-power NAS:

```yaml
# Conservative settings for low-power devices
sonarr:
  hourly_cap: 15
  sleep_duration: 1800  # 30 minutes
  hunt_missing_items: 1
  hunt_upgrade_items: 0
```

### Shared Seedbox

For shared hosting environments:

```yaml
# Respectful settings for shared environments
radarr:
  hourly_cap: 20
  sleep_duration: 1200  # 20 minutes
  hunt_missing_movies: 2
  hunt_upgrade_movies: 1
```

### High-Performance Dedicated Server

For powerful home servers or dedicated machines:

```yaml
# Higher performance settings for dedicated hardware
sonarr:
  hourly_cap: 60
  sleep_duration: 600  # 10 minutes
  hunt_missing_items: 5
  hunt_upgrade_items: 3
```

## API Usage Monitoring

### Reading API Usage Stats

The dashboard provides real-time API statistics:

- **Current Usage**: How many requests have been made in the past hour
- **API Limit**: Your configured maximum
- **Usage Ratio**: Current usage as a percentage of your limit

### Log Monitoring

Check logs for API-related entries:

- **INFO**: Normal API operations
- **WARNING**: Approaching rate limits
- **ERROR**: Rate limit reached or API errors

## Troubleshooting

### Common API Issues

| Issue | Possible Causes | Solutions |
|-------|----------------|-----------|
| Rate limit errors | API cap too low for activity level | Increase cap or reduce activity |
| Connection timeouts | Network issues or *arr app overload | Extend timeout settings, reduce API load |
| Inconsistent behavior | Competing processes using the API | Coordinate schedules with other tools |
| API authentication errors | Incorrect API key or URL | Verify credentials and test connection |

### How to Reset API Counters

If you need to reset the API counters:

1. Restart the Huntarr service
2. This will clear the current rolling window counters
3. Note that this should only be done if absolutely necessary

## Best Practices Summary

1. **Start Conservative**: Begin with lower limits and increase gradually
2. **Monitor Regularly**: Check API usage patterns over several days
3. **Adjust Strategically**: Make small, incremental changes
4. **Balance Settings**: Coordinate API caps with processing amounts and sleep durations
5. **Respect Shared Resources**: Use lower caps when on shared hosting or seedboxes

## Next Steps

With a good understanding of API rate limiting, consider exploring:

- [Scheduling](scheduling.md) to distribute API usage strategically
- [Performance Tuning](../advanced/performance-tuning.md) for overall optimization
- [Stateful Management](../advanced/stateful-management.md) to reduce unnecessary API calls 