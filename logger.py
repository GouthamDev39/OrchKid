# logger.py
import logging
from logging.handlers import RotatingFileHandler

LOG_FILE = "orchestrator.log"

# Configure root logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),  # Logs to console
        RotatingFileHandler(LOG_FILE, maxBytes=1_000_000, backupCount=5)  # Logs to file with rotation
    ]
)

logger = logging.getLogger("orchestrator")
