import requests
import json
import os
import sys, getopt
import datetime
import util
import settings
from winmentor import WinMentor
from datetime import datetime as dt, timedelta
import logging.config
from configparser import ConfigParser, NoOptionError
import codecs
from util import send_email
import re
import traceback
import inspect
from django.template import loader, Context
import django
import decorators
from decimal import Decimal


def generateWorkOrders(baseURL, branch, date):
    logger.info(">>> {}()".format(inspect.stack()[0][3]))
    start = dt.now()

    url = baseURL + "/products/summary/?"
    url += "type=sale"
    verify=False # only for workOrders
    if verify:
        url += "&verify=1"

    url += "&winMentor=1"
    # url += "&excludeListVal=0"
    url += "&excludeCodes=1,2"

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
    logger.debug("token: {}".format(token))

    r = requests.get(url, headers={'GESTOTOKEN': token})

    if r.status_code != 200:
        logger.error("Gesto request failed: %d, %s", r.status_code, r.text)
        logger.error("Gesto request url: {}", url)

        1/0
    else:
        retJSON = r.json()

        if retJSON["verify"] in ["success", "no verify requested", ]:
            # email is sent from Gesto if there is any problem
            winmentor.addWorkOrders(retJSON)

    logger.info("<<< {}() - duration = {}".format(inspect.stack()[0][3], dt.now() - start))


def generateMonetare(baseURL, branch, date):
    logger.info(">>> {}()".format(inspect.stack()[0][3]))
    start = dt.now()

    company = util.getCfgVal("winmentor", "companyName")
    logger.info("Generate monetare for {}, {}".format(branch, tokens[branch]))

    url = baseURL + "/products/summary/?"
    url += "type=sale"

    verify=False # only for workOrders
    if verify:
        url += "&verify=1"

    url += "&winMentor=1"
    url += "&excludeOpVal=0"

    if company in ["CARMIC IMPEX SRL",]:
        url += "&cumulate_poses=0"

    # url += "&excludeCodes=1,2"
    # url += "&excludeNoStock=1"

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
    r = requests.get(url, headers={'GESTOTOKEN': token})

    if r.status_code != 200:
        logger.error("Gesto request failed: %d, %s", r.status_code, r.text)
        logger.error("Gesto request url: {}", url)
        logger.error("Gesto request token: {}", token)
        1/0
    else:
        retJSON = r.json()
        # logger.debug(retJSON)

        # email is sent from Gesto if there is any problem
        if isinstance(retJSON, dict):
            if not verify or retJSON["verify"] == "success":
                winmentor.addMonetare(retJSON)
        elif isinstance(retJSON, list):
            for monetar in retJSON:
                if not verify or retJSON["verify"] == "success":
                    winmentor.addMonetare(monetar)

    logger.info("<<< {}() - duration = {}".format(inspect.stack()[0][3], dt.now() - start))


@decorators.time_log
def getExportedDeliveryNotes(baseURL, startDate, endDate):
    operationType = "reception,receptionImported"
    url = baseURL + "/operations/?"
    url += "&type=" + operationType

    url += "&dateBegin={}".format(util.getTimestamp(startDate - timedelta(days = 1)))
    url += "&dateEnd={}".format(util.getTimestamp(endDate))

    companyName = util.getCfgVal("winmentor", "companyName")

    url += "&returnFields=relatedDocumentNo,itemsCount,value,documentNo,documentDate,simbolWinMentorDeliveryNote"

    source_name = util.getCfgVal("deliveryNote", "source_name")
    if source_name not in [None, "", ]:
        url += "&source_name={}".format(source_name)

    token = util.getCfgVal("winmentor", "companyToken")
    logger.debug("Gesto request token: {}".format(token))

    urlPage = url + "&pageSize=1"
    logger.info(urlPage)

    r = requests.get(urlPage, headers={'GESTOTOKEN': token})

    ret = {}

    if r.status_code != 200:
        logger.error("Gesto request failed: %d, %s", r.status_code, r.text)
        1/0
    else:
        retJSON = r.json()
        util.log_json(retJSON)

        totalRecords = retJSON["range"]["totalRecords"]
        logger.info("{} {}".format(totalRecords, operationType))

        if totalRecords != 0:
            pageSize = 500
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
                    if "itemsCount" in op and op["itemsCount"] == 0:
                        logger.info("No product on this operation")
                        continue

                    ret[op["relatedDocumentNo"]] = op

    util.log_json(ret.keys())

    return ret


def importAvize(baseURL, date):
    logger.info(">>> {}()".format(inspect.stack()[0][3]))
    start = dt.now()

    exported_delivery_notes = getExportedDeliveryNotes(baseURL, date, date)

    deliveryNotes = winmentor.getTransferuri(date)

    company = util.getCfgVal("winmentor", "companyName")

    opStr = {
        "version": "1.0",
        "type": "reception",
        "company": company,
    }

    hour = util.getCfgVal("deliveryNote", "hour", "int")

    winMentorDocumentNos = []

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

            for (destination, val3) in val2.items():
                if company in ["SC Pan Partener Spedition Arg SRL"]:
                    dest_name = destination
                else:
                    dest_name = winmentor.getGestiuneName(destination),

                opStr["destination"] = {
                            "name": dest_name,
                            "type": "warehouse",
                            "winMentorcode": destination,
                        }

                for (documentNo, val4) in val3.items():
                    winMentorDocumentNos.append(documentNo)
                    opStr["documentDate"] = util.getTimestamp(documentDate)
                    opStr["documentDateHuman"] = documentDate.strftime("%d/%m/%Y %H:%M:%S")

                    if documentNo in exported_delivery_notes:
                        exported_document = exported_delivery_notes[documentNo]
                        exp_val = Decimal("{:.2f}".format(exported_document["value"]))
                        val4_val = Decimal("{:.2f}".format(val4["value"]))

                        logger.info("count: {} - {}, value: {} - {}, date: {} - {}, destination: {} - {}".format(
                                                            exported_document["itemsCount"],
                                                            len(val4["items"]),
                                                            exp_val,
                                                            val4_val,
                                                            datetime.datetime.utcfromtimestamp(exported_document["documentDate"]).date(),
                                                            documentDate.date(),
                                                            destination,
                                                            exported_document["simbolWinMentorDeliveryNote"]
                                                            ))

                        if destination == exported_document["simbolWinMentorDeliveryNote"] \
                        and datetime.datetime.utcfromtimestamp(exported_document["documentDate"]).date() == documentDate.date()\
                        and exported_document["itemsCount"] == len(val4["items"]) \
                        and exp_val == val4_val:
                            logger.info("Receptia {} exista".format(documentNo))
                            continue
                        else:
                            logger.info("Receptia {} a fost modificata".format(documentNo))
                            logger.info("gesto-wm ... count: {} - {}, value: {} - {}, date: {} - {}, destination: {} - {}".format(
                                                            exported_document["itemsCount"],
                                                            len(val4["items"]),
                                                            exp_val,
                                                            val4_val,
                                                            datetime.datetime.utcfromtimestamp(exported_document["documentDate"]).date(),
                                                            documentDate.date(),
                                                            destination,
                                                            exported_document["simbolWinMentorDeliveryNote"]
                                                            ))

                            opStr["operation_id"] = exported_document["id"]
                            opStr["documentNo"] = exported_document["documentNo"]

                    else:
                        logger.info("Receptia {} nu exista".format(documentNo))


                    opStr["relatedDocumentNo"] = documentNo
                    opStr["items"] = []

                    for item in val4["items"]:
                        opStr["items"].append(item)

                    util.log_json(opStr)

                    opStrText = json.dumps(opStr, default=util.defaultJSON)

                    r = requests.post(baseURL+"/importOperation/", data = opStrText)
                    logger.info("Gesto response: %d, %s", r.status_code, r.text)
                    if r.status_code != 200:
                        logger.error("Gesto request failed: %d, %s", r.status_code, r.text)
                        1/0

                    # 1/0
                    opStr.pop('documentNo', None)
                    opStr.pop('items', None)
                    opStr.pop('operation_id', None)
                    opStr.pop('documentDate', None)
                opStr.pop('destination', None)
        opStr.pop('source', None)

    logger.info("<<< {}() - duration = {}".format(inspect.stack()[0][3], dt.now() - start))


def getGestoDocuments(baseURL, branch, operationType, excludeCUI=None, endDate = None, daysDelta = 7):
    """
    @param branch: Gesto branch used for request
    @tparam [datetime] startDate: first day of request, defaults to today
    @tparam [numeric] daysDelta: request for how many days, defaults to 7
    @return processed json if successfull, None otherwise

    """
    logger.info(">>> {}()".format(inspect.stack()[0][3]))
    start = dt.now()

    logger.info("Getting receptie from Gesto for {}, {}".format(branch, tokens[branch]))
    if endDate is None:
        endDate = dt.today()
        endDate = endDate.replace(hour=23, minute=59, second=59)

    startDate = (endDate - timedelta(days = daysDelta)).replace(hour=0, minute=0, second=0)
    start = datetime.datetime.strptime("2023-09-29", "%Y-%m-%d")
    branchStartDate = dt.strptime(util.getCfgVal("receptionsStartDate", branch), "%Y-%m-%d")
    logger.debug("startDate: {}".format(branchStartDate))
    startDate = max([startDate, branchStartDate])

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
    token = tokens[branch]
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

        pageSize = 10
        pagesCount = int((totalRecords + pageSize - 1) / pageSize)
        print("pagesCount: {}".format(pagesCount))

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
                if operationType == "reception":
                    # Get partener from gesto
                    gestoPartener = util.fixupCUI(op["source"]["code"])
                    logger.info("gestoPartener = {}".format(gestoPartener))
                    winmentor.addReception(op)

                # if ctr2==2:
                #     1/0

    logger.info("<<< {}() - duration = {}".format(inspect.stack()[0][3], dt.now() - start))


def getGestoDocumentsMarkedForWinMentorExport(baseURL):
    """
    @param branch: Gesto branch used for request
    """

    logger.info("Getting all operations marked for WinMentorExport")
    url = baseURL + "/operations/?"
    url += "&markedForWinMentorExport=1"
    url += "&onlyKeepStockProducts=1"
    logger.debug(url)

    token = util.getCfgVal("winmentor", "companyToken")
    logger.debug("Gesto request token: {}".format(token))

    r = requests.get(url, headers={'GESTOTOKEN': token})

    if r.status_code != 200:
        logger.error("Gesto request failed: %d, %s", r.status_code, r.text)
    else:
        retJSON = r.json()
        util.log_json(retJSON)

        totalRecords = retJSON["range"]["totalRecords"]
        logger.info("{} operations".format(totalRecords))
        if totalRecords == 0:
            return

        if retJSON["data"][0]["simbolWinMentorReception"] in [None, "nil",]:
            txtMail = "Locatia {} nu are setat un simbol pentru WinMentor".format(retJSON["data"][0]["destination"]["name"])

            send_email(
                    subject = txtMail,
                    msg = txtMail
                    )

            return

        totalRecords = retJSON["range"]["totalRecords"]
        logger.info("{} operations".format(totalRecords))

        for ctr, op in enumerate(retJSON["data"], start=1):
            logger.debug("{}, {}, {}".format(ctr, totalRecords, op["id"]))

            is_exported_OK = False

            opDate = dt.utcfromtimestamp(op["documentDate"])

            # winmentor.setLunaLucru(opDate.month, opDate.year)

            if op["type"]== "reception":
                # Get partener from gesto
                gestoPartener = util.fixupCUI(op["source"]["code"])
                if gestoPartener == '':
                    gestoPartener = util.fixupCUI(op["source"]["ro"])

                logger.info("gestoPartener = {}".format(gestoPartener))

                # op["items"] = op["items"]
                if int(gestoPartener) > 1500 \
                or int(gestoPartener) < 0:
                    is_exported_OK = winmentor.addReception(op)
                else:
                    is_exported_OK = winmentor.addWorkOrderFromOperation(op)
            elif op["type"] == "supplyOrder":
                if not op["products_missing_category"]:
                    is_exported_OK = winmentor.addSupplyOrder(op)
            elif op["type"] in ["return", "notaConstatareDiferente"]:
                is_exported_OK = winmentor.addWorkOrderFromOperation(op)
            elif op["type"] in ["scrap"]:
                is_exported_OK = winmentor.addNotaModificareStoc(op)
            elif op["type"] in ["productPriceChange",]:
                is_exported_OK = winmentor.addModificarePret(op)
            elif op["type"] == "NotaReglareStoc":
                items_qty_plus = []
                items_qty_minus = []
                for item in op["items"]:
                    if item["qty"] > 0:
                        items_qty_plus.append(item)
                    elif item["qty"] < 0:
                        items_qty_minus.append(item)

                op["items"] = items_qty_minus
                is_exported_OK = winmentor.addNotaModificareStoc(op)
                op["items"] = items_qty_plus
                is_exported_OK = winmentor.addNotaModificareStoc(op, "Marire")

                is_exported_OK = False
            else:
                logger.info(f'!!! {op["type"]} - nu se exporta !!!')

            if is_exported_OK:
                url = baseURL + "/operations/{}/exportedWinMentor/".format(op["id"])
                r = requests.put(url, headers={'GESTOTOKEN': token})
                logger.info(r)

            # if ctr==1:
            #     1/0

def getExportWinMentorData():
    logger.info(">>> {}()".format(inspect.stack()[0][3]))
    start = dt.now()

    baseURL = util.getCfgVal("gesto", "url")
    token = util.getCfgVal("winmentor", "companyToken")
    url = baseURL + "/report/exportWinMentorData/"

    while True:
        # until no other exported report exists
        url = baseURL + "/report/exportWinMentorData/"

        r = requests.get(url, headers={'GESTOTOKEN': token})

        if r.status_code != 200:
            logger.error("Gesto request failed: %d, %s", r.status_code, r.text)
            break
        else:
            retJSON = r.json()
            util.log_json(retJSON)

            if retJSON["report_id"] is not None:
                if isinstance(retJSON["report_data"], list):
                    # doar monetarele pot veni ca lista
                    for rd in retJSON["report_data"]:
                        ret = winmentor.addMonetare(rd)
                elif retJSON["report_data"]["data"] == "monetare":
                    ret = winmentor.addMonetare(retJSON["report_data"])
                elif retJSON["report_data"]["data"] == "intrari_din_productie":
                    report_data = retJSON["report_data"]

                    logger.info("verify: {}".format(report_data["verify"]))
                    if report_data["verify"] in ["no verify requested", "success", ]:
                        # email is sent from Gesto if there is any problem
                        ret = winmentor.addIntrariDinProductie(report_data)
                    # elif report_data["verify"] == "No Vectron data":
                    #     ret = True
                    else:
                        ret = False
                elif retJSON["report_data"]["data"] == "transferuri":
                    report_data = retJSON["report_data"]

                    logger.info("verify: {}".format(report_data["verify"]))
                    if report_data["verify"] in ["no verify requested", "success", ]:
                        # email is sent from Gesto if there is any problem
                        ret = winmentor.addWorkOrders(report_data)
                    # elif report_data["verify"] == "No Vectron data":
                    #     ret = True
                    else:
                        ret = False
                elif retJSON["report_data"]["data"] == "bonuri_de_consum":
                    ret = winmentor.addProductSummary(retJSON["report_data"])
                else:
                    1/0

                logger.info("ret: {}".format(ret))

                if ret:
                    # success
                    url = baseURL + "/report/exportWinMentorData/{}/exportedWinMentor/".format(retJSON["report_id"])
                    r = requests.put(url, headers={'GESTOTOKEN': token})
                    logger.info(r)
                else:
                    url = baseURL + "/report/exportWinMentorData/{}/exportProblems/".format(retJSON["report_id"])
                    r = requests.put(url, headers={'GESTOTOKEN': token})
                    logger.info(r)

                if retJSON["remaining_reports"] == 0:
                    logger.info("No more reports to export")
                    break
            else:
                logger.info("report id is null")
                break


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

                    if os.path.exists(path):
                        path = os.path.join(
                            folder,
                            dt.strftime(dt.now(), "%Y_%m_%d__%H_%M__%f.log")
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
        cfg = ConfigParser()
        cfg.optionxform = str
        cfg.read_file(open('config_local.ini'))

        logger.info(">>> {}()".format(inspect.stack()[0][3]))
        start = dt.now()

        # start = datetime.datetime.strptime("2023-09-25", "%Y-%m-%d")

        tokens={}
        for opt in cfg.options("tokens"):
            tokens[opt] = str(util.getCfgVal("tokens", opt))

        # Connect to winmentor
        import os
        cwd = os.getcwd()
        logger.info("cwd: {}".format(cwd))

        # for f in os.listdir("\\mentor\\winment\\"):
        #     logger.info(f)

        winmentor = WinMentor(firma = util.getCfgVal("winmentor", "firma"), an=start.year, luna=start.month)
        if not winmentor:
            logger.error("Failed to get winmentor object")
            1/0

        # TODO -- END TESTING --

        logger.info("START")

        branches = util.getCfgVal("gesto", "branches")

        # Get date to use for Unit Test
        try:
            workdate = dt.strptime(util.getCfgVal("_UT_", "workdate"), "%Y-%m-%d")
        except NoOptionError as e:
            workdate = dt.today()

        doExportReceptions = util.getCfgVal("gesto", "exportReceptions", "bool")
        doGenerateWorkOrders = util.getCfgVal("gesto", "generateWorkOrders", "bool")
        doGenerateMonetare = util.getCfgVal("gesto", "generateMonetare", "bool")
        doImportAvize = util.getCfgVal("gesto", "importAvize", "bool")

        markedForWinMentorExport = False
        exportWinMentorData = False

        try:
            opts, args = getopt.getopt(sys.argv[1:],"h",["exportReceptions=",
                                     "generateWorkOrders=",
                                     "generateMonetare=",
                                     "importAvize=",
                                     "branches=",
                                     "exportWinMentorData=",
                                     "markedForWinMentorExport=",
                                     "workDate="
                                    ])

            logger.info(opts)
            logger.info(args)

        except getopt.GetoptError:
            print('{} --exportReceptions=<> --generateWorkOrders=<> --generateMonetare=<> --importAvize=<> --branches=<> --workDate=<YYYY-MM-DD>'.format(sys.argv[0]))
            sys.exit(2)
        for opt, arg in opts:
            if opt == '-h':
                print('{} --exportReceptions=<> --generateWorkOrders=<> --generateMonetare=<> --importAvize=<> --branches=<> --workDate=<YYYY-MM-DD>'.format(sys.argv[0]))
                sys.exit()
            elif opt in ("--exportReceptions"):
                doExportReceptions = bool(int(arg))
            elif opt in ("--generateWorkOrders"):
                doGenerateWorkOrders = bool(int(arg))
            elif opt in ("--generateMonetare"):
                doGenerateMonetare = bool(int(arg))
            elif opt in ("--importAvize"):
                doImportAvize = bool(int(arg))
            elif opt in ("--branches"):
                branches = [x.strip() for x in arg.split(",")]
            elif opt in ("--markedForWinMentorExport"):
                markedForWinMentorExport = bool(int(arg))
            elif opt in ("--exportWinMentorData"):
                exportWinMentorData = bool(int(arg))
            elif opt in ("--workDate"):
                try:
                    workdate = dt.strptime(arg, "%Y-%m-%d")
                except NoOptionError as e:
                    pass

        logger.info( 'exportReceptions {}'.format(doExportReceptions))
        logger.info( 'generateWorkOrders {}'.format(doGenerateWorkOrders))
        logger.info( 'generateMonetare {}'.format(doGenerateMonetare))
        logger.info( 'importAvize {}'.format(doImportAvize))
        logger.info( 'branches: {}'.format(branches))

        logger.info( 'markedForWinMentorExport {}'.format(markedForWinMentorExport))
        logger.info( 'exportWinMentorData {}'.format(exportWinMentorData))

        daysDelta = util.getCfgVal("gesto", "daysDelta", "int")
        baseURL = util.getCfgVal("gesto", "url")

        logger.info("Using workdate: {}".format(workdate))

        # end of day
        endDate = workdate.replace(hour=23, minute=59, second=59)
        logger.info("Using end date: {}".format(endDate))

        if markedForWinMentorExport or exportWinMentorData:
            if markedForWinMentorExport:
                logger.info( 'markedForWinMentorExport {}'.format(markedForWinMentorExport))
                getGestoDocumentsMarkedForWinMentorExport(
                                baseURL = baseURL,
                            )

            if exportWinMentorData:
                logger.info( 'exportWinMentorData {}'.format(exportWinMentorData))
                getExportWinMentorData()

        else:
            if doExportReceptions:
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

            if doGenerateMonetare:
                if util.cfg_has_section("monetareCasa"):
                    branches = cfg.options("monetareCasa")
                    logger.info( 'branches: {}'.format(branches))

                for branch in branches:
                    gestoData = generateMonetare(
                            baseURL = baseURL,
                            branch = branch,
                            date = endDate,
                            )

            if doGenerateWorkOrders:
                if util.cfg_has_section("monetareCasa"):
                    branches = cfg.options("monetareCasa")
                    logger.info( 'branches: {}'.format(branches))

                for branch in branches:
                    gestoData = generateWorkOrders(
                            baseURL = baseURL,
                            branch = branch,
                            date = endDate,
                            )

            if doImportAvize:
                gestoData = importAvize(
                        baseURL = baseURL,
                        date = endDate,
                        )

        # Send mail with new products and partners
        winmentor.sendNewProductsMail()
        winmentor.sendPartnersMail()
        winmentor.sendIncorrectWinMentorProductsMail()

    except Exception as e:
        print(repr(e))
        logger.exception(repr(e))
        util.newException(e)

    logger.info("END")
    logger.info("<<< {}() - duration = {}".format(inspect.stack()[0][3], dt.now() - start))
