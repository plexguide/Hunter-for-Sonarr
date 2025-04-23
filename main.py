import sys
import time
from src.utils.logger import logger
import signal
import src.state as state
import src.api as api
import src.missing as missing
import src.upgrade as upgrade
from src.huntarr import (
    signal_handler,
    validate_config,
    settings,
    display_config
)


# Global flag to control execution
running = True


def main():
    """Main function to run the Huntarr-Sonarr application."""
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    logger.info("Starting Huntarr-Sonarr")

    # Validate configuration
    if not validate_config():
        logger.error("Invalid configuration, exiting")
        sys.exit(1)

    # Display configuration
    display_config()

    # Initialize state
    state.ensure_state_dir()

    # Check API connection
    if not api.check_api_connection():
        logger.error("Could not connect to Sonarr API, exiting")
        sys.exit(1)

    try:
        cycle_count = 0
        # Main loop
        while running:
            cycle_count += 1
            logger.info(f"Starting cycle {cycle_count}")

            try:
                # Clean expired state
                state.clean_expired_state()

                # Process missing shows with the new optimized approach
                missing.process_missing_shows()

                # Process upgradable episodes
                upgrade.process_upgradable_episodes()

                # Sleep between cycles
                if running:
                    logger.info(f"Cycle {cycle_count} completed, sleeping for {settings.SLEEP_SECONDS} seconds")
                    logger.info("⭐ Tool Great? 💰 Donate 2 Daughter's College Fund - https://donate.plex.one")
                    for _ in range(settings.SLEEP_SECONDS):
                        if not running:
                            break
                        time.sleep(1)

            except Exception as e:
                logger.error(f"Error during cycle {cycle_count}: {e}")
                # Sleep a bit before retrying
                logger.info(f"Sleeping for {settings.SLEEP_SECONDS} seconds before next attempt...")
                logger.info("⭐ Tool Great? 💰 Donate to my Daughter's College Fund - https://donate.plex.one")
                time.sleep(10)

    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down")

    logger.info("Huntarr-Sonarr shutting down")


if __name__ == "__main__":
    main()
