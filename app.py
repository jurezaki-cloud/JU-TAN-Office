"""Primary JU-TAN Office entry point."""


def main():
    """Initialize the database and start the PySide6 application."""
    from app.core.logger import configure_logging
    from app.database.database import db
    from app.windows.main_window import run

    logger = configure_logging()
    logger.info("JU-TAN Office Enterprise se je zagnal.")
    db.initialize()
    try:
        from app.services.backup_service import backup_service
        backup_service.create_automatic_if_due()
    except Exception:
        logger.exception("Samodejne varnostne kopije ni bilo mogoče ustvariti.")
    return run()


if __name__ == "__main__":
    main()
