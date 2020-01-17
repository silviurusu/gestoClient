import requests
import json
import os
import sys, getopt
import datetime
import util
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


def generateWorkOrders(baseURL, branch, date, doVerify):
    # ajung in mentor in NT_G
    logger.info(">>> {}()".format(inspect.stack()[0][3]))
    start = dt.now()

    url = baseURL + "/products/summary/?"
    companyName = util.getCfgVal("winmentor", "companyName")
    if companyName == "Panemar morarit si panificatie SRL":
        url += "type=workOrder"
    else:
        if branch != "Sediu":
            logger.info("Only generate transfers for Sediu, not for {}".format(branch))
            logger.info("<<< {}() - duration = {}".format(inspect.stack()[0][3], dt.now() - start))
            return True

        url += "type=sale"
        url += "&excludeCodes=1,2"

    if branch == "29 Memo":
        doVerify = False

    if doVerify:
        url += "&verify=1"
    url += "&winMentor=1"
    url += "&excludeListVal=0"
    url += "&showInactivePoses=0"

    # add workOrders for the previous day
    dateEnd = date - timedelta(days = 1)
    dateBegin = dateEnd.replace(hour=0, minute=0, second=0)

    url += "&dateBegin={}".format(util.getTimestamp(dateBegin))
    url += "&dateEnd={}".format(util.getTimestamp(dateEnd))

    logger.debug(url)
    logger.debug("dateBegin: {}".format(dateBegin.strftime("%Y-%m-%d %H:%M:%S")))
    logger.debug("dateEnd: {}".format(dateEnd.strftime("%Y-%m-%d %H:%M:%S")))

    retJSON = None
    token = tokens[branch]
    logger.error("Gesto request token: {}".format(token))

    r = requests.get(url, headers={'GESTOTOKEN': token})

    if r.status_code != 200:
        logger.error("Gesto request failed: %d, %s", r.status_code, r.text)
        logger.error("Gesto request url: {}".format(url))
        1/0
    else:
        retJSON = r.json()

        logger.info("verify: {}".format(retJSON["verify"]))

        if not doVerify or retJSON["verify"] == "success":
            # email is sent from Gesto if there is any problem
            winmentor.addWorkOrders(retJSON)
            ret = True
        elif retJSON["verify"] == "No Vectron data":
            ret = True
        else:
            ret = False

    logger.info("<<< {}() - duration = {}".format(inspect.stack()[0][3], dt.now() - start))
    return ret

# NP_G
# productie - exectie - intrari din productie
def generateIntrariDinProductie(baseURL, branch, date, doVerify):
    logger.info(">>> {}()".format(inspect.stack()[0][3]))
    start = dt.now()

    url = baseURL + "/products/summary/?"
    url += "type=workOrder"

    if branch == "29 Memo":
        doVerify = False

    if doVerify:
        url += "&verify=1"

    url += "&winMentor=1"
    url += "&excludeListVal=0"
    url += "&showInactivePoses=0"

    # add workOrders for the previous day
    dateEnd = date - timedelta(days = 1)
    dateBegin = dateEnd.replace(hour=0, minute=0, second=0)

    url += "&dateBegin={}".format(util.getTimestamp(dateBegin))
    url += "&dateEnd={}".format(util.getTimestamp(dateEnd))

    logger.debug(url)
    logger.debug("dateBegin: {}".format(dateBegin.strftime("%Y-%m-%d %H:%M:%S")))
    logger.debug("dateEnd: {}".format(dateEnd.strftime("%Y-%m-%d %H:%M:%S")))

    retJSON = None
    token = tokens[branch]
    logger.error("Gesto request token: {}".format(token))

    r = requests.get(url, headers={'GESTOTOKEN': token})

    if r.status_code != 200:
        logger.error("Gesto request failed: %d, %s", r.status_code, r.text)
        logger.error("Gesto request url: {}".format(url))
        1/0
    else:
        retJSON = r.json()

        logger.info("verify: {}".format(retJSON["verify"]))
        if not doVerify or retJSON["verify"] == "success":
            # email is sent from Gesto if there is any problem
            winmentor.addIntrariDinProductie(retJSON)
            ret = True
        elif retJSON["verify"] == "No Vectron data":
            ret = True
        else:
            ret = False

    logger.info("<<< {}() - duration = {}".format(inspect.stack()[0][3], dt.now() - start))
    return ret

# bonuri de consum
# BC_G
def exportSummaryTransfers(baseURL, branch, date):
    logger.info(">>> {}()".format(inspect.stack()[0][3]))
    start = dt.now()

    url = baseURL + "/products/summary/?"
    url += "type=transfer"
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
    token = tokens[branch]
    logger.error("Gesto request token: {}".format(token))

    r = requests.get(url, headers={'GESTOTOKEN': token})

    if r.status_code != 200:
        logger.error("Gesto request failed: %d, %s", r.status_code, r.text)
        logger.error("Gesto request url: {}".format(url))
        1/0
    else:
        retJSON = r.json()
        winmentor.addProductSummary(retJSON, dateEnd)

    logger.info("<<< {}() - duration = {}".format(inspect.stack()[0][3], dt.now() - start))


def exportSummaryBonDeConsum(baseURL, branch, date):
    logger.info(">>> {}()".format(inspect.stack()[0][3]))
    start = dt.now()

    url = baseURL + "/products/summary/?"
    url += "type=bon_de_consum"
    url += "&winMentor=1"
    url += "&codes_gte=5000"
    url += "&codes_lte=6000"

    # add BonDeConsum for the previous month
    dateEnd = (date.replace(day=1) - datetime.timedelta(days=1)).replace(hour=23, minute=59, second=59)
    dateBegin = dateEnd.replace(day=1, hour=0, minute=0, second=0)

    url += "&dateBegin={}".format(util.getTimestamp(dateBegin))
    url += "&dateEnd={}".format(util.getTimestamp(dateEnd))

    logger.debug(url)
    logger.debug("dateBegin: {}".format(dateBegin.strftime("%Y-%m-%d %H:%M:%S")))
    logger.debug("dateEnd: {}".format(dateEnd.strftime("%Y-%m-%d %H:%M:%S")))

    retJSON = None
    token = tokens[branch]
    logger.error("Gesto request token: {}".format(token))

    r = requests.get(url, headers={'GESTOTOKEN': token})

    if r.status_code != 200:
        logger.error("Gesto request failed: %d, %s", r.status_code, r.text)
        logger.error("Gesto request url: {}".format(url))
        1/0
    else:
        retJSON = r.json()
        winmentor.addProductSummary(retJSON, dateEnd, monthly=True)

    logger.info("<<< {}() - duration = {}".format(inspect.stack()[0][3], dt.now() - start))


def generateMonetare(baseURL, branch, date):
    logger.info(">>> {}()".format(inspect.stack()[0][3]))
    start = dt.now()

    logger.info("Generate monetare for {}, {}".format(branch, tokens[branch]))

    url = baseURL + "/products/summary/?"
    url += "type=sale"
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
    token = tokens[branch]
    logger.error("Gesto request token: {}".format(token))

    r = requests.get(url, headers={'GESTOTOKEN': token})

    if r.status_code != 200:
        logger.error("Gesto request failed: %d, %s", r.status_code, r.text)
        logger.error("Gesto request url: {}".format(url))
        1/0
    else:
        retJSON = r.json()
        winmentor.addMonetare(retJSON)

    logger.info("<<< {}() - duration = {}".format(inspect.stack()[0][3], dt.now() - start))


def getExportedDeliveryNotes(baseURL, startDate, endDate):
    logger.info(">>> {}()".format(inspect.stack()[0][3]))
    start = dt.now()

    operationType = "reception"
    url = baseURL + "/operations/?"
    url += "&type=" + operationType

    url += "&dateBegin={}".format(util.getTimestamp(startDate))
    url += "&dateEnd={}".format(util.getTimestamp(endDate))
    url += "&onlyRelatedDocumentNo=1"

    retJSON = None
    token = "gG9PGmXQaF"
    logger.error("Gesto request token: {}".format(token))

    r = requests.get(url, headers={'GESTOTOKEN': token})

    logger.info(url)

    ret = []

    if r.status_code != 200:
        logger.error("Gesto request failed: %d, %s", r.status_code, r.text)
    else:
        retJSON = r.json()
        logger.debug("\n%s",
                json.dumps(
                    retJSON,
                    sort_keys=True,
                    indent=4,
                    separators=(',', ': '),
                    default=util.defaultJSON
                    )
                )

        totalRecords = retJSON["range"]["totalRecords"]
        logger.info("{} {}".format(totalRecords, operationType))

        if totalRecords != 0:
            pageSize = 100
            pagesCount = int((totalRecords + pageSize - 1) / pageSize)

            for ctr in range(1, pagesCount + 1):
                urlPage = url + "&pageSize="+str(pageSize)
                urlPage += "&page="+str(ctr)
                logger.debug("{}, {}, {}".format(ctr, pagesCount, urlPage))

                r = requests.get(urlPage, headers={'GESTOTOKEN': token})
                retJSON = r.json()

                tot = len(retJSON["data"])
                for ctr2, op in enumerate(retJSON["data"], start=1):
                    logger.debug("{}, {}, {}".format(ctr2, tot, op["id"]))
                    ret.append(op["relatedDocumentNo"])

    logger.info(ret)

    logger.info("<<< {}() - duration = {}".format(inspect.stack()[0][3], dt.now() - start))
    return ret


def importAvize(baseURL, date):
    logger.info(">>> {}()".format(inspect.stack()[0][3]))
    start = dt.now()

    deliveryNotes = winmentor.getTransferuri(date)

    opStr = {
        "version": "1.0",
        "type": "reception",
        "company": util.getCfgVal("winmentor", "companyName"),
    }

    hour = util.getCfgVal("deliveryNote", "hour", "int")

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

                    opStrText = json.dumps(
                        opStr,
                        sort_keys=True,
                        indent=4,
                        separators=(',', ': '),
                        default=util.defaultJSON
                        )
                    logger.info(opStrText)
                    opStrText = json.dumps(
                        opStr,
                        default=util.defaultJSON
                        )

                    r = requests.post(baseURL+"/importOperation/", data = opStrText)
                    if r.status_code != 200:
                        logger.error("Gesto request failed: %d, %s", r.status_code, r.text)
                        1/0

                    # 1/0
                    opStr.pop('documentNo', None)
                    opStr.pop('items', None)
                opStr.pop('destination', None)
            opStr.pop('date', None)
        opStr.pop('source', None)

    logger.info("<<< {}() - duration = {}".format(inspect.stack()[0][3], dt.now() - start))


# "return": "NTR_G"
# "reception": "NTA_G"
def getGestoDocuments(baseURL, branch, operationType, excludeCUI=None, endDate = None, daysDelta = 7):
    """
    @param branch: Gesto branch used for request
    @tparam [datetime] startDate: first day of request, defaults to today
    @tparam [numeric] daysDelta: request for how many days, defaults to 7
    @return processed json if successfull, None otherwise

    """
    logger.info(">>> {}()".format(inspect.stack()[0][3]))
    start = dt.now()

    # opDate = datetime.datetime.strptime("2018-06-01", "%Y-%m-%d")
    # winmentor.transferExists(10, opDate)
    # 1/0
    # endDate = min(endDate, datetime.datetime.strptime("2018-04-30 23:59:59", "%Y-%m-%d %H:%M:%S"))
    endDate = None

    logger.info("Getting {} from Gesto for {}, {}".format(operationType, branch, tokens[branch]))
    if endDate is None:
        endDate = dt.today()
        endDate = endDate.replace(hour=23, minute=59, second=59)

    if operationType == "reception":
        # start of previousMonth
        startDate = dt.today().replace(day=1, hour=0, minute=0, second=0)
        startDate = startDate - timedelta(days=1)
        startDate = startDate.replace(day=1, hour=0, minute=0, second=0)
        # startDate = datetime.datetime.strptime("2019-11-08", "%Y-%m-%d")
    elif operationType == "supplyOrder":
        startDate = dt.today().replace(hour=0, minute=0, second=0)
        # startDate = startDate - timedelta(days = 1)
        endDate = startDate + timedelta(days = daysDelta)
    elif operationType == "return":
        # start of previousMonth
        startDate = dt.today().replace(day=1, hour=0, minute=0, second=0)
        startDate = startDate - timedelta(days=1)
        startDate = startDate.replace(day=1, hour=0, minute=0, second=0)
        # startDate = datetime.datetime.strptime("2019-11-08", "%Y-%m-%d")
    elif operationType == "sale":
        # startDate = dt.today().replace(day=1, hour=0, minute=0, second=0)
        # startDate = startDate - timedelta(days=1)
        # startDate = endDate.replace(day=1, hour=0, minute=0, second=0)
        endDate = endDate.replace(day=1) - datetime.timedelta(days=1)
        endDate = endDate.replace(hour=23, minute=59, second=59)
        startDate = endDate.replace(day=1, hour=0, minute=0, second=0)
    else :
        startDate = (endDate - timedelta(days = daysDelta)).replace(hour=0, minute=0, second=0)
    try:
        branchStartDate = dt.strptime(util.getCfgVal("receptionsStartDate", branch), "%Y-%m-%d")
    except NoOptionError:
        branchStartDate = startDate

    logger.debug("startDate: {}".format(startDate))
    logger.debug("branchStartDate: {}".format(branchStartDate))
    startDate = max([startDate, branchStartDate])

    logger.debug("startDate: {}".format(startDate))
    logger.debug("endDate: {}".format(endDate))

    onlyKeepStockProducts = False
    id = None
    # id = 46405157
    # if operationType == "reception":
    #     id = 49095512
    #     onlyKeepStockProducts = True
    # if operationType == "return":
    #     id = 46966370

    if id is not None:
        url = baseURL + "/operations/{}/?".format(id)
    else:
        url = baseURL + "/operations/?"
        url += "&type="+operationType

        if startDate is not None:
            startDate = util.getTimestamp(startDate)
            url += "&dateBegin="+str(startDate)
        if endDate is not None:
            endDate = util.getTimestamp(endDate)
            url += "&dateEnd="+str(endDate)

        logger.debug("startDate: {}".format(dt.utcfromtimestamp(startDate)))
        logger.debug("endDate: {}".format(dt.utcfromtimestamp(endDate)))

    if excludeCUI is not None:
        url += "&excludeCUI="+str(excludeCUI)

    if onlyKeepStockProducts:
        url += "&onlyKeepStockProducts=1"

    url += "&winMentor=1"

    if operationType == "sale":
        url += "&showInvoicedSales=1"

    urlCount = url + "&pageSize=1"
    urlCount += "&page=1"
    logger.debug(url)

    retJSON = None
    token = tokens[branch]
    logger.error("Gesto request token: {}".format(token))

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

        totalRecords = retJSON["range"]["totalRecords"]
        if totalRecords == 0:
            logger.info("{} {}".format(totalRecords, operationType))
            logger.info("<<< {}() - duration = {}".format(inspect.stack()[0][3], dt.now() - start))
            return

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

        pageSize = 100
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
                if op["type"] == "reception":
                    # Get partener from gesto
                    gestoPartener = util.fixupCUI(op["source"]["code"])
                    logger.info("gestoPartener = {}".format(gestoPartener))

                    # op["items"] = op["items"]
                    if int(gestoPartener) > 1500 \
                    or int(gestoPartener) < 0:
                        winmentor.addReception(op)
                    else:
                        deliveryNoteReceptionsDate = datetime.datetime.strptime("2018-06-01", "%Y-%m-%d")
                        opDate = dt.utcfromtimestamp(op["documentDate"])
                        logger.info("deliveryNoteReceptionsDate = {}".format(deliveryNoteReceptionsDate))
                        logger.info("opDate = {}".format(opDate))

                        if opDate > deliveryNoteReceptionsDate:
                            winmentor.addWorkOrderFromOperation(op)
                            # 1/0

                    # 1/0

                elif op["type"] == "supplyOrder":
                    winmentor.addSupplyOrder(op)
                elif op["type"] == "sale":
                    winmentor.addSale(op)
                elif op["type"] == "return":
                    winmentor.addWorkOrderFromOperation(op)

                # if ctr2==1:
                #     1/0

    logger.info("<<< {}() - duration = {}".format(inspect.stack()[0][3], dt.now() - start))


def getGestoDocumentsMarkedForWinMentorExport(baseURL, branch):
    """
    @param branch: Gesto branch used for request
    """
    logger.info(">>> {}()".format(inspect.stack()[0][3]))
    start = dt.now()

    logger.info("Getting all operations marked for WinMentorExport")
    url = baseURL + "/operations/?"
    url += "&markedForWinMentorExport=1"
    url += "&onlyKeepStockProducts=1"
    logger.debug(url)

    token = tokens[branch]
    logger.error("Gesto request token: {}".format(token))

    r = requests.get(url, headers={'GESTOTOKEN': token})

    if r.status_code != 200:
        logger.error("Gesto request failed: %d, %s", r.status_code, r.text)
    else:
        retJSON = r.json()
        logger.debug("\n%s",
                json.dumps(
                    retJSON,
                    sort_keys=True,
                    indent=4,
                    separators=(',', ': '),
                    default=util.defaultJSON
                    )
                )

        totalRecords = retJSON["range"]["totalRecords"]
        logger.info("{} operations".format(totalRecords))
        if totalRecords == 0:
            logger.info("<<< {}() - duration = {}".format(inspect.stack()[0][3], dt.now() - start))
            return

        if retJSON["data"][0]["simbolWinMentorReception"] in [None, "nil",]:
            txtMail = "Locatia {} nu are setat un simbol pentru WinMentor".format(retJSON["data"][0]["destination"]["name"])

            send_email(
                    subject = txtMail,
                    msg = txtMail
                    )

            logger.info("<<< {}() - duration = {}".format(inspect.stack()[0][3], dt.now() - start))
            return

        totalRecords = retJSON["range"]["totalRecords"]
        logger.info("{} operations".format(totalRecords))

        currentMonth = None
        currentYear = None

        for ctr, op in enumerate(retJSON["data"], start=1):
            logger.debug("{}, {}, {}".format(ctr, totalRecords, op["id"]))

            opDate = dt.utcfromtimestamp(op["documentDate"])
            if opDate.month != currentMonth and opDate.year != currentYear:
                winmentor.setLunaLucru(opDate.month, opDate.year)
                currentMonth = opDate.month
                currentYear = opDate.year

            gestoData = retJSON["data"]
            if op["type"]== "reception":
                # Get partener from gesto
                gestoPartener = util.fixupCUI(op["source"]["code"])
                logger.info("gestoPartener = {}".format(gestoPartener))

                # op["items"] = op["items"]
                if int(gestoPartener) > 1500 \
                or int(gestoPartener) < 0:
                    winmentor.addReception(op)
                else:
                    deliveryNoteReceptionsDate = datetime.datetime.strptime("2018-06-01", "%Y-%m-%d")
                    opDate = dt.utcfromtimestamp(op["documentDate"])
                    logger.info("deliveryNoteReceptionsDate = {}".format(deliveryNoteReceptionsDate))
                    logger.info("opDate = {}".format(opDate))

                    if opDate > deliveryNoteReceptionsDate:
                        winmentor.addWorkOrderFromOperation(op)
                        # 1/0

                # 1/0

            elif op["type"] == "supplyOrder":
                winmentor.addSupplyOrder(op)
            elif op["type"] == "sale":
                winmentor.addSale(op)
            elif op["type"] == "return":
                winmentor.addWorkOrderFromOperation(op)

            url = baseURL + "/operations/{}/exportedWinMentor/".format(op["id"])
            r = requests.put(url, headers={'GESTOTOKEN': token})
            logger.info(r)

            # if ctr==1:
            #     1/0

    logger.info("<<< {}() - duration = {}".format(inspect.stack()[0][3], dt.now() - start))


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

        # logger.info("SILVIU")
        # exit()

        logger.info(">>> {}()".format(inspect.stack()[0][3]))
        start = dt.now()

        # with open('d:\\gestoClientWME\\debug\\silviu.log', 'wb') as f:
        #     f.write(start.strftime("%Y-%m-%d %H:%M:%S"))

        # 1/0

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

        branches = util.getCfgVal("gesto", "branches")
        branches_monetare = util.getCfgVal("gesto", "branches_monetare")

        branches_default = True

        # Get date to use for Unit Test
        try:
            workdate = dt.strptime(util.getCfgVal("_UT_", "workdate"), "%Y-%m-%d")
        except NoOptionError as e:
            workdate = dt.today()

        doExportReceptions = util.getCfgVal("gesto", "exportReceptions", "bool")
        doExportSales = util.getCfgVal("gesto", "exportSales", "bool")
        doExportReturns = util.getCfgVal("gesto", "exportReturns", "bool")
        doExportSupplyOrders = util.getCfgVal("gesto", "exportSupplyOrders", "bool")
        doGenerateWorkOrders = util.getCfgVal("gesto", "generateWorkOrders", "bool")
        doGenerateIntrariDinProductie = util.getCfgVal("gesto", "generateIntrariDinProductie", "bool")
        doGenerateMonetare = util.getCfgVal("gesto", "generateMonetare", "bool")
        doImportAvize = util.getCfgVal("gesto", "importAvize", "bool")
        doExportSummaryTransfers = util.getCfgVal("gesto", "exportSummaryTransfers", "bool")
        doExportSummaryBonDeConsum = util.getCfgVal("gesto", "exportSummaryBonDeConsum", "bool")
        doVerify = util.getCfgVal("gesto", "verify", "bool")
        markedForWinMentorExport = False

        try:
            # logger.info(sys.argv)
            opts, args = getopt.getopt(sys.argv[1:],"h",["exportReceptions=",
                                     "exportSales=",
                                     "exportReturns=",
                                     "exportSupplyOrders=",
                                     "generateWorkOrders=",
                                     "generateIntrariDinProductie=",
                                     "generateMonetare=",
                                     "importAvize=",
                                     "exportSummaryTransfers=",
                                     "exportSummaryBonDeConsum=",
                                     "branches=",
                                     "verify=",
                                     "workDate=",
                                     "markedForWinMentorExport=",
                                    ])

            logger.info(opts)
            logger.info(args)

        except getopt.GetoptError:
            print '{} --exportReceptions=<> --generateWorkOrders=<> --generateIntrariDinProductie=<> --generateMonetare=<> --importAvize=<> --exportSummaryTransfers=<> --exportSummaryBonDeConsum=<> --exportSales=<> --exportReturns=<> --exportSupplyOrders=<> --branches=<> --verify=<> --markedForWinMentorExport=<> --workDate=<YYYY-MM-DD>'.format(sys.argv[0])
            sys.exit(2)
        for opt, arg in opts:
            if opt == '-h':
                print '{} --exportReceptions=<> --generateWorkOrders=<> --generateIntrariDinProductie=<> --generateMonetare=<> --importAvize=<> --exportSummaryTransfers=<> --exportSummaryBonDeConsum=<> --exportSales=<> --exportReturns=<> --exportSupplyOrders=<> --branches=<> --verify=<> --markedForWinMentorExport=<> --workDate=<YYYY-MM-DD>'.format(sys.argv[0])
                sys.exit()
            elif opt in ("--exportReceptions"):
                doExportReceptions = bool(int(arg))
            elif opt in ("--exportSales"):
                doExportSales = bool(int(arg))
            elif opt in ("--exportReturns"):
                doExportReturns = bool(int(arg))
            elif opt in ("--exportSupplyOrders"):
                doExportSupplyOrders = bool(int(arg))
            elif opt in ("--generateWorkOrders"):
                doGenerateWorkOrders = bool(int(arg))
            elif opt in ("--generateIntrariDinProductie"):
                doGenerateIntrariDinProductie = bool(int(arg))
            elif opt in ("--generateMonetare"):
                doGenerateMonetare = bool(int(arg))
            elif opt in ("--importAvize"):
                doImportAvize = bool(int(arg))
            elif opt in ("--exportSummaryTransfers"):
                doExportSummaryTransfers = bool(int(arg))
            elif opt in ("--exportSummaryBonDeConsum"):
                doExportSummaryBonDeConsum = bool(int(arg))
            elif opt in ("--branches"):
                branches = [x.strip().replace("_", " ") for x in arg.split(",")]
                branches_default = False
            elif opt in ("--workDate"):
                try:
                    workdate = dt.strptime(arg, "%Y-%m-%d")
                except NoOptionError as e:
                    pass
            elif opt in ("--verify"):
                doVerify = bool(int(arg))
            elif opt in ("--markedForWinMentorExport"):
                markedForWinMentorExport = bool(int(arg))

        logger.info( 'markedForWinMentorExport {}'.format(markedForWinMentorExport))

        if markedForWinMentorExport:
            if dt.now().hour == 12 and dt.now().minute == 5:
                logger.info(">>> E ora 12.05, nu prelua documentele")

                logger.info("END")
                logger.info("<<< {}() - duration = {}".format(inspect.stack()[0][3], dt.now() - start))
                exit()

        tokens = util.getCfgOptsDict("tokens")

        # Connect to winmentor
        winmentor = WinMentor(firma = util.getCfgVal("winmentor", "firma"), an=start.year, luna=start.month)
        if not winmentor:
            logger.error("Failed to get winmentor object")
            1/0

        baseURL = util.getCfgVal("gesto", "url")

        if markedForWinMentorExport:
            logger.info( 'markedForWinMentorExport {}'.format(markedForWinMentorExport))
            getGestoDocumentsMarkedForWinMentorExport(
                            baseURL = baseURL,
                            branch = branches[0]
                        )
        else:
            logger.info( 'exportReceptions {}'.format(doExportReceptions))
            logger.info( 'exportSales {}'.format(doExportSales))
            logger.info( 'exportReturns {}'.format(doExportReturns))
            logger.info( 'exportSupplyOrders {}'.format(doExportSupplyOrders))
            logger.info( 'generateWorkOrders {}'.format(doGenerateWorkOrders))
            logger.info( 'generateIntrariDinProductie {}'.format(doGenerateIntrariDinProductie))
            logger.info( 'generateMonetare {}'.format(doGenerateMonetare))
            logger.info( 'importAvize {}'.format(doImportAvize))
            logger.info( 'exportSummaryTransfers {}'.format(doExportSummaryTransfers))
            logger.info( 'exportSummaryBonDeConsum {}'.format(doExportSummaryBonDeConsum))
            logger.info( 'branches: {}'.format(branches))
            logger.info( 'verify: {}'.format(doVerify))

            daysDelta = util.getCfgVal("gesto", "daysDelta", "int")

            logger.info("Using workdate: {}".format(workdate))

            # end of day
            endDate = workdate.replace(hour=23, minute=59, second=59)
            logger.info("Using end date: {}".format(endDate))

            if doExportReceptions:
                # if dt.now().hour == 13:
                #     logger.info(">>> E ora 12, nu prelua receptiile")
                #     exit()

                if branches_default:
                    branches = cfg.options("receptionsStartDate")

                logger.info( 'branches: {}'.format(branches))

                excludeCUI = util.getCfgVal("receptions", "excludeCUI")

                for branch in branches:
                    gestoData = getGestoDocuments(
                            baseURL = baseURL,
                            branch = branch,
                            operationType="reception",
                            excludeCUI=excludeCUI,
                            endDate = endDate,
                            daysDelta = daysDelta,
                            )

            if doExportSales:
                for branch in branches:
                    gestoData = getGestoDocuments(
                            baseURL = baseURL,
                            branch = branch,
                            operationType="sale",
                            endDate = endDate,
                            daysDelta = daysDelta,
                            )

            if doExportReturns:
                for branch in branches:
                    gestoData = getGestoDocuments(
                            baseURL = baseURL,
                            branch = branch,
                            operationType="return",
                            endDate = endDate,
                            daysDelta = daysDelta,
                            )

            if doExportSupplyOrders:
                for branch in branches:
                    gestoData = getGestoDocuments(
                            baseURL = baseURL,
                            branch = branch,
                            operationType="supplyOrder",
                            endDate = endDate,
                            # daysDelta = daysDelta,
                            daysDelta = 1,
                            )

            # ordinea e importanta
            for branch in branches:
                if doGenerateIntrariDinProductie:
                    ret = generateIntrariDinProductie(
                            baseURL = baseURL,
                            branch = branch,
                            date = endDate,
                            doVerify = doVerify,
                            )

                    if ret == False:
                        # verification failed
                        continue

                if doGenerateWorkOrders:
                    ret = generateWorkOrders(
                            baseURL = baseURL,
                            branch = branch,
                            date = endDate,
                            doVerify = doVerify,
                            )
                    if ret == False:
                        # verification failed
                        continue

                if doExportSummaryTransfers:
                    gestoData = exportSummaryTransfers(
                            baseURL = baseURL,
                            branch = branch,
                            date = endDate,
                            )

                if doExportSummaryBonDeConsum:
                    gestoData = exportSummaryBonDeConsum(
                            baseURL = baseURL,
                            branch = branch,
                            date = endDate,
                            )

                if doGenerateMonetare:
                    gestoData = generateMonetare(
                            baseURL = baseURL,
                            branch = branch,
                            date = endDate,
                            )

                if doImportAvize:
                    gestoData = importAvize(
                            baseURL = baseURL,
                            date = endDate,
                            )

            if branches_monetare != ['']:
                for branch in branches_monetare:
                    if doGenerateMonetare:
                        gestoData = generateMonetare(
                                baseURL = baseURL,
                                branch = branch,
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
