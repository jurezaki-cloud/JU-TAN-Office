from app.core.logger import logger
from app.database.database import db
from app.windows.main_window import run

logger.info("JU-TAN Office Enterprise se je zagnal.")

db.initialize()

if __name__ == "__main__":
    run()