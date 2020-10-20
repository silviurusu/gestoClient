# import traceback
# from gesto.myLogger import logger
import datetime
# import os
# import inspect
# from gesto import settings
from functools import wraps
import logging
import util
# from django.http import HttpResponse
from django.core.handlers.wsgi import WSGIRequest
# from django.shortcuts import render
from django.http import HttpResponse

logger = logging.getLogger(name = __name__)


def get_request(*args, **kwargs):
    request = None
    for arg in args:
        if isinstance(arg, WSGIRequest):
            request = arg
            break

    if request is None \
    and 'request' in kwargs:
        request = kwargs['request']

    return request


def time_log(print_args=True):
    def time_log_decorator(func):

        @wraps(func)
        def wrapper_time_log_decorator(*args, **kwargs):
            # storing time before function execution
            # logger.info(func)

            # if func.__name__ != "processOperationStrings":
            #     1/0

            logger.info(">>> {}()".format(func.__name__))
            if not callable(print_args) \
                    or print_args == False:
                pass
            else:
                # trace first "request" parameter
                request = get_request(*args, **kwargs)
                # if request is not None:
                #     util1.util.traceRequest(request)

                if len(args) > 0:
                    logger.info("positional args:")
                    for ctr, arg in enumerate(args, start=1):
                        if isinstance(arg, dict):
                            if "request" in arg:
                                logger.info(" arg {}: don't trace this argument, contains request".format(ctr))
                            elif "companySource" in arg and func.__name__ not in ["verifyProductUpdate", "importOperation", "processOperationStrings", ]:
                                logger.info(" arg {}: don't trace operation string json, {}".format(ctr, func.__name__))
                            else:
                                util.log_json(arg, indent=None)
                        else:
                            logger.info(arg)

                for k, arg in kwargs.items():
                    if arg == request:
                        continue
                    logger.info("{} --- {}: {}".format(func.__name__, k, arg))

            start = datetime.datetime.now()

            # if "function" not in kwargs:
            #     kwargs["function"] = []

            # kwargs["function"].append(func.__name__)

            result = func(*args, **kwargs)

            FUNCTION_DURATION = datetime.datetime.now() - start

            if result is not None \
            and isinstance(result, HttpResponse):
                try:
                    result.content = result.content.replace("FUNCTION_DURATION", "{}".format(FUNCTION_DURATION))
                except ContentNotRenderedError:
                    logger.info("no time_log information")
                    pass

            # storing time after function execution
            logger.info("<<< {}() - duration = {}".format(func.__name__, datetime.datetime.now() - start))
            return result

        return wrapper_time_log_decorator

    return time_log_decorator(print_args) if callable(print_args) else time_log_decorator


def disable_logging(lvl = logging.DEBUG):
    def actual_disable_logging(func):
        wraps(func)
        def wrapper(*args,**kwargs):
            logging.disable(lvl)
            result = func(*args,**kwargs)
            logging.disable(logging.NOTSET)
            return result
        return wrapper

    return actual_disable_logging
