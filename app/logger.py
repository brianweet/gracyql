import logging
import sys
from pathlib import Path

import structlog

class EventRenamer(object):  # with a better name hopefully
    def __init__(self, field_name):
        self._field_name = field_name

    def __call__(self, logger, name, event_dict):
        if 'event' in event_dict and not isinstance(event_dict['event'], dict):
            event_dict[self._field_name] = event_dict.pop('event')
        return event_dict


def configure_logger(log_name, log_dir, log_level):
    eventrenamer = EventRenamer("message")
    timestamper = structlog.processors.TimeStamper(fmt="iso")

    shared_processors = [
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        timestamper,
        eventrenamer
    ]
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            timestamper,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.stdlib.render_to_log_kwargs,
            eventrenamer
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        processor=structlog.processors.JSONRenderer(),
        foreign_pre_chain=shared_processors,
    )

    if log_dir:
        handler = logging.FileHandler(Path(log_dir)/("%s.json.log"%log_name))
    else:
        handler = logging.StreamHandler(sys.stdout)

    handler.setFormatter(formatter)
    root_logger = logging.getLogger()
    root_logger.addHandler(handler)
    root_logger.setLevel(log_level)

    logger = structlog.get_logger(log_name)
    logger.setLevel(log_level)
    return logger
