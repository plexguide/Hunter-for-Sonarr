# Stateful Management

> Understanding how Huntarr tracks processed media to optimize performance and prevent redundant searches

## What is Stateful Management?

Stateful management is a core feature of Huntarr that tracks which media items have already been processed during search operations. It maintains a persistent record of:

- Media items that have been searched for missing content
- Media items that have been checked for quality upgrades
- The timestamp when each item was last processed

This tracking system prevents Huntarr from repeatedly searching for the same items, which helps:

- Reduce unnecessary API requests to your *arr applications
- Prevent potential API rate limiting
- Improve overall system performance
- Ensure all media gets fair attention over time

## How Stateful Management Works

### State Creation and Storage

When Huntarr processes media items, it creates and maintains several important states:

1. **Initial State Creation**: The first time Huntarr runs, it creates a new state file
2. **State Persistence**: This information is stored in the Huntarr database
3. **Automatic Resets**: States are automatically cleared after the configured reset interval

### Item Tracking Workflow

The typical workflow for state tracking is:

1. Before processing an item, Huntarr checks if it's in the state database
2. If found and the processing time is within the reset interval, the item is skipped
3. If not found or the reset interval has passed, the item is processed
4. After processing, the item is added or updated in the state database with the current timestamp

## Configuring Stateful Management

### State Reset Interval

The most important setting for stateful management is the **State Reset Interval**:

- Found under **Settings > General > Stateful Management**
- Measured in hours (default: 168 hours / 7 days)
- Determines how long Huntarr remembers processed items

Setting this value involves balancing thoroughness with efficiency:

- **Shorter intervals** (24-72 hours): More frequent rescanning, useful for active libraries
- **Medium intervals** (3-7 days): Good balance for most users
- **Longer intervals** (7+ days): Less frequent rescanning, useful for stable libraries

### Manual State Reset

For certain situations, you might want to perform a manual reset:

1. Go to **Settings > General > Stateful Management**
2. Click the **Emergency Reset** button
3. Confirm the action when prompted

Common reasons for manual resets include:

- After significant changes to your media library
- When troubleshooting search issues
- When you want to force a complete reprocessing of all media
- After upgrading to a new version of Huntarr

## Monitoring Stateful Data

Huntarr provides visibility into its stateful management system:

- **Initial State Created**: When the state tracking first began
- **State Reset Date**: When the next automatic reset will occur

These are shown in the **Settings > General > Stateful Management** section.

## Best Practices

### Optimal State Reset Intervals

Choose your reset interval based on your media management style:

| Usage Pattern | Recommended Interval | Rationale |
|---------------|----------------------|-----------|
| Active Hunter | 24-72 hours | Frequent checking for new content and upgrades |
| Balanced | 3-7 days | Good compromise between thoroughness and efficiency |
| Stable Library | 7-14 days | Less frequent checks for established libraries |

### When to Manually Reset

Consider manually resetting the state when:

- Adding a large batch of new content to your *arr applications
- Making significant changes to quality profiles
- After fixing connectivity issues with your applications
- When you suspect searches aren't being performed as expected

### Resource Considerations

Stateful management directly impacts resource usage:

- Shorter reset intervals increase CPU, memory, and network usage
- Longer intervals reduce resource consumption but might miss some upgrades
- For resource-constrained systems, consider longer intervals (7+ days)

## Advanced Topics

### State File Location

The stateful management data is stored in:

- Docker installations: `/config/db/stateful.db`
- Native installations: In the Huntarr application data directory

### Troubleshooting State Issues

If you experience problems with stateful management:

1. Check the logs for any errors related to state tracking
2. Verify that the database is not corrupted
3. Perform a manual reset as a troubleshooting step
4. If problems persist, consider rebuilding the state database

### Custom Stateful Management

For advanced users, Huntarr supports individualized state tracking for different applications:

- Each *arr application maintains its own state records
- Reset intervals affect all applications equally
- Manual resets clear state for all applications

## Next Steps

With a good understanding of stateful management, you may want to explore:

- [Performance Tuning](performance-tuning.md) for optimizing Huntarr
- [API Rate Limiting](../guides/api-rate-limiting.md) to avoid throttling
- [Scheduling](../guides/scheduling.md) to control when Huntarr runs 