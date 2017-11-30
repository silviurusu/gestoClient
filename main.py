import requests
import json
import os
import sys, getopt
import datetime
import util
# from myConfigParser import *
import settings
from winmentor import WinMentor
from datetime import datetime as dt, timedelta
from itertools import izip
import logging.config
from ConfigParser import SafeConfigParser, NoOptionError, NoSectionError
import codecs
from util import send_email
import re
import traceback
import inspect
from django.template import loader, Context
import django


def generateWorkOrders(baseURL, token, date):
    logger.info(">>> {}()".format(inspect.stack()[0][3]))
    start = dt.now()

    url = baseURL + "/products/summary/?"
    url += "type=workOrder"
    verify=True # only for workOrders
    if verify:
        url += "&verify=1"

    url += "&winMentor=1"
    url += "&excludeListVal=0"

    # add workOrders for the previous day
    dateEnd = date - timedelta(days = 1)
    dateBegin = dateEnd.replace(hour=0, minute=0, second=0)

    url += "&dateBegin={}".format(util.getTimestamp(dateBegin))
    url += "&dateEnd={}".format(util.getTimestamp(dateEnd))

    logger.debug(url)
    logger.debug("dateBegin: {}".format(dateBegin.strftime("%Y-%m-%d %H:%M:%S")))
    logger.debug("dateEnd: {}".format(dateEnd.strftime("%Y-%m-%d %H:%M:%S")))

    retJSON = None
    r = requests.get(url, headers={'GESTOTOKEN': token})

    if r.status_code != 200:
        logger.error("Gesto request failed: %d, %s", r.status_code, r.text)
        logger.error("Gesto request url: {}", url)
        logger.error("Gesto request token: {}", token)
        1/0
    else:
        retJSON = r.json()

        if retJSON["verify"] == "success":
            # email is sent from Gesto if there is any problem
            winmentor.addWorkOrders(retJSON)

    logger.info("<<< {}() - duration = {}".format(inspect.stack()[0][3], dt.now() - start))


def generateMonetare(baseURL, token, date):
    logger.info(">>> {}()".format(inspect.stack()[0][3]))
    start = dt.now()

    url = baseURL + "/products/summary/?"
    url += "type=sale"

    verify=False # only for workOrders
    if verify:
        url += "&verify=1"

    url += "&winMentor=1"
    url += "&excludeOpVal=0"

    # add monetare for the previous day
    dateEnd = date - timedelta(days = 1)
    dateBegin = dateEnd.replace(hour=0, minute=0, second=0)

    url += "&dateBegin={}".format(util.getTimestamp(dateBegin))
    url += "&dateEnd={}".format(util.getTimestamp(dateEnd))

    logger.debug(url)
    logger.debug("dateBegin: {}".format(dateBegin.strftime("%Y-%m-%d %H:%M:%S")))
    logger.debug("dateEnd: {}".format(dateEnd.strftime("%Y-%m-%d %H:%M:%S")))

    retJSON = None
    r = requests.get(url, headers={'GESTOTOKEN': token})

    if r.status_code != 200:
        logger.error("Gesto request failed: %d, %s", r.status_code, r.text)
        logger.error("Gesto request url: {}", url)
        logger.error("Gesto request token: {}", token)
        1/0
    else:
        retJSON = r.json()

        # logger.debug(retJSON)
        if not verify or retJSON["verify"] == "success":
            pass

            # email is sent from Gesto if there is any problem
            winmentor.addMonetare(retJSON)

    logger.info("<<< {}() - duration = {}".format(inspect.stack()[0][3], dt.now() - start))


def importAvize(baseURL, date):
    logger.info(">>> {}()".format(inspect.stack()[0][3]))
    start = dt.now()

    deliveryNotes = winmentor.getTransferuri(date)

    opStr = {
        "version": "1.0",
        "type": "reception",
        "company": cfg.get("winmentor", "companyName"),
    }

    hour = int(cfg.get("deliveryNote", "hour"))

    for (source, val1) in deliveryNotes.items():
        opStr["source"] = {
                            "name": winmentor.getGestiuneName(source),
                            "type": "company",
                            "winMentorcode": source,
                        }

        for (date, val2) in val1.items():
            date = [int(x) for x in date.split(".")]
            date = datetime.datetime(date[2], date[1], date[0])
            # logger.info(date)
            # logger.info(type(date))

            operationDate = datetime.datetime.now()
            opStr["operationDate"] = util.getTimestamp(operationDate)
            opStr["operationDateHuman"] = operationDate.strftime("%d/%m/%Y %H:%M:%S")

            if operationDate.day == date.day \
            and operationDate.month == date.month \
            and operationDate.year == date.year:
                documentDate = operationDate
            else:
                documentDate = date.replace(hour=hour)

            opStr["documentDate"] = util.getTimestamp(documentDate)
            opStr["documentDateHuman"] = documentDate.strftime("%d/%m/%Y %H:%M:%S")

            for (destination, val3) in val2.items():
                opStr["destination"] = {
                            "name": winmentor.getGestiuneName(destination),
                            "type": "warehouse",
                            "winMentorcode": destination,
                        }

                for (documentNo, val4) in val3.items():
                    opStr["relatedDocumentNo"] = documentNo

                    opStr["items"] = []

                    for item in val4:
                        opStr["items"].append(item)
                    logger.info(
                        json.dumps(
                            opStr,
                            sort_keys=True,
                            indent=4,
                            separators=(',', ': '),
                            default=util.defaultJSON
                            )
                        )

                    opStr.pop('documentNo', None)
                    opStr.pop('items', None)
                opStr.pop('destination', None)
            opStr.pop('date', None)
        opStr.pop('source', None)

    logger.info("<<< {}() - duration = {}".format(inspect.stack()[0][3], dt.now() - start))


def getGestoDocuments(baseURL, token, operationType, excludeCUI=None, endDate = None, daysDelta = 7):
    """
    @param token: Gesto token used for request
    @tparam [datetime] startDate: first day of request, defaults to today
    @tparam [numeric] daysDelta: request for how many days, defaults to 7
    @return processed json if successfull, None otherwise

    """
    logger.info(">>> {}()".format(inspect.stack()[0][3]))
    start = dt.now()

    logger.info("Getting receptie from Gesto.")
    if endDate is None:
        endDate = dt.today()
        endDate = endDate.replace(hour=23, minute=59, second=59)

    startDate = (endDate - timedelta(days = daysDelta)).replace(hour=0, minute=0, second=0)
    if token == "2043451": # "34 Fabricii"
        startDate = max([startDate, datetime.datetime(2017, 11, 21)])

    logger.debug("startDate: {}".format(startDate))
    logger.debug("endDate: {}".format(endDate))

    url = baseURL + "/operations?"
    url += "&type="+operationType
    if startDate is not None:
        startDate = util.getTimestamp(startDate)
        url += "&dateBegin="+str(startDate)
    if endDate is not None:
        endDate = util.getTimestamp(endDate)
        url += "&dateEnd="+str(endDate)

    if excludeCUI is not None:
        url += "&excludeCUI="+str(excludeCUI)

    url += "&winMentor="+str(1)

    urlCount = url + "&pageSize="+str(1)
    urlCount += "&page="+str(1)
    logger.debug(url)
    logger.debug("startDate: {}".format(dt.utcfromtimestamp(startDate)))
    logger.debug("endDate: {}".format(dt.utcfromtimestamp(endDate)))

    retJSON = None
    r = requests.get(urlCount, headers={'GESTOTOKEN': token})

    if r.status_code != 200:
        logger.error("Gesto request failed: %d, %s", r.status_code, r.text)
    else:
        retJSON = r.json()
        # logger.debug("\n%s",
        #         json.dumps(
        #             retJSON,
        #             sort_keys=True,
        #             indent=4,
        #             separators=(',', ': '),
        #             default=util.defaultJSON
        #             )
        #         )

        if retJSON["data"][0]["simbolWinMentorReception"] in [None, "nil",]:
            txtMail = "Locatia {} nu are setat un simbol pentru WinMentor".format(retJSON["data"][0]["destination"]["name"])

            send_email(
                    subject = txtMail,
                    msg = txtMail
                    )

            logger.info("<<< {}() - duration = {}".format(inspect.stack()[0][3], dt.now() - start))
            return

        totalRecords = retJSON["range"]["totalRecords"]
        logger.info("{} {}".format(totalRecords, operationType))

        pageSize = 10
        pagesCount = int((totalRecords + pageSize - 1) / pageSize)
        print "pagesCount: {}".format(pagesCount)

        for ctr in range(1, pagesCount + 1):
            urlPage = url + "&pageSize="+str(pageSize)
            urlPage += "&page="+str(ctr)
            logger.debug("{}, {}, {}".format(ctr, pagesCount, urlPage))

            r = requests.get(urlPage, headers={'GESTOTOKEN': token})
            retJSON = r.json()
            # logger.debug("\n%s",
            #         json.dumps(
            #             retJSON,
            #             sort_keys=True,
            #             indent=4,
            #             separators=(',', ': '),
            #             default=util.defaultJSON
            #             )
            #         )

            tot = len(retJSON["data"])
            for ctr2, op in enumerate(retJSON["data"], start=1):
                logger.debug("{}, {}, {}".format(ctr2, tot, op["id"]))

                # gestoData = retJSON["data"]
                # if util.isArray(gestoData) and len(gestoData) >= 1:
                if operationType == "reception":
                    # Get partener from gesto
                    gestoPartener = util.fixupCUI(op["source"]["code"])
                    logger.info("gestoPartener = {}".format(gestoPartener))
                    winmentor.addReception(op)

                    # if winmentor.getPanemarCUI() != gestoPartener:
                    #     # not from Panemar
                    #     winmentor.addReception(op)
                    # else:
                    #     logger.info("Reception from Panemar, don't import")

                # if ctr2==2:
                #     1/0

    logger.info("<<< {}() - duration = {}".format(inspect.stack()[0][3], dt.now() - start))


def cleanId(name):
    """ Remove spaces and convert a id/name to smallcase, to avoid
    user insert format problems. Example: "31 Vlaicu", "31Vlaicu" all
    convert to "31vlaicu"

    """
    return "".join(name.lower().split())


def setup_logging(
        default_path='logging.json',
        default_level=logging.INFO,
        env_key='LOG_CFG'
        ):
    """ Setup logging configuration

    """
    path = default_path
    value = os.getenv(env_key, None)
    if value:
        path = value
    if os.path.exists(path):
        with open(path, 'rt') as f:
            config = json.load(f)

            # Search for hadlers with "folder" and set the
            # .. log file with current date in that folder
            for _, dhandler in config["handlers"].items():
                folder = dhandler.pop("folder", None)
                if folder:
                    path = os.path.join(
                            folder,
                            dt.strftime(dt.now(), "%Y_%m_%d__%H_%M.log")
                            )
                    if not os.path.exists(folder):
                        os.mkdir(folder)
                    dhandler["filename"] = path

        logging.config.dictConfig(config)
    else:
        logging.basicConfig(level=default_level)


if __name__ == "__main__":
    try:

        # Set DJANGO for email support
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")
        django.setup()

        # Get logger
        setup_logging()
        logger = logging.getLogger(name = __name__)

        # Get Script settings
        cfg = SafeConfigParser()
        cfg.optionxform = str
        with codecs.open('config_local.ini', 'r', encoding='utf-8') as f:
            cfg.readfp(f)

        logger.info(">>> {}()".format(inspect.stack()[0][3]))
        start = dt.now()

        # Connect to winmentor
        winmentor = WinMentor(firma = cfg.get("winmentor", "firma"), an=start.year, luna=start.month)
        if not winmentor:
            logger.error("Failed to get winmentor object")
            1/0

        winmentor.setPanemarCUI(cfg.get("winmentor", "cui"))

        # # TODO here for testing
        # intrari, rc = winmentor._stat.GetIntrari()
        # result = []
        # keys = (
        #        "partenerId",
        #        "data",
        #        "nrDoc",
        #        "idArticol",
        #        "cant", # cantitate
        #        "um",
        #        "pret",
        #        "simbGest",
        #        "_"
        #        )
        # if (rc == 0) and util.isArray(intrari):
        #     for intrare in intrari:
        #         val = winmentor._colonListToDict(keys, intrare)
        #         print(repr(val))

        # sys.exit(0)
        # # TODO -- END TESTING --

        logger.info("START")

        tokens = [x.strip() for x in cfg.get("gesto", "tokens").split(",")]

        # Get date to use for Unit Test
        try:
            utDate = dt.strptime(cfg.get("_UT_", "workdate"), "%Y-%m-%d")
        except NoOptionError as e:
            utDate = dt.today()

        logger.info("Using utDate: {}".format(utDate))

        # end of day
        endDate = utDate.replace(hour=23, minute=59, second=59)
        logger.info("Using end date: {}".format(endDate))

        doExportReceptions = cfg.getboolean("gesto", "exportReceptions")
        doGenerateWorkOrders = cfg.getboolean("gesto", "generateWorkOrders")
        doGenerateMonetare = cfg.getboolean("gesto", "generateMonetare")
        doImportAvize = cfg.getboolean("gesto", "importAvize")

        try:
            opts, args = getopt.getopt(sys.argv[1:],"h",["exportReceptions=",
                                     "generateWorkOrders=",
                                     "generateMonetare=",
                                     "importAvize="
                                    ])

            logger.info(opts)
            logger.info(args)

        except getopt.GetoptError:
            print '{} --exportReceptions=<> --generateWorkOrders=<> --generateMonetare=<> --importAvize=<>'.format(sys.argv[0])
            sys.exit(2)
        for opt, arg in opts:
            if opt == '-h':
                print '{} --exportReceptions=<> --generateWorkOrders=<> --generateMonetare=<> --importAvize=<>'.format(sys.argv[0])
                sys.exit()
            elif opt in ("--exportReceptions"):
                doExportReceptions = bool(int(arg))
            elif opt in ("--generateWorkOrders"):
                doGenerateWorkOrders = bool(int(arg))
            elif opt in ("--generateMonetare"):
                doGenerateMonetare = bool(int(arg))
            elif opt in ("--importAvize"):
                doImportAvize = bool(int(arg))

        logger.info( 'exportReceptions {}'.format(doExportReceptions))
        logger.info( 'generateWorkOrders {}'.format(doGenerateWorkOrders))
        logger.info( 'generateMonetare {}'.format(doGenerateMonetare))
        logger.info( 'importAvize {}'.format(doImportAvize))

        if doExportReceptions:
            for token in tokens:
                logger.info("Using Gesto token: {}".format(token))

                gestoData = getGestoDocuments(
                        baseURL = cfg.get("gesto", "url"),
                        token = token,
                        operationType="reception",
                        excludeCUI=cfg.get("winmentor", "cui"),
                        endDate = endDate,
                        daysDelta = cfg.getint("gesto", "daysDelta"),
                        )

        if doGenerateMonetare:
            for token in tokens:
                logger.info("Using Gesto token: {}".format(token))
                gestoData = generateMonetare(
                        baseURL = cfg.get("gesto", "url"),
                        token = token,
                        date = endDate,
                        )

        if doGenerateWorkOrders:
            for token in tokens:
                logger.info("Using Gesto token: {}".format(token))
                gestoData = generateWorkOrders(
                        baseURL = cfg.get("gesto", "url"),
                        token = token,
                        date = endDate,
                        )

        if doImportAvize:
            gestoData = importAvize(
                    baseURL = cfg.get("gesto", "url"),
                    date = endDate,
                    )

        # Send mail with new products and partners
        winmentor.sendNewProductsMail()
        winmentor.sendPartnersMail()
        winmentor.sendIncorrectWinMentorProductsMail()

    except Exception as e:
        print repr(e)
        logger.exception(repr(e))
        util.newException(e)

    logger.info("END")
    logger.info("<<< {}() - duration = {}".format(inspect.stack()[0][3], dt.now() - start))
