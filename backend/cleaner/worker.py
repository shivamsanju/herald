from celery import Celery

import utils
from config import config

logger = utils.get_logger("cleaner")

worker = Celery(
    "cleaner", broker=f"redis://{config.get('REDIS_HOST')}:{config.get('REDIS_PORT')}/0"
)


worker.conf.task_create_missing_queues = True
worker.conf.task_acks_late = False
worker.conf.broker_connection_retry_on_startup = True
worker.conf.worker_hijack_root_logger = False

try:
    worker.autodiscover_tasks(["cleaner.tasks"])
except Exception as e:
    logger.exception(str(e))
    raise utils.HeraldAppException(str(e))