import datetime
import settings
import logging
import functools
import re
import inspect
from configparser import ConfigParser
from django.template import loader
import traceback
import json
from decimal import Decimal
import requests
import decorators

logger = logging.getLogger(__name__)


def newException(e):
    try:
        logger.info(">>> {0}()".format(inspect.stack()[0][3]))
        start = datetime.datetime.now()

        # new Exception for today
        template = loader.get_template("mail/admin/exception.html")
        subject = "Exception at {0}()".format(inspect.stack()[1][3])

        html_part = template.render({
            "subject": subject,
            "exception": e,
            "exceptionType": type(e),
            "traceback": traceback.format_exc()
        })
        send_email(subject, html_part)

    except BaseException as e:
        logger.exception(e)

    logger.info("<<< {}() - duration = {}".format(inspect.stack()[0][3], datetime.datetime.now() - start))


def getNextDocumentNumber(type):
    cfg_file_name = 'config_documentNo_local.ini'
    cfg = ConfigParser()
    cfg.optionxform = str
    try:
        cfg.read(cfg_file_name)
    except:
        logger.exception(f"Failed to read {cfg_file_name} file")
        1/0

    docNo = cfg.getint("documentNumbers", type)
    cfg.set("documentNumbers", type, str(docNo+1))

    with open(cfg_file_name, 'w') as configfile:
        cfg.write(configfile)

    return docNo


def retToFileArray(ret, filename):
    ret = ret[0]
    retCnt = len(ret)

    thefile = open(filename+".txt", 'w')
    for ctr, r in enumerate(ret, start=1):
        thefile.write("{}/{} - {}\n".format(ctr, retCnt, r))


def cfg_has_option(section, option):
    cfg_file_name = 'config_local.ini'

    cfg = ConfigParser()
    cfg.read(cfg_file_name)

    return cfg.has_option(section, option)


def cfg_has_section(section):
    cfg_file_name = 'config_local.ini'

    cfg = ConfigParser()
    cfg.read(cfg_file_name)

    return cfg.has_section(section)


def getCfgVal(section, varName, retType=None):
    logger.info(">>> {0}()".format(inspect.stack()[0][3]))
    start = datetime.datetime.now()

    cfg_file_name = 'config_local.ini'

    cfg = ConfigParser()
    cfg.read(cfg_file_name)

    if retType == "int":
        ret = cfg.getint(section, varName)
    elif retType == "bool":
        ret = cfg.getboolean(section, varName)
    else:
        ret = cfg.get(section, varName)

    if section == "client" and varName in ['bccEmails', 'notificationEmails', ] \
    or section == "deliveryNote" and varName in ['sources', 'destinations'] \
    or section == "gesto" and varName in ['branches', ] \
    or section == "receptions" and varName in ['branches', ] \
    or section == "products" and varName in ['allowMissingDefaultGest', ]:
        ret = [x.strip() for x in ret.split(",")]

    logger.info("{}: {}".format(varName, ret))
    logger.info("<<< {}() - duration = {}".format(inspect.stack()[0][3], datetime.datetime.now() - start))
    return ret


@decorators.time_log
def send_email(subject, msg, toEmails=None, bccEmails=None, location=True, isGestoProblem=False):
    if not isGestoProblem:
        callersFrame = inspect.stack()[1][0]
    else:
        callersFrame = inspect.stack()[2][0]

    frameinfo = inspect.getframeinfo(callersFrame)

    msg = "\n" + msg
    if location:
        msg = "{}\n\n{}:{}".format(msg, frameinfo.filename, frameinfo.lineno)
    logger.info("msg: {}".format(msg))

    if msg.find("<html") == -1:
        # msg = msg.replace("<", "&lt;")
        # msg = msg.replace(">", "&gt;")
        # this one goes last
        msg = msg.replace("\n", "<br/>")

    if toEmails is None or bccEmails is None:
        # create new list, if I ever append to it the value for settings.BCC_EMAILS will change and I will
        # send emails to people I don't want'
        bccEmailsCfg = getCfgVal("client", "bccEmails")

        if toEmails is None:
            toEmails = bccEmailsCfg
            logger.info("toEmails: {0}".format(toEmails))
        elif bccEmails is None:
            bccEmails = bccEmailsCfg
            logger.info(f"bccEmails: {bccEmails}")

    email_body = {
        "subject": subject,
        "body": msg,
        "emails": toEmails,
        "from_email": settings.DEFAULT_FROM_EMAIL,
    }

    logger.info(email_body)

    baseURL = getCfgVal("gesto", "url")
    token = getCfgVal("winmentor", "companyToken")

    r = requests.post(baseURL+"/api/email/", json=email_body, headers={'GESTOTOKEN': token})
    logger.info("{} - {}".format(r.status_code, r.text))


def defaultJSON(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    elif isinstance(obj, datetime.datetime):
        return obj.strftime('%Y-%m-%d %H:%M:%S')


def getTimestamp(date):
    if isinstance(date, str):
        date = datetime.datetime.strptime(date, '%Y-%m-%d %H:%M:%S')
    elif not isinstance(date, datetime.datetime):
        date = datetime.datetime.combine(date, datetime.datetime.min.time())

    ret = int((date - datetime.datetime(1970, 1, 1)).total_seconds())
    return ret

def disable_logging(lvl = logging.DEBUG):
    """ Decorator

    """
    def actual_disable_logging(func):
        @functools.wraps(func)
        def wrapper(*args,**kwargs):
            logging.disable(lvl)
            result = func(*args,**kwargs)
            logging.disable(logging.NOTSET)
            return result
        return wrapper
    return actual_disable_logging


@disable_logging(logging.DEBUG)
def fixupCUI2(cui):
    """ Return a CUI or CNP or Serie/Nr CI in format fix, daca sirul de intrare
        corepunde:
        CUI: XXddddddd[d][d]
        CNP: ddddddddddddd
        Serie/Nr CI: XXdddddd
        @return: (Boolean, str): True daca sirul a putut fi fixuit plus sirul
                fixuit, false si sirul de intrare altfel

    """
    # Incearca CUI
    x = re.match("^\\s*([A-z]{2})?\\s*([0-9]{7,9})\\s*$", cui)
    if x:
        pref, no = x.groups()
        if no:
            pref = "RO" if pref is None else pref
            logger.debug("%s -> %s", cui, pref + no)

            return (True, pref + no)

    # Incearca CNP
    x = re.match("^\\s*([0-9]{13})\\s*$", cui)
    if x:
        no, = x.groups()
        if no:
            logger.debug("%s -> %s", cui, no)

            return (True, no)

    # Incearca Serie/Nr
    x = re.match("^\\s*([A-z]{2})?\\s*([0-9]{6})?\\s*$", cui)
    if x:
        serie, nr = x.groups()
        if nr:
            serie = "TM" if serie is None else serie
            logger.debug("%s -> %s", cui, serie + nr)

            return (True, serie + nr)

    return (False, cui)


@disable_logging(logging.DEBUG)
def fixupCUI(cui):
    """ Return a unique simbol that can identify the partener
        @return: (str): simbol that can identify the partener
    """

    ret = cui.replace(" ", "").lower()
    ret = ret.replace("ro", "")

    return ret


def log_json(myjson, indent=2):
    frames = traceback.extract_stack()
    frame = frames[-2]
    logger.info("{}:{}, {}()".format(frame.filename, frame.lineno, frame.name))

    logger.info(json.dumps(myjson, sort_keys=True, indent=indent, separators=(',', ': '), default=defaultJSON))
