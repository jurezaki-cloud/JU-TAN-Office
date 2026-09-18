"""Module entry point for ``python -m app.main``."""

from app import __version__


def main():
    # Importing the root entry point lazily prevents UI side effects when this
    # module is inspected by tests and development tools.
    from app.windows.main_window import run
    from app.core.logger import configure_logging
    from app.database.database import db

    logger = configure_logging()
    logger.info("JU-TAN Office %s se je zagnal.", __version__)
    db.initialize()
    try:
        from app.services.backup_service import backup_service
        backup_service.create_automatic_if_due()
    except Exception:
        logger.exception("Samodejne varnostne kopije ni bilo mogoče ustvariti.")
    return run()


if __name__ == "__main__":
    main()
