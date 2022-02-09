# import traceback
# from gesto.myLogger import logger
import datetime
# import os
# import inspect
# from gesto import settings
from functools import wraps
import logging
# import util1.util
# from django.http import HttpResponse
from django.core.handlers.wsgi import WSGIRequest
# from django.shortcuts import render

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
                # # trace first "request" parameter
                request = get_request(*args, **kwargs)
                # if request is not None:
                #     util1.util.traceRequest(request)

                if len(args) > 0:
                    for ctr, arg in enumerate(args, start=1):
                        if isinstance(arg, dict):
                            if "request" in arg:
                                logger.info(" arg {}: {}".format(ctr, "don't trace this argument, contains request"))
                            elif any(["documentNo" in arg and "ops" in arg and func.__name__ == "needs_exporting"]):
                                logger.info(" arg {}: don't trace operation string json, {}".format(ctr, func.__name__))
                            else:
                                logger.info(arg)
                        elif str(type(arg)) == "<class 'winmentor.WinMentor'>":
                            pass
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

            # storing time after function execution
            logger.info("<<< {}() - duration = {}".format(func.__name__, datetime.datetime.now() - start))
            return result

        return wrapper_time_log_decorator

    return time_log_decorator(print_args) if callable(print_args) else time_log_decorator