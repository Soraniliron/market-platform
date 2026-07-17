from datetime import datetime

from logs.logger import logger


def scheduled_test_job():
    logger.info(
        "Scheduled test job executed at %s",
        datetime.now().isoformat(),
    )
    