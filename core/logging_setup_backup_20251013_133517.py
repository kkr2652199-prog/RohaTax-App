import logging
from logging.handlers import RotatingFileHandler
import os


def init_logging(log_dir: str = "logs") -> None:
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, "app.log")

    root = logging.getLogger()
    root.setLevel(logging.INFO)

    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s - %(message)s"))

    # Rotating file handler ~5MB x 5 files
    fh = RotatingFileHandler(log_path, maxBytes=5 * 1024 * 1024, backupCount=5, encoding="utf-8")
    fh.setLevel(logging.INFO)
    fh.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s - %(message)s"))

    # Avoid duplicate handlers on reload
    for h in list(root.handlers):
        root.removeHandler(h)

    root.addHandler(ch)
    root.addHandler(fh)


















