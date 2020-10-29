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
from decimal import Decimal
from django.utils.translation import ngettext
import decorators


@decorators.time_log
def generateWorkOrders(baseURL, branch, date, doVerify):
    # ajung in mentor in NT_G

    url = baseURL + "/products/summary/?"
    companyName = util.getCfgVal("winmentor", "companyName")
    if companyName == "Panemar morarit si panificatie SRL":
        url += "type=workOrder"
    else:
        if branch != "Sediu":
            logger.info("Only generate transfers for Sediu, not for {}".format(branch))
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

    return ret

# NP_G
# productie - exectie - intrari din productie
@decorators.time_log
def generateIntrariDinProductie(baseURL, branch, date, doVerify):
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

    return ret

# bonuri de consum
# BC_G
@decorators.time_log
def exportSummaryTransfers(baseURL, branch, date):
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


@decorators.time_log
def exportSummaryBonDeConsum(baseURL, branch, date):
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


@decorators.time_log
def generateMonetare(baseURL, branch, date):
    logger.info("Generate monetare for {}, {}".format(branch, tokens[branch]))

    # add monetare for the previous day
    dateEnd = date - timedelta(days = 1)
    dateBegin = dateEnd.replace(hour=0, minute=0, second=0)

    sales_details = []

    companyName = util.getCfgVal("winmentor", "companyName")
    if companyName == "Panemar morarit si panificatie SRL":
        logger.info("endDate: {}".format(endDate))
        # adauga intai vanzarile facturate
        sales_details = getGestoDocuments(
                                baseURL = baseURL,
                                branch = branch,
                                operationType="sale",
                                endDate = dateEnd,
                                daysDelta = 1,
                                )

        if sales_details is not None and None in sales_details:
            # there are problems with the sale export
            return

    url = baseURL + "/products/summary/?"
    url += "type=sale"
    url += "&winMentor=1"
    url += "&excludeOpVal=0"

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
        winmentor.addMonetare(retJSON, sales_details)


@decorators.time_log
def getExportedDeliveryNotes(baseURL, startDate, endDate):
    operationType = "reception"
    url = baseURL + "/operations/?"
    url += "&type=" + operationType

    url += "&dateBegin={}".format(util.getTimestamp(startDate))
    url += "&dateEnd={}".format(util.getTimestamp(endDate))
    url += "&returnFields=relatedDocumentNo,itemsCount,value,documentNo,documentDate,simbolWinMentorDeliveryNote"

    filterCUI = util.getCfgVal("receptions", "excludeCUI")
    if filterCUI not in [None, "", ]:
        url += "&filterCUI={}".format(filterCUI)

    token = util.getCfgVal("winmentor", "companyToken")
    logger.error("Gesto request token: {}".format(token))

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
                    ret[op["relatedDocumentNo"]] = op

    util.log_json(ret)

    return ret


@decorators.time_log
def needs_exporting(comanda, exported_receptions_notes):
    ret = False
    if comanda["documentNo"] not in exported_receptions_notes["documentNo"]:
        ret = True
    else:
        exported_op = exported_receptions_notes["ops"][comanda["documentNo"]]
        util.log_json(exported_op)

        logger.info("{} - {},  {} - {}".format(comanda["date"], exported_op["date"], comanda["destination"], exported_op["destination"]))
        if comanda["date"] != exported_op["date"] \
        or comanda["destination"] != exported_op["destination"]:
            ret = True
        else:
            comanda_items = comanda["items"]
            exported_op_items = exported_op["items"]

            if len(comanda_items) != len(exported_op_items):
                ret = True
            else:
                comanda_items = sorted(comanda_items, key=lambda k: k['winMentorCode'])
                exported_op_items = sorted(exported_op_items, key=lambda k: k['winMentorCode'])

                for (i1, i2) in zip(comanda_items, exported_op_items):
                    if any([i1["winMentorCode"] != i2["winMentorCode"],
                            i1["qty"] != i2["qty"],
                            i1["opPrice"] != i2["opPrice"]]):
                        logger.info("i1: {}".format(i1))
                        logger.info("i2: {}".format(i2))
                        ret = True
                        break

    logger.info("ret: {}".format(ret))

    return ret


@decorators.time_log
def exportComenziGest(baseURL, date, interval=1):
    """
    Se exporta comenzile de la gestiuni, ajung receptii in Gesto
    :param
        interval: 1 - default number of days
                  2 - 20 days
    :return:
    """

    # begining of month
    # startDate = date.replace(day=12)
    # startDate = date.replace(day=1, hour=0, minute=0, second=0)
    if interval == 1:
        start_days = 5
        end_days = 0
    elif interval == 2:
        start_days = 20
        end_days = 1
    else:
        1/0

    startDate = date - timedelta(days=start_days)
    startDate = startDate.replace(hour=0, minute=0, second=0, microsecond=0)
    # startDate = startDate.strftime("%d.%m.%Y")

    # startDate = datetime.datetime.strptime("2020-02-01", "%Y-%m-%d")

    # end of month
    # endDate = date.replace(day=25)
    # endDate = endDate + timedelta(days = 10)
    # endDate = endDate.replace(day=1)
    # endDate = endDate - timedelta(days=1)
    # endDate = endDate.replace(hour=23, minute=59, second=59)
    # endDate = endDate.strftime("%d.%m.%Y")
    endDate = date - timedelta(days=end_days)
    endDate = endDate.replace(hour=23, minute=59, second=59, microsecond=0)

    logger.info("startDate: {}".format(startDate))
    logger.info("endDate: {}".format(endDate))

    exported_receptions_notes = getExportedDeliveryNotes(baseURL, startDate, endDate)

    comenziGest = winmentor.getComenziGest(startDate, endDate)

    excludeCUI = util.getCfgVal("receptions", "excludeCUI")

    opStr = {
        "version": "1.1",
        "type": "reception",
        "company": util.getCfgVal("winmentor", "companyName"),
    }

    hour = util.getCfgVal("deliveryNote", "hour", "int")

    for (documentNo, val1) in comenziGest.items():
        # logger.info(documentNo)
        if not needs_exporting(val1, exported_receptions_notes):
            logger.info("Receptia exista: {}, {}, {}".format(documentNo, val1["date"], val1["destination"]))
            continue

        logger.info("Receptia nu exista sau a fost modificata: {}, {}, {}".format(documentNo, val1["date"], val1["destination"]))
        logger.info(val1)

        try:
            op = exported_receptions_notes["ops"][val1["documentNo"]]
            # comanda was modified
            opStr["operation_id"] = op["id"]
        except KeyError:
            # remove operation_id from operation string
            opStr.pop('operation_id', None)

        opStr["relatedDocumentNo"] = documentNo

        # "date": "06.01.2020",
        # "destination": "18 Hateg",
        # "documentNo": "159",
        # "items": [
        #     {
        #         "qty": 40.0,
        opStr["source"] = {
                        "ro": excludeCUI,
                    }

        opStr["destination"] = {
                        "name": val1["destination"],
                        "type": "warehouse"
                    }

        date = [int(x) for x in val1["date"].split(".")]
        date = datetime.datetime(date[2], date[1], date[0])
        # logger.info(date)
        # logger.info(type(date))

        operationDate = datetime.datetime.now()
        opStr["operationDate"] = util.getTimestamp(operationDate)
        opStr["operationDateHuman"] = operationDate.strftime("%d/%m/%Y %H:%M:%S")

        if all([operationDate.day == date.day,
                operationDate.month == date.month,
                operationDate.year == date.year]):
            documentDate = operationDate
        else:
            documentDate = date.replace(hour=hour)

        branchStartDate = dt.strptime(util.getCfgVal("comenziGestStartDate", val1["destination"]), "%Y-%m-%d")
        logger.debug("branchStartDate: {}".format(branchStartDate))

        opStr["documentDate"] = util.getTimestamp(documentDate)
        opStr["documentDateHuman"] = documentDate.strftime("%d/%m/%Y %H:%M:%S")

        opStr["items"] = val1["items"]

        util.log_json(opStr)

        # 1/0

        opStrText = json.dumps(opStr, default=util.defaultJSON)

        if documentDate > branchStartDate:
            logger.info("{} > {}. Receptia se va importa in Gesto".format(documentDate, branchStartDate))

            r = requests.post(baseURL+"/importOperation/", data = opStrText)
            logger.info("Gesto response: %d, %s", r.status_code, r.text)
            if r.status_code != 200:
                logger.error("Gesto request failed: %d, %s", r.status_code, r.text)
                1/0
        else:
            logger.info("{} < {}. Receptia nu se va importa in Gesto".format(documentDate, branchStartDate))

        # 1/0


@decorators.time_log
def importAvize(baseURL, date):
    # begining of previous month
    startDate = date.replace(day=1)
    startDate = startDate - timedelta(days=1)
    startDate = startDate.replace(day=1, hour=0, minute=0, second=0)

    # startDate = startDate.strftime("%d.%m.%Y")
    # startDate = datetime.datetime.strptime("2020-05-01", "%Y-%m-%d")

    # end of month
    endDate = date.replace(day=25)
    endDate = endDate + timedelta(days = 10)
    endDate = endDate.replace(day=1)
    endDate = endDate - timedelta(days=1)
    endDate = endDate.replace(hour=23, minute=59, second=59)
    # endDate = endDate.strftime("%d.%m.%Y")
    # startDate = datetime.datetime.strptime("2020-02-29", "%Y-%m-%d")

    logger.info("startDate: {}".format(startDate))
    logger.info("endDate: {}".format(endDate))

    exported_delivery_notes = getExportedDeliveryNotes(baseURL, startDate, endDate)

    deliveryNotes = winmentor.getTransferuri(startDate, endDate)

    opStr = {
        "version": "1.0",
        "type": "reception",
        "company": util.getCfgVal("winmentor", "companyName"),
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

            if all([operationDate.day == date.day,
                    operationDate.month == date.month,
                    operationDate.year == date.year]):
                documentDate = operationDate
            else:
                documentDate = date.replace(hour=hour)

            for (destination, val3) in val2.items():
                opStr["destination"] = {
                            "name": winmentor.getGestiuneName(destination),
                            "type": "warehouse",
                            "winMentorcode": destination,
                        }

                for (documentNo, val4) in val3.items():
                    winMentorDocumentNos.append(documentNo)
                    opStr["documentDate"] = util.getTimestamp(documentDate)
                    opStr["documentDateHuman"] = documentDate.strftime("%d/%m/%Y %H:%M:%S")

                    do10 = False

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

    # winMentorDocumentNos.pop()
    # winMentorDocumentNos.pop()

    logger.info("{} winMentorDocumentNos: {}".format(len(winMentorDocumentNos), winMentorDocumentNos))
    exported_delivery_notes_document_nos = exported_delivery_notes.keys()
    logger.info("{} exported_delivery_notes: {}".format(len(exported_delivery_notes_document_nos), exported_delivery_notes_document_nos))

    if len(exported_delivery_notes_document_nos) != len(winMentorDocumentNos):
        deleted_delivery_notes = []

        for dn in exported_delivery_notes_document_nos:
            if dn not in winMentorDocumentNos:
                dn_doc = exported_delivery_notes[dn]
                dn_doc["documentDateHuman"] = dt.utcfromtimestamp(dn_doc["documentDate"]).strftime("%d/%m/%Y %H:%M:%S")
                dn_doc["destination"] = winmentor.getGestiuneName(dn_doc["simbolWinMentorDeliveryNote"])
                deleted_delivery_notes.append(dn_doc)

        logger.info("deleted_delivery_notes: {}".format(deleted_delivery_notes))

        template = loader.get_template("mail/admin/WinMentorDeletedDeliveryNotes.html")
        deleted_delivery_notes_cnt = len(deleted_delivery_notes)
        if deleted_delivery_notes_cnt != 0:
            subject = ngettext(
                "%(deleted_delivery_notes_cnt)d aviz sters din WinMentor",
                "%(deleted_delivery_notes_cnt)d avize sterse din WinMentor",
                deleted_delivery_notes_cnt
                ) % {
                    'deleted_delivery_notes_cnt': deleted_delivery_notes_cnt,
                }

            html_part = template.render({
                'HOME_URL': settings.HOME_URL,
                "subject": subject,
                "deleted_delivery_notes": deleted_delivery_notes,
            })
            # send_email(subject, html_part, location=False)
            send_email(subject, html_part, toEmails=util.getCfgVal("client", "notificationEmails"), location=False)


# return: NTR_G
# reception: NTA_G
# sale: FI_G
@decorators.time_log
def getGestoDocuments(baseURL, branch, operationType, excludeCUI=None, endDate = None, daysDelta = 7):
    """
    @param branch: Gesto branch used for request
    @tparam [datetime] startDate: first day of request, defaults to today
    @tparam [numeric] daysDelta: request for how many days, defaults to 7
    @return processed json if successfull, None otherwise

    """

    # opDate = datetime.datetime.strptime("2018-06-01", "%Y-%m-%d")
    # winmentor.transferExists(10, opDate)
    # 1/0
    # endDate = min(endDate, datetime.datetime.strptime("2018-04-30 23:59:59", "%Y-%m-%d %H:%M:%S"))
    # endDate = None

    logger.info("Getting {} from Gesto for {}, {}".format(operationType, branch, tokens[branch]))
    if endDate is None:
        endDate = dt.today()
        endDate = endDate.replace(hour=23, minute=59, second=59)

    if operationType == "reception":
        # start of previousMonth
        startDate = dt.today().replace(day=1, hour=0, minute=0, second=0)
        startDate = startDate - timedelta(days=1)
        startDate = startDate.replace(day=1, hour=0, minute=0, second=0)
        # startDate = datetime.datetime.strptime("2020-02-24", "%Y-%m-%d")
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
        if daysDelta!=1:
            # startDate = dt.today().replace(day=1, hour=0, minute=0, second=0)
            # startDate = startDate - timedelta(days=1)
            # startDate = endDate.replace(day=1, hour=0, minute=0, second=0)
            endDate = endDate.replace(day=1) - datetime.timedelta(days=1)
            endDate = endDate.replace(hour=23, minute=59, second=59)
            startDate = endDate.replace(day=1, hour=0, minute=0, second=0)
        else:
            # preia vanzarile facturate pe o anumita zi
            endDate = endDate.replace(hour=23, minute=59, second=59)
            startDate = endDate.replace(hour=0, minute=0, second=0)
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

    token = tokens[branch]
    logger.error("Gesto request token: {}".format(token))

    ret = []

    r = requests.get(urlCount, headers={'GESTOTOKEN': token})

    if r.status_code != 200:
        logger.error("Gesto request failed: %d, %s", r.status_code, r.text)
    else:
        retJSON = r.json()
        util.log_json(retJSON)

        totalRecords = retJSON["range"]["totalRecords"]
        if totalRecords == 0:
            logger.info("{} {}".format(totalRecords, operationType))
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
            util.log_json(retJSON)

            tot = len(retJSON["data"])
            for ctr2, op in enumerate(retJSON["data"], start=1):
                logger.debug("{}, {}, {}".format(ctr2, tot, op["id"]))
                if op["id"] in [83344696, ]:
                    continue

                # gestoData = retJSON["data"]
                # if util.isArray(gestoData) and len(gestoData) >= 1:
                if op["type"] == "reception":
                    # Get partener from gesto
                    gestoPartener = util.fixupCUI(op["source"]["code"])
                    if gestoPartener == '':
                        gestoPartener = util.fixupCUI(op["source"]["ro"])

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
                    ret.append(winmentor.addSale(op))
                elif op["type"] == "return":
                    winmentor.addWorkOrderFromOperation(op)

                # if ctr2==1:
                #     1/0

    return ret


@decorators.time_log
def getExportWinMentorData():
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
                if retJSON["report_data"]["data"] == "monetare":
                    ret = winmentor.addMonetare(retJSON["report_data"])
                elif retJSON["report_data"]["data"] == "intrariDinProductie":
                    report_data = retJSON["report_data"]

                    logger.info("verify: {}".format(report_data["verify"]))
                    if report_data["verify"] in ["no verify requested", "success", ]:
                        # email is sent from Gesto if there is any problem
                        ret = winmentor.addIntrariDinProductie(report_data)
                    elif report_data["verify"] == "No Vectron data":
                        ret = True
                    else:
                        ret = False
                elif retJSON["report_data"]["data"] == "transferuri":
                    report_data = retJSON["report_data"]

                    logger.info("verify: {}".format(report_data["verify"]))
                    if report_data["verify"] in ["no verify requested", "success", ]:
                        # email is sent from Gesto if there is any problem
                        ret = winmentor.addWorkOrders(report_data)
                    elif report_data["verify"] == "No Vectron data":
                        ret = True
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


@decorators.time_log
def getGestoDocumentsMarkedForWinMentorExport(baseURL, branch):
    """
    @param branch: Gesto branch used for request
    """
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
        util.log_json(retJSON)

        totalRecords = retJSON["range"]["totalRecords"]
        logger.info("{} operations".format(totalRecords))
        if totalRecords == 0:
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
                if gestoPartener == '':
                    gestoPartener = util.fixupCUI(op["source"]["ro"])

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

        workdate = dt.today()

        doExportReceptions = False
        doExportSales = False
        doExportReturns = False
        doExportSupplyOrders = False
        doGenerateWorkOrders = False
        doGenerateIntrariDinProductie = False
        doGenerateMonetare = False
        doImportAvize = False
        doExportComenziGest = False
        doExportSummaryTransfers = False
        doExportSummaryBonDeConsum = False

        doVerify = False
        companyName = util.getCfgVal("winmentor", "companyName")
        if companyName == "Panemar morarit si panificatie SRL":
            doVerify = True

        markedForWinMentorExport = False
        exportWinMentorData = False

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
                                     "exportComenziGest=",
                                     "exportSummaryTransfers=",
                                     "exportSummaryBonDeConsum=",
                                     "branches=",
                                     "verify=",
                                     "workDate=",
                                     "markedForWinMentorExport=",
                                     "exportWinMentorData=",
                                    ])

            logger.info(opts)
            logger.info(args)

        except getopt.GetoptError:
            print '{} --exportReceptions=<> --generateWorkOrders=<> --generateIntrariDinProductie=<> --generateMonetare=<> --importAvize=<> --exportComenziGest=<> --exportSummaryTransfers=<> --exportSummaryBonDeConsum=<> --exportSales=<> --exportReturns=<> --exportSupplyOrders=<> --branches=<> --verify=<> --markedForWinMentorExport=<> --exportWinMentorData=<> --workDate=<YYYY-MM-DD>'.format(sys.argv[0])
            sys.exit(2)
        for opt, arg in opts:
            if opt == '-h':
                print '{} --exportReceptions=<> --generateWorkOrders=<> --generateIntrariDinProductie=<> --generateMonetare=<> --importAvize=<> --exportComenziGest=<> --exportSummaryTransfers=<> --exportSummaryBonDeConsum=<> --exportSales=<> --exportReturns=<> --exportSupplyOrders=<> --branches=<> --verify=<> --markedForWinMentorExport=<> --exportWinMentorData=<> --workDate=<YYYY-MM-DD>'.format(sys.argv[0])
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
            elif opt in ("--exportComenziGest"):
                doExportComenziGest = int(arg)
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
            elif opt in ("--exportWinMentorData"):
                exportWinMentorData = bool(int(arg))

        logger.info( 'markedForWinMentorExport {}'.format(markedForWinMentorExport))
        logger.info( 'exportWinMentorData {}'.format(exportWinMentorData))

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
        elif exportWinMentorData:
            logger.info( 'exportWinMentorData {}'.format(exportWinMentorData))
            getExportWinMentorData()

        else:
            logger.info( 'exportReceptions {}'.format(doExportReceptions))
            logger.info( 'exportSales {}'.format(doExportSales))
            logger.info( 'exportReturns {}'.format(doExportReturns))
            logger.info( 'exportSupplyOrders {}'.format(doExportSupplyOrders))
            logger.info( 'generateWorkOrders {}'.format(doGenerateWorkOrders))
            logger.info( 'generateIntrariDinProductie {}'.format(doGenerateIntrariDinProductie))
            logger.info( 'generateMonetare {}'.format(doGenerateMonetare))
            logger.info( 'importAvize {}'.format(doImportAvize))
            logger.info( 'exportComenziGest {}'.format(doExportComenziGest))
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

            if doImportAvize:
                gestoData = importAvize(
                        baseURL = baseURL,
                        date = endDate,
                        )

            if doExportComenziGest:
                gestoData = exportComenziGest(
                        baseURL = baseURL,
                        date = endDate,
                        interval = doExportComenziGest
                        )

            # ordinea e importanta
            for branch in branches:
                logger.info("Working with branch: {}".format(branch))

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
        winmentor.sendComenziWithProblemsMail()


    except Exception as e:
        print repr(e)
        logger.exception(repr(e))
        util.newException(e)

    logger.info("END")
    logger.info("<<< {}() - duration = {}".format(inspect.stack()[0][3], dt.now() - start))
