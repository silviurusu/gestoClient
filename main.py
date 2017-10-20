import requests
import json
import os
import sys
import datetime
import util
import settings
import re
from winmentor import WinMentor
from datetime import datetime as dt, timedelta
from itertools import izip
import logging
import logging.config
import functools
from ConfigParser import SafeConfigParser, NoOptionError, NoSectionError
import codecs
from util import send_email


def disable_logging(lvl = logging.DEBUG): # TODO move to utils
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


def getGestoReceptie(baseURL, token, startDate = None, daysDelta = 7):
    """
    @param token: Gesto token used for request
    @tparam [datetime] startDate: first day of request, defaults to today
    @tparam [numeric] daysDelta: request for how many days, defaults to 7
    @return processed json if successfull, None otherwise

    """
    logger.info("Getting receptie from Gesto.")
    if startDate is None:
        startDate = dt.today()
    startDate, endDate = startDate - timedelta(days = daysDelta), startDate

    idStart=None
    idEnd=None

    opType = "reception"

    url = baseURL + "/operations?"
    url += "&type="+opType
    if startDate is not None:
        startDate = util.getTimestamp(startDate)
        url += "&dateBegin="+str(startDate)
    if endDate is not None:
        endDate = util.getTimestamp(endDate)
        url += "&dateEnd="+str(endDate)

    if idStart is not None:
        url += "&idStart="+str(idStart)
    if idEnd is not None:
        url += "&idStart="+str(idEnd)

    urlCount = url + "&pageSize="+str(1)
    urlCount += "&page="+str(1)
    logger.debug(url)
    logger.debug("startDate: {}".format(dt.fromtimestamp(startDate)))
    logger.debug("endDate: {}".format(dt.fromtimestamp(endDate)))

    retJSON = None
    r = requests.get(urlCount, headers={'GESTOTOKEN': token})

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

    return retJSON

@disable_logging(logging.DEBUG)
def fixupCUI(cui):
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

def matchGestiune(name, listaGestiuni):
    """
    @param name: Nume destinatie din Gesto
    @param listaGestiuni: Lista gestiuni din WinMentor

    """
    result = []

    x = re.match("^\s*([0-9]{1,4})\s*", name)
    if x:
        no = x.group(1)
        if no:
            logger.debug(repr(no))
            # Find a "gestiune" that matches
            for gestiune in listaGestiuni:
                regex = r"^\s*" + re.escape(no) + "\s*Magazin"
                found = re.match(regex, gestiune["denumire"], re.IGNORECASE)
                if found:
                    result.append(gestiune)

    return result

def genNrNir():
    """ Genereaza nr NIR pentru o factura noua

    """
    # TODO implementme
    return "672267"

def cleanId(name):
    """ Remove spaces and convert a id/name to smallcase, to avoid
    user insert format problems. Example: "31 Vlaicu", "31Vlaicu" all
    convert to "31vlaicu"

    """
    return "".join(name.lower().split())


def work2(winmentor, gestoData, cui):
    # TODO commentme
    # TODO renameme

    _, cui = fixupCUI(cui)
    logger.info("CUI Panemar: {}".format(cui))

    # Get from winmentor parteneri si produse, indexeaza-le dupa coduri
    def getwmParteneri():
        return { fixupCUI(p["idPartener"])[1]: p for p in winmentor.getListaParteneri() }
    wmParteneri = getwmParteneri()
    logger.debug("len(wmParteneri)=%d", len(wmParteneri))

    def getwmProduse():
        return { p["CodExternIntern"] : p for p in winmentor.getNomenclatorArticole() }
    wmProds = getwmProduse()
    logger.debug("len(wmProds)=%d", len(wmProds))

    # Get gestiuni
    gestiuni = winmentor.getListaGestiuni()

    for entry in gestoData:
        # Get partener from gesto
        _, gestoPartener = fixupCUI(entry["source"]["code"])
        logger.info("gestoPartener = {}".format(gestoPartener))

        # Get gestiune in WinMentor
        magazine = matchGestiune(entry["destination"]["name"], gestiuni)
        wmGestiune = None
        fromPanemar = (cui == gestoPartener)
        for magazin in magazine:
            den = magazin["denumire"]
            if (fromPanemar and re.search("PRODUSE", den, re.IGNORECASE)) or \
                    re.search("marfa", den, re.IGNORECASE):
                wmGestiune = magazin["simbol"]
                break
        logger.info("gestiune in WinMentor: {}".format(wmGestiune))

        # Seteaza luna si anul in WinMentor
        opDate = dt.fromtimestamp(entry["operationDate"])
        winmentor.setLunaLucru(opDate.month, opDate.year)

        wmPartener = None # Cod partener exact ca in Winmentor

        if wmParteneri.get(gestoPartener):
            logger.info("Gasit partener")
            wmPartener = wmParteneri[gestoPartener]["idPartener"]
        else:
            logger.info(
                    "Need to add partner to winmentor - codFiscal: %s, denumire: %s",
                    gestoPartener, entry["source"]["name"]
                    )
            wmPartener = gestoPartener
            rc = winmentor.adaugaPartener(
                    codFiscal = gestoPartener,
                    denumirePartener = entry["source"]["name"]
                    )
            if not rc:
                logger.error(repr(winmentor.getListaErori()))
                return

            # Get again lista parteneri, check if added correcly
            wmParteneri = getwmParteneri()
            logger.debug("len(wmParteneri)=%d (again)", len(wmParteneri))
            if wmParteneri.get(gestoPartener) is None:
                logger.error("Failed to add new partener correcly.")
                return

        # Cauta daca exista deja o factura in Winmentor cu intrarea din gesto
        alreadyAdded = False
        lstArt = winmentor.getFactura(
                partenerId = wmPartener,
                serie = "",
                nr = entry["documentNo"],
                data = opDate
                )
        if lstArt and (len(lstArt) != 0):
            logger.info("Gasit intrare in winmentor.")
            if len(lstArt) != len(entry["items"]):
                logger.error("Product list from gesto is different than product list from winmentor")
            else:
                # Verifica toate produsele din factura daca corespund cu cele din gesto
                alreadyAdded = True

                for artWm in lstArt:
                    wmCode = artWm["idArticol"]
                    # Remove "G_" prefix, if any
                    wmCode = wmCode[len("G_"):] if wmCode.startswith("G_") else wmCode

                    # Search for article from winmentor in gesto array
                    artGesto = None
                    for a in entry["items"]:
                        if wmCode == a["code"]:
                            artGesto = a["code"]
                            break

                    if artGesto is None:
                        logger.error("Product [%s] from winmentor not found gesto", wmCode)
                        alreadyAdded = False
                        break

        if alreadyAdded:
            logger.info("Factura e deja adaugata")
            return

        # Get lista articole from gesto, create array of articole pentru factura
        articoleFactura = []
        for articol in entry["items"]:
            # Remove "." from all articol strings
            articol = { key: val.replace(".", "") if isinstance(val, basestring) else val for key, val in articol.iteritems() }
            gestoId = articol["code"]
            # Check if articol is in WinMentor
            haveArticol = wmProds.get(gestoId)
            if not haveArticol:
                if not gestoId.startswith("G_"):
                    gestoId = "G_" + gestoId
                    haveArticol = wmProds.get(gestoId)
            if not haveArticol:
                # Adauga produs in winmentor, cu prefixul G_
                logger.info("Need to add product to winmentor")
                rc = winmentor.addProduct(
                        idArticol = gestoId,
                        denumire = articol["name"],
                        codIntern = articol["id"],
                        um = articol["um"],
                        pret = articol["listPrice"],
                        cotaTVA = articol["vat"]
                        )
                if not rc:
                    logger.error(repr(winmentor.getListaErori()))
                    return

                # Get again lista articole
                wmProds = getwmProduse()
                if wmProds.get(gestoId) is None:
                    logger.error("Failed to add articol to Winmentor")
                    return
                logger.debug("len(wmProds)=%s (again)", len(wmProds))

            # Adauga produs la lista produse factura
            articoleFactura.append(
                    {
                        "codExternArticol": gestoId,
                        "um": articol["um"],
                        "cant": articol["qty"],
                        "pret": articol["listPrice"],
                        "simbGest": wmGestiune
                        }
                    )

        # Creaza factura import
        rc = winmentor.importaFactIntrare(
                logOn = "Master", # TODO what's this?
                nrDoc = entry["documentNo"],
                nrNir = genNrNir(),
                data = opDate,
                dataNir = opDate,
                scadenta = opDate + timedelta(days = 1),
                codFurnizor = wmPartener,
                items = articoleFactura
                )
        if rc:
            logger.info("SUCCESS: Adaugare factura")
        else:
            logger.error(repr(winmentor.getListaErori()))


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
                            dt.strftime(dt.now(), "%Y_%m_%d.log")
                            )
                    if not os.path.exists(folder):
                        os.mkdir(folder)
                    dhandler["filename"] = path

        logging.config.dictConfig(config)
    else:
        logging.basicConfig(level=default_level)


if __name__ == "__main__":
    # Get logger
    setup_logging()
    logger = logging.getLogger(name = __name__)

    # Get Script settings
    cfg = SafeConfigParser()
    try:
        with codecs.open('config_local.ini', 'r', encoding='utf-8') as f:
            cfg.readfp(f)
    except:
        logger.exception("Failed to read .ini file")
        sys.exit(1)

    # Connect to winmentor
    try:
        winmentor = WinMentor(firma = cfg.get("winmentor", "firma"))
        if not winmentor:
            logger.error("Failed to get winmentor object")
            sys.exit(1)
    except:
        logger.exception("Failed link to winmentor")
        sys.exit(1)

    # Set DJANGO for email support
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")

    logger.info("START")

    toEmails = [x.strip() for x in cfg.get("client", "emails").split(",")]
    tokens = [x.strip() for x in cfg.get("gesto", "tokens").split(",")]

    # Get date to use for Unit Test
    utDate = None
    try:
        utDate = dt.strptime(cfg.get("_UT_", "workdate"), "%Y-%m-%d")
        logger.info("Using date: {}".format(utDate))
    except:
        pass

    for token in tokens:
        logger.info("Using Gesto token: {}".format(token))
        startDate = utDate if utDate else dt.today()
        logger.info("Using start date: {}".format(startDate))

        try:
            gestoData = getGestoReceptie(
                    baseURL = cfg.get("gesto", "url"),
                    token = token,
                    startDate = startDate
                    )["data"]
            if util.isArray(gestoData) and len(gestoData) >= 1:
                work2(winmentor, gestoData, cfg.get("winmentor", "cui"))

        except Exception as e:
            logger.exception(repr(e))

    # Send mail with new products and partners
    try:
        newProducts = winmentor.getNewProducts()
        if len(newProducts) != 0:
            txtMail = ""
            for prod in newProducts:
                for tag, val in prod.iteritems():
                    txtMail += "{}: {}\n".format(tag, val)
                txtMail += "-" * 20 + "\n"
            logger.debug("Text email: \n%s", txtMail)
            send_email(
                    subject = "Produs(e) noi in WinMentor",
                    msg = txtMail,
                    toEmails = toEmails
                    )

        newPartners = winmentor.getNewPartners()
        if len(newPartners) != 0:
            txtMail = ""
            for partner in newPartners:
                for tag, val in partner.iteritems():
                    txtMail += "{}: {}\n".format(tag, val)
                txtMail += "-" * 20 + "\n"
            logger.debug("Text email: \n%s", txtMail)
            send_email(
                    subject = "Partener(i) noi in WinMentor",
                    msg = txtMail,
                    toEmails = toEmails
                    )

    except Exception as e:
        logger.error("Failed to send email")
        logger.exception(repr(e))


    logger.info("END")