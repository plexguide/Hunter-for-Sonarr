# Scheduling Guide

> Control when Huntarr runs searches to optimize resource usage and media hunting efficiency

## Understanding Huntarr Scheduling

The scheduling system in Huntarr gives you precise control over when media searches and upgrades happen. This capability allows you to:

- Run intensive operations during off-peak hours
- Reduce system resource contention 
- Avoid network congestion
- Align media hunting with when new content is typically released
- Divide workloads across different time periods

## The Scheduling Interface

Huntarr's scheduling interface provides a visual calendar where you can:

- Set active/inactive periods by clicking time slots
- Create rules for different days of the week
- Apply global or app-specific schedules
- See scheduling conflicts and overlaps

### Accessing Scheduling

To access the scheduling interface:

1. Navigate to the main menu
2. Select **Scheduling**
3. The default view shows the weekly schedule grid

### Understanding the Schedule Grid

The schedule grid displays:

- Rows for each day of the week
- Columns for each hour of the day
- Colored blocks indicating active periods
- White/empty blocks indicating inactive periods

## Creating and Managing Schedules

### Basic Scheduling

To set up a basic schedule:

1. Click on any time slot in the grid to toggle it active/inactive
2. Active slots will be colored, indicating Huntarr will run during these times
3. Click and drag to select multiple time slots at once

### Creating Schedule Rules

For more advanced control:

1. Click the **Add Rule** button
2. Configure the rule options:
   - **Days**: Select which days this rule applies to
   - **Start Time**: When the activity period begins
   - **End Time**: When the activity period ends
   - **Active**: Whether Huntarr should be active or inactive during this period
   - **Applications**: Which apps this rule applies to (All or specific apps)
3. Click **Save** to apply the rule

### Schedule Rule Examples

**Example 1: Overnight Processing**
- Days: All
- Time: 1:00 AM - 6:00 AM
- Active: Yes
- Applications: All

**Example 2: Weekend-Only Upgrades**
- Days: Saturday, Sunday
- Time: 9:00 AM - 5:00 PM
- Active: Yes
- Applications: All
- Mode: Upgrades Only

**Example 3: Disable During Peak Hours**
- Days: Monday-Friday
- Time: 6:00 PM - 10:00 PM
- Active: No
- Applications: All

### Editing and Removing Rules

To manage existing rules:

1. Find the rule in the **Active Rules** section
2. Click the **Edit** (pencil) icon to modify the rule
3. Click the **Delete** (trash) icon to remove the rule
4. Confirm any deletion when prompted

## Advanced Scheduling Strategies

### Time-Based Activity Types

Optimize different types of activities at different times:

1. **Missing Content Focus**: Schedule specific periods just for finding missing content
2. **Upgrade Focus**: Schedule specific periods focused on quality upgrades
3. **Mixed Operations**: Allow both operations during less restricted time periods

### App-Specific Scheduling

Create dedicated schedules for each application:

1. Navigate to the **App-Specific Rules** tab
2. Select the application you want to schedule
3. Create rules that apply only to that application
4. This allows prioritizing more important apps during prime time

### Importing and Exporting Schedules

Share or backup your schedules:

1. Click the **Export** button to download your current schedule configuration
2. Use **Import** to load a previously exported schedule
3. This is useful when setting up multiple instances of Huntarr

## Real-World Scheduling Scenarios

### Work/Home Schedule

For a home server used during evenings and weekends:

- **Weekday Days (7:00 AM - 5:00 PM)**: Full activity (while you're at work)
- **Weekday Evenings (5:00 PM - 11:00 PM)**: Limited activity (using minimal resources)
- **Weekday Nights (11:00 PM - 7:00 AM)**: Full activity
- **Weekends**: Reduced activity during daytime, full activity overnight

### Download Speed Management

For users with bandwidth caps or slower connections:

- **Peak Hours (6:00 PM - 12:00 AM)**: Minimal or no activity
- **Off-Peak Hours (12:00 AM - 6:00 AM)**: Full activity
- **Daytime Hours (6:00 AM - 6:00 PM)**: Moderate activity

### Media Release Alignment

Align with typical media release schedules:

- **TV Show Night (Sundays, 8:00 PM - 12:00 AM)**: Increased Sonarr activity
- **Movie Release Days (Tuesdays)**: Increased Radarr activity
- **Music Release Day (Fridays)**: Increased Lidarr activity

## Best Practices

### Scheduling for Efficiency

- **Stagger App Activity**: Avoid running all apps simultaneously
- **Align with Media Releases**: Schedule Sonarr activity to run shortly after popular show air times
- **Respect Sleep/Wake**: For devices that sleep, ensure schedules align with awake periods

### Common Scheduling Mistakes to Avoid

- **Over-scheduling**: Creating too many short active periods creates inefficient search patterns
- **No Down-time**: Always allow some inactive periods to reduce system and network load
- **Too Restrictive**: Schedules that are too limited may miss important content

### Monitoring Schedule Effectiveness

After setting up a schedule:

1. Monitor Huntarr's statistics to verify it's running during expected periods
2. Check logs for any timing issues or missed opportunities
3. Adjust schedules based on observed performance

## Troubleshooting

### Schedule Not Being Applied

If your schedule doesn't seem to be working:

1. Verify the schedule has been saved correctly
2. Check that Huntarr's system time is correct
3. Look for conflicting rules that might be overriding each other
4. Restart Huntarr to ensure the schedule is loaded properly

### Conflicting Rules

When rules conflict:

1. More specific rules generally take precedence over general ones
2. App-specific rules override global rules
3. The most recently created rule wins in case of identical conflicts

## Next Steps

With a solid understanding of scheduling, consider exploring:

- [API Rate Limiting](api-rate-limiting.md) to prevent overloading your *arr applications
- [Performance Tuning](../advanced/performance-tuning.md) to optimize Huntarr further
- [Multi-Instance Setup](multi-instance.md) for complex media library management 