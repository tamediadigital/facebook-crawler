import logging
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')


def setup_logger(name, where, level=logging.INFO):
    if where == "stdout":
        handler = logging.StreamHandler()
    else:
        handler = logging.FileHandler(where)

    handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)

    return logger


stdout_log = setup_logger('console', 'stdout')
