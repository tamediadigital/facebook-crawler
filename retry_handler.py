import functools


def retry(exception_to_check, logger, tries=3):
    def deco_retry(f):
        @functools.wraps(f)
        def f_retry(*args, **kwargs):
            m_tries = tries
            while m_tries > 1:
                try:
                    return f(*args, **kwargs)
                except exception_to_check as e:
                    logger.error(e)
                    m_tries -= 1

            return f(*args, **kwargs)
        return f_retry
    return deco_retry
