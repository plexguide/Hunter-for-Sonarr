# Huntarr UI Migration Guide

Huntarr now includes a brand new, modern user interface with improved design and usability. This guide will help you switch to the new UI.

## Automatic Migration

To automatically switch to the new UI, run:

```bash
python migrate_ui.py
```

This script will:
1. Verify all required UI files are present
2. Configure your installation to use the new UI by default

## Manual Access

You can manually access the new UI at these URLs:
- Main interface: `http://your-server/new`
- User settings: `http://your-server/user/new`

## Switching Between Interfaces

- To temporarily use the classic UI: `http://your-server/?ui=classic`
- To temporarily use the new UI: `http://your-server/?ui=new`

## New Features in the Modern UI

- Responsive design that works well on all device sizes
- Improved dark/light theme switching
- More intuitive navigation
- Dashboard-style home page with status cards
- Better organized settings interface
- Enhanced log viewing experience

## Reporting Issues

If you encounter any problems with the new UI, please report them on our GitHub issue tracker.
