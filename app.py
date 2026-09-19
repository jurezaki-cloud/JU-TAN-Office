"""JU-TAN Office Enterprise — namizna aplikacija."""

from app.core.logger import install_excepthook, logger
from app.windows.main_window import run

install_excepthook()
logger.info("JU-TAN Office Enterprise se je zagnal.")

if __name__ == "__main__":
    run()


