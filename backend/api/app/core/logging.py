import logging
import sys
from app.core.config import settings

def setup_logging():
    """Configura logging estructurado (JSON en producción, texto en desarrollo)"""
    
    logger = logging.getLogger()
    logger.setLevel(settings.LOG_LEVEL)
    logger.handlers = []
    
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    
    return logger
