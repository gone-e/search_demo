import logging
import time
from functools import wraps


def retry_function(function_name, max_retries, *args, **kwargs):
    for retry_cnt in range(max_retries):
        try:
            return function_name(*args, **kwargs)
        except Exception as error:
            if retry_cnt + 1 == max_retries:
                logging.error("Failed %s attempt(s) at calling: %s", max_retries, function_name)
                logging.error("    args: %s", args)
                logging.error("    kwargs: %s", kwargs)
                logging.error("    error: %s", error)
                raise
            else:
                logging.warning("Failed %d attempt(s) at calling: %s", retry_cnt + 1, function_name)
                logging.warning("Retrying after %s seconds", retry_cnt ** 2)
                time.sleep((retry_cnt + 1) ** 2)


def retry(exception_to_check, tries=4, delay=1, backoff=2, logger=None):
    """
    Retry calling the decorated function using an exponential backoff.

    http://www.saltycrane.com/blog/2009/11/trying-out-retry-decorator-python/
    original from: http://wiki.python.org/moin/PythonDecoratorLibrary#Retry

    :param exception_to_check: the exception to check. may be a tuple of
        exceptions to check
    :type exception_to_check: Exception or tuple
    :param tries: number of times to try (not retry) before giving up
    :type tries: int
    :param delay: initial delay between retries in seconds
    :type delay: int
    :param backoff: backoff multiplier e.g. value of 2 will double the delay
        each retry
    :type backoff: int
    :param logger: logger to use. If None, print
    :type logger: logging.Logger instance
    """

    def deco_retry(f):
        @wraps(f)
        def f_retry(*args, **kwargs):
            mtries, mdelay = tries, delay
            while mtries > 1:
                try:
                    return f(*args, **kwargs)
                except exception_to_check:
                    msg = "%s, Retrying in %d seconds..." % (str(exception_to_check), mdelay)
                    if logger:
                        logger.exception(msg)
                    else:
                        print(msg)
                    time.sleep(mdelay)
                    mtries -= 1
                    mdelay *= backoff
            return f(*args, **kwargs)

        return f_retry  # true decorator

    return deco_retry
