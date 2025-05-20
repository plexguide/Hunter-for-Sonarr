# Dry Run Mode

Huntarr.io includes a "Dry Run Mode" feature that allows you to test your configuration without making any actual changes to your systems.

## What is Dry Run Mode?

Dry Run Mode logs all actions that would normally occur, but doesn't actually execute them. This is useful for:

- Testing a new configuration to make sure it will work as expected
- Verifying which items Huntarr would search for or upgrade
- Troubleshooting issues without affecting your real data

## How to Enable Dry Run Mode

1. Go to **Settings** in the Huntarr.io web interface
2. Select the **General** settings tab 
3. In the **Advanced Settings** section, toggle on **Dry Run Mode**
4. Click **Save Settings**

![Dry Run Mode Toggle](img/dry-run-toggle.png)

## How It Works

When Dry Run Mode is enabled:

- All API calls that would normally modify data (searches, upgrades, etc.) are simulated
- Actions are logged with "DRY RUN:" prefix, showing what would have happened
- No actual changes are made to your *arr applications or download clients

This allows you to see what Huntarr would do without any risk.

## Swaparr-Specific Dry Run Setting

The Swaparr module has its own dry run setting that is independent of the global setting. This allows you to:

- Run Swaparr in dry run mode while other modules perform actions normally
- Run other modules in dry run mode while Swaparr performs actions normally

If either the global dry run setting OR the Swaparr-specific dry run setting is enabled, Swaparr will operate in dry run mode.

## Logging

When running in dry run mode, check your logs for entries that begin with `DRY RUN:` to see what actions would have been taken.