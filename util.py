import datetime
import collections
from django.core.mail import EmailMessage
import logging
import re
import inspect
from ConfigParser import SafeConfigParser, NoOptionError, NoSectionError
import codecs
from django.template import loader, Context
import traceback
import json
from decimal import Decimal
import decorators


logger = logging.getLogger(__name__)


@decorators.time_log
def newException(e):
    try:
        # new Exception for today
        template = loader.get_template("mail/admin/exception.html")
        subject = "Exception at {}()".format(inspect.stack()[1][3])

        html_part = template.render({
            "subject": subject,
            "exception": e,
            "exceptionType": type(e),
            "traceback": traceback.format_exc()
        })
        send_email(subject, html_part)

    except BaseException as e:
        logger.exception("{0}, {1}".format(e, e.message))


def getNextDocumentNumber(type):
    import sys

    cfg = SafeConfigParser()
    cfg.optionxform = str
    try:
        import os.path
        documentNumberFolder = getCfgVal("gesto", "documentNumberFolder")

        cfg_filename = os.path.join(documentNumberFolder, 'config_documentNo_local.ini')
        with codecs.open(cfg_filename, 'r', encoding='utf-8') as f:
            cfg.readfp(f)
    except:
        logger.exception("Failed to read .ini file")
        sys.exit(1)

    docNo = cfg.getint("documentNumbers", type)
    cfg.set("documentNumbers", type, str(docNo+1))
    with open(cfg_filename, 'wb') as configfile:
        cfg.write(configfile)

    return docNo


def isArray(var):
    return isinstance(var, collections.Iterable) and (not isinstance(var, basestring))


def retToFileArray(ret, filename):
    ret = ret[0]
    retCnt = len(ret)

    thefile = open(filename+".txt", 'w')
    for ctr, r in enumerate(ret, start=1):
        thefile.write("{}/{} - {}\n".format(ctr, retCnt, r))


@decorators.time_log
def getCfgVal(section, varName, retType=None):
    cfg = SafeConfigParser()
    with codecs.open('config_local.ini', 'r', encoding='utf-8') as f:
        cfg.readfp(f)

    if retType == "int":
        ret = cfg.getint(section, varName)
    elif retType == "bool":
        ret = cfg.getboolean(section, varName)
    else:
        ret = cfg.get(section, varName)

    if section == "client" and varName in ['bccEmails', 'notificationEmails', ] \
    or section == "deliveryNote" and varName in ['sources', 'destinations'] \
    or section == "gesto" and varName in ['branches', 'branches_monetare'] \
    or section == "receptions" and varName in ['branches', ] \
    or section == "products" and varName in ['allowMissingDefaultGest', ]:
        ret = [x.strip() for x in ret.split(",")]

    logger.info("{}: {}".format(varName, ret))
    return ret


@decorators.time_log
def getCfgOptsDict(section):
    cfg = SafeConfigParser()
    cfg.optionxform = str

    with codecs.open('config_local.ini', 'r', encoding='utf-8') as f:
        cfg.readfp(f)

    ret={}
    for opt in cfg.options(section):
        ret[opt] = cfg.get(section, opt)

    log_json(ret)
    return ret


@decorators.time_log
def send_email(subject, msg, toEmails=None, bccEmails=None, location=True, isGestoProblem=False, replaceWithHTMLCodes=False):
    if not isGestoProblem:
        callersFrame = inspect.stack()[1][0]
    else:
        callersFrame = inspect.stack()[2][0]

    frameinfo = inspect.getframeinfo(callersFrame)

    msg = "\n" + msg
    if location:
        msg = "{}\n\n{}:{}".format(msg, frameinfo.filename, frameinfo.lineno)
    logger.info("msg: {}".format(msg))

    if replaceWithHTMLCodes or msg.find("<!-- replaceWithHTMLCodes -->") != -1:
        # msg = msg.replace("<", "&lt;")
        # msg = msg.replace(">", "&gt;")
        msg = msg.replace("    ", "&nbsp;&nbsp;&nbsp;&nbsp;")
        # this one goes last
        msg = msg.replace("\n", "<br/>")

    logger.info("msg: {}".format(msg))

    if toEmails is None or bccEmails is None:
        # create new list, if I ever append to it the value for settings.BCC_EMAILS will change and I will
        # send emails to people I don't want'
        bccEmailsCfg = getCfgVal("client", "bccEmails")

        if toEmails is None:
            toEmails = bccEmailsCfg
            logger.info("toEmails: {0}".format(toEmails))
        elif bccEmails is None:
            bccEmails = bccEmailsCfg
            logger.info("bccEmails: {0}".format(bccEmails))

    try:
        email = EmailMessage(subject, msg, to=toEmails, bcc=bccEmails)
        email.content_subtype = "html"

        if 1==1:
            email.send()
        else:
            logger.info(msg)

    except BaseException as e:
        logger.exception("{}, {}".format(e, e.message))


def getNumber(arg, decimal_places=4):
    if arg == '':
        ret = 0
    else:
        ret = float(arg.replace(",","."))
        if int(ret) == ret:
            # change to int if possible
            ret = int(ret)
        else:
            ret = Decimal(format(ret, '.{}f'.format(decimal_places)))

    return ret


def printArray(array):
    print("")
    for item in array:
        print(item)

    print("")


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


@decorators.disable_logging(logging.DEBUG)
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
    x = re.match("^\s*([A-z]{2})?\s*([0-9]{7,9})\s*$", cui)
    if x:
        pref, no = x.groups()
        if no:
            pref = "RO" if pref is None else pref
            logger.debug("%s -> %s", cui, pref + no)

            return (True, pref + no)

    # Incearca CNP
    x = re.match("^\s*([0-9]{13})\s*$", cui)
    if x:
        no, = x.groups()
        if no:
            logger.debug("%s -> %s", cui, no)

            return (True, no)

    # Incearca Serie/Nr
    x = re.match("^\s*([A-z]{2})?\s*([0-9]{6})?\s*$", cui)
    if x:
        serie, nr = x.groups()
        if nr:
            serie = "TM" if serie is None else serie
            logger.debug("%s -> %s", cui, serie + nr)

            return (True, serie + nr)

    return (False, cui)


@decorators.disable_logging(logging.DEBUG)
def fixupCUI(cui):
    """ Return a unique simbol that can identify the partener
        @return: (str): simbol that can identify the partener
    """

    ret = cui.replace(" ", "").lower()
    ret = ret.replace("ro", "")

    return ret


def log_json(myjson, indent=2):
    # logger.info(myjson)
    logger.info(json.dumps(myjson, sort_keys=True, indent=indent, separators=(',', ': '), default=defaultJSON))


@decorators.time_log
def getTokens():
    import requests

    baseURL = getCfgVal("gesto", "url")
    token = getCfgVal("winmentor", "companyToken")
    url = baseURL + "/poses/?active=1"

    logger.info(url)

    r = requests.get(url, headers={'GESTOTOKEN': token})

    if r.status_code != 200:
        logger.error("Gesto request failed: %d, %s", r.status_code, r.text)
        1 / 0
    else:
        retJSON = r.json()
        logger.debug("\n%s",
                    json.dumps(
                        retJSON,
                        sort_keys=True,
                        indent=4,
                        separators=(',', ': '),
                        default=defaultJSON
                        )
                    )

        tokens = dict([(pos["branch"]["name"], str(pos["serialNum"])) for pos in retJSON["data"]])

        return tokens
