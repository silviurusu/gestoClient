'''
Facade (wrapper) for WinMentor OLE wrapper

@date 20/09/2017
@author Radu Cucu
'''


import pythoncom, win32com.client
from datetime import timedelta
import datetime
import logging
import util
import os
import re
import signal
import json
from util import send_email
from django.template import loader
import decorators
import math
from decimal import Decimal, ROUND_HALF_UP
from pywintypes import com_error
import settings


class LunaInchisa(Exception):
    """WinMentor nu accepta documente in luna ceruta; documentul ramane de transmis."""

    def __init__(self, companyName, opDate):
        self.companyName = companyName
        self.luna = f"{opDate:%m.%Y}"
        super().__init__(f"Luna {self.luna} este inchisa in WinMentor la {companyName}, documentele raman de transmis pana la deschiderea lunii")


class WinMentor(object):
    ''' classdocs
    '''

    companyName = None
    logOn = util.getCfgVal("winmentor", "userName")

    multiplePartenerIDs = {}
    multiplePartenerIDsForEmail = []
    parteneri = None
    products = None
    gestiuni = None
    intrari = {}
    transfers = {}

    productCodesBauturi = [[1005, 1006], [700, 728], [731, 798],]
    productCodesSdwSalate = [[799, 882], [1100, 1150],]

    missingCodes = {}
    missingDefaultGest = {}
    productsMissingWMCodes =[]
    missingWMCodes = {}


    @staticmethod
    def docImpServerStartedAt():
        """Cand a pornit cel mai vechi DocImpServer.exe, sau None daca nu ruleaza niciunul.

        Momentul spune cat de vechi e importul blocat, ceea ce e singura informatie utila
        in notificare: cateva secunde inseamna o rulare normala in curs, ore inseamna blocaj.

        Instantele blocate se aduna - bucla per firma porneste cate una pe firma - iar cea
        mai veche masoara blocajul cel mai lung, deci pe ea o raportam."""
        started = [
            util.wmi_creation_datetime(proc.CreationDate)
            for proc in win32com.client.GetObject('winmgmts:').InstancesOf('win32_process')
            if proc.Name == "DocImpServer.exe"
        ]

        return min(started) if started else None


    @staticmethod
    def killOrphanDocImpServers():
        """Opreste instantele DocImpServer.exe ramase in urma unui run care s-a incheiat.

        Serverul COM nu se inchide cand clientul iese - nici macar dupa un export reusit -
        iar de atunci garda de mai sus vede un import "in curs" si opreste orice rulare,
        la infinit, pana intervine cineva.

        Orfan inseamna doua lucruri deodata: procesul e in sesiunea noastra, ca sa nu atingem
        importurile pornite manual din Mentor.exe (acelea traiesc in sesiunea utilizatorului,
        noi in sesiunea 0), si nu mai exista niciun alt main.py care l-ar putea folosi. Cand
        nu putem stabili amandoua, nu oprim nimic: un export intarziat cu cinci minute e mai
        ieftin decat un import taiat la mijloc.

        Intoarce cate instante au fost oprite."""
        logger = logging.getLogger(__name__)

        try:
            procs = list(win32com.client.GetObject('winmgmts:').InstancesOf('win32_process'))
        except com_error as e:
            logger.warning(f"nu pot enumera procesele, las DocImpServer in pace: {e}")
            return 0

        pid = os.getpid()
        session = next((proc.SessionId for proc in procs if proc.ProcessId == pid), None)

        if session is None:
            logger.warning("nu-mi gasesc propriul proces in WMI, las DocImpServer in pace")
            return 0

        servers = [
            proc for proc in procs
            if proc.Name == "DocImpServer.exe" and proc.SessionId == session
        ]

        if not servers:
            return 0

        # un alt main.py inseamna ca serverele sunt ale lui: le foloseste sau tocmai le porneste
        exports = [
            proc.ProcessId for proc in procs
            if proc.ProcessId != pid
            and proc.Name.lower().startswith("python")
            and "main.py" in (proc.CommandLine or "")
        ]

        if exports:
            logger.info(f"main.py mai ruleaza in {exports}, DocImpServer nu e orfan")
            return 0

        killed = 0

        for proc in servers:
            started = util.wmi_creation_datetime(proc.CreationDate)

            try:
                # win32com rezolva Terminate din WMI ca proprietate, deci proc.Terminate()
                # l-ar executa la accesarea atributului si abia apoi ar crapa apeland int-ul
                # intors; os.kill e TerminateProcess pe Windows, fara ambiguitatea asta
                os.kill(proc.ProcessId, signal.SIGTERM)
            except OSError as e:
                logger.warning(f"DocImpServer orfan {proc.ProcessId}: nu l-am putut opri: {e}")
                continue

            logger.info(f"DocImpServer orfan {proc.ProcessId}, pornit {started:%d.%m %H:%M}, oprit")
            killed += 1

        return killed


    def __init__(self, **kwargs):
        self.logger = logging.getLogger(__name__)

        self._fdm = pythoncom.LoadTypeLib('DocImpServer.tlb')
        self._stat = None

        if self._fdm is None:
            return

        for idx in range(0, self._fdm.GetTypeInfoCount()):
            fdoc = self._fdm.GetDocumentation(idx)

            if fdoc[0] == 'DocImpObject':
                type_iid = self._fdm.GetTypeInfo(idx).GetTypeAttr().iid
                self.logger.info("Before Dispatch()")
                self._stat = win32com.client.Dispatch(type_iid)
                self.logger.info("After Dispatch()")

        if self._stat is None:
            return

        # seteaza firma de lucru
        company_cfg = kwargs.get("company")
        self.setFirmaLucru(company_cfg["firma"])

        self.companyName = company_cfg["companyName"]

        # Seteaza luna lucru
        self.an = kwargs.get("an")
        self.logger.info("an: {}".format(self.an))
        self.luna = kwargs.get("luna")
        self.logger.info("luna: {}".format(self.luna))

        if self.an and self.luna:
            if not self.setLunaLucru(self.an, self.luna):
                1/0

        # TODO check this values ...
        self._stat.SetIDPartField('CodFiscal')
        # self._stat.SetIDPartField('CodIntern')
        if self.companyName in ["SC Pan Partener Spedition Arg SRL", ]:
            self._stat.SetIDArtField('CodIntern')
        else:
            self._stat.SetIDArtField('CodExtern')

        self._newProducts = []
        self.missingPartners = {}
        self.missingCodes = {}
        self.missingDefaultGest = {}
        self.productsMissingWMCodes =[]
        self.missingWMCodes = {}
        self.allowMissingDefaultGest = util.getCfgVal("products", "allowMissingDefaultGest")


    def close(self):
        """Elibereaza referinta COM catre DocImpServer.exe al firmei.

        Fara ea serverul traieste pana la iesirea procesului - si uneori si dupa, fiindca la
        teardown-ul interpretorului ordinea de eliberare nu mai e a noastra. Chemata aici,
        eliberarea se intampla cat timp procesul e inca sanatos, deci serverul chiar apuca
        sa vada ca n-a mai ramas nimeni pe el.

        Dupa close() instanta nu mai e buna de nimic; companyName ramane, ca mesajele de
        eroare de dupa sa mai poata spune despre ce firma vorbesc."""
        self._stat = None
        self._fdm = None


    def isDrink(self, productCode):
        for p in self.productCodesBauturi:
            if productCode >= p[0] and productCode <= p[1]:
                return True

        return False


    def isSdwSalad(self, productCode):
        for p in self.productCodesSdwSalate:
            if productCode >= p[0] and productCode <= p[1]:
                return True

        return False


    def getListaErori(self):
        if self._stat is None:
            return (u'Nu am comunicare cu obiectul COM', )
        return self._stat.GetListaErori()


    def getListaFirme(self):
        if self._stat is None:
            return None
        return self._stat.GetListaFirme()


    def setFirmaLucru(self, firma):
        self.firma = firma
        if self._stat is None:
            return

        rc = self._stat.SetNumeFirma(self.firma)
        self.logger.info(f"SetNumeFirma rc = {rc}")
        if rc != 1:
            self.logger.error(repr(self.getListaErori()))
            1/0



    @decorators.time_log
    def setLunaLucru(self, an=2024, luna=12):
        self.luna = luna
        self.an = an

        if self._stat is None:
            return False

        rc = self._stat.SetLunaLucru(self.an, self.luna)
        if (rc != 1):
            errors = self.getListaErori()
            self.logger.info("Nu pot seta luna de lucru")
            self.logger.error(errors)

            return False

        return True


    def setLunaLucruPentruExport(self, opDate, document):
        """Ca setLunaLucru, dar un document de export nu se pierde: luna inchisa ridica LunaInchisa."""
        if not self.setLunaLucru(opDate.year, opDate.month):
            self.logger.info(f"{document} din {opDate:%d.%m.%Y} ramane de transmis")
            raise LunaInchisa(self.companyName, opDate)


    def _colonListToDict(self, keys, myStr):
        ''' Generate a dict from a list of keys and a color-separated string
        '''
        myDict = {}

        strData = myStr.split(';')
        count = min(len(strData), len(keys))
        for i in range(0, count):
            vals = strData[i].split("~")
            if len(vals) == 1:
                myDict[keys[i]] = vals[0]
            elif len(vals) > 1:
                myDict[keys[i]] = vals

        return myDict


    @decorators.time_log
    def productsAreOK(self, gestoData):
        ret = True

        for item in gestoData["items"]:
            if item["winMentorCode"] == "nil" \
            or item["winMentorCode"] == "":
                ret = False
                if item["code"] not in self.missingCodes:
                    # only add a code once
                    self.missingCodes[item["code"]] = item
            elif not self.productExists(item["winMentorCode"]):
                ret = False
                if item["winMentorCode"] not in self.missingWMCodes:
                    details_arr = []
                    self.logger.info("code: {}, missing".format(item["code"]))

                    # only add a code once
                    if "operationDateHuman" in gestoData:
                        dateHuman = gestoData["operationDateHuman"]
                    elif "dateBeginHuman" in gestoData:
                        dateHuman = gestoData["dateBeginHuman"][:10]

                    details_arr.append(dateHuman)
                    details_arr.append(gestoData["branch"])

                    if "source" in gestoData:
                        details_arr.append(gestoData["source"]["name"])
                    if "relatedDocumentNo" in gestoData:
                        details_arr.append(gestoData["relatedDocumentNo"])
                    if "documentNo" in gestoData:
                        details_arr.append(gestoData["documentNo"])

                    # self.logger.info(f"{details_arr=}")

                    details = " - ".join([str(d) for d in details_arr if d not in [None, "nil", ""]])

                    self.missingWMCodes[item["code"]] = {
                            "item": item,
                            "details": details
                        }

            elif self.companyName not in ["SC Pan Partener Spedition Arg SRL", 'S.C. Kattana Black SRL'] \
                    and self.getProduct(item["winMentorCode"])["GestImplicita"] == "" \
                    and item["winMentorCode"] not in self.allowMissingDefaultGest:
                ret = False
                if item["code"] not in self.missingDefaultGest:
                    # only add a code once
                    self.missingDefaultGest[item["code"]] = item

        self.logger.info("ret: {}".format(ret))

        return ret


    def getListaParteneri(self):
        keys = (
                "idPartener",
                "denumire",
                "codFiscal",
                "localitate",
                "adresa",
                "telefon",
                "persoaneContact",
                "simbolClasa",
                "clasa",
                "simbolCategoriePret",
                "denumireCategoriePret",
                "marcaAgent",
                "numeAgent",
                "prenumeAgent",
                "scadenta",
                "discount",
                "localitateSediu",
                "CodExtern",
                "partenerBlocat",
                "creditLaVanzare",
                "codFiscal",
                "contBanca",
                "localitateSediu",
                "tara",
                "agentSediuSecundar"
                )

        lista, rc = self._stat.GetListaParteneri()
        if rc != 0:
            return None

        parteneri = []
        for idx, partenerStr in enumerate(lista):
            self.logger.debug(f"{idx} -- {partenerStr}")
            parteneri.append(self._colonListToDict(keys, partenerStr))

        self.multiplePartenerIDs = {}
        retParteneri = {}
        for p in parteneri:
            id = util.fixupCUI(p["idPartener"])
            # self.logger.debug("{} - {} ".format(p["idPartener"], id))

            if (id in ['12106375', 12106375]
                and p['denumire'] not in ['DADDA COMPUTER 2000 SRL DEPOZITELOR 22 C']
            ):
                continue

            if id in retParteneri:
                if id in ["6287579", 6287579]:
                    # matra apare de mai multe ori
                    continue

                if id not in self.multiplePartenerIDs:
                    self.multiplePartenerIDs[id] = p
            else:
                retParteneri[id] = p

        self.logger.debug("partners count: {}".format(len(retParteneri)))
        # self.logger.debug("partners : {}".format(retParteneri))

        self.parteneri = retParteneri


    def getNomenclatorArticole(self):
        keys = (
            "CodExternIntern",
            "Denumire",
            "DenUM",
            "PretVanzare",
            "SimbolClasa",
            "DenClasa",
            "CodExternInternProducator",
            "Den.Producator",
            "GestImplicita",
            "CodExtern",
            "CotaTVA",
            "DenUMSecundaraImplicita",
            "ParitateUMSecundaraImplicita",
            "Masa",
            "Serviciu",
            "CodVamal",
            "PretMinim",
            "CantImplicita",
            "PretValuta",
            "DataAdaug",
            "Masa",
            "PretVCuTVA",
            "Locatie",
            "PretReferinta"
        )

        lista, rc = self._stat.GetNomenclatorArticole()
        if rc != 0:
            msg = self.getListaErori()
            msg = repr(msg)
            self.logger.info(msg)
            send_email(
                    subject = "WinMentor - GetNomenclatorArticole eroare",
                    msg = msg
                    )
            1/0
            return None

        products = []
        for idx, prodStr in enumerate(lista):
            self.logger.info(prodStr)
            products.append(self._colonListToDict(keys, prodStr))

        ret = { p["CodExternIntern"] : p for p in products }
        self.logger.debug("products count: {}".format(len(ret)))

        self.products = ret
        # self.logger.info(f"products: {products}")


    def getProducts(self):
        if self.products is None:
            self.getNomenclatorArticole()

        return self.products


    def getProduct(self, id):
        if self.products is None:
            self.getNomenclatorArticole()

        return self.products[id]


    @decorators.time_log
    def partenerExists(self, partenerID):
        if self.parteneri is None:
            self.getListaParteneri()

        if partenerID not in self.parteneri:
            ret = False
        else:
            ret = True

        self.logger.info("ret: {}".format(ret))

        return ret


    @decorators.time_log
    def getPartener(self, partenerID):
        if self.parteneri is None:
            self.getListaParteneri()

        if partenerID not in self.parteneri:
            ret = None
        else:
            ret = self.parteneri[partenerID]

        self.logger.info("ret: {}".format(ret))

        return ret


    @decorators.time_log
    def transferExists(self, nrDoc, documentDate):
        """ @return daca transferul exista sau nu in Mentor
        """

        workDate = documentDate.strftime("%d.%m.%Y")

        # make sure we have loaded the existing transfers for the day
        if workDate not in self.transfers:
            self.transfers[workDate] = []

            # self._stat.SetTipFiltruTransferuri(1)
            transferuri, rc = self._stat.GetTransferuri()

            if rc != 0:
                self.logger.error(repr(self.getListaErori()))

            for item in transferuri:
                self.logger.info(item)
                items = item.split(";")
                if items[2] not in self.transfers[workDate]:
                    self.transfers[workDate].append(items[2])

            self.logger.info("{} transferuri pe {}".format(len(self.transfers[workDate]), workDate))
            self.logger.info(self.transfers[workDate])
            # 1/0

        self.logger.info(f"{nrDoc=}")

        if str(nrDoc) not in self.transfers[workDate]:
            self.logger.info("Transferul nu exista in WinMentor")

            ret = False
        else:
            self.logger.info("Transferul este adaugat deja")
            ret = True

        return ret


    def productExists(self, code):
        if self.products is None:
            self.getNomenclatorArticole()

        if code not in self.products:
            return False
        else:
            return True


    def _dictToColonList(self, keys, args, separator = ";", forceAbs = False):
        pd = []
        for key in keys:
            val = args.get(key, "") if isinstance(args, dict) else args[key]
            if isinstance(val, list):
                # It's an iterable type (ex: array, tuple), iterate it and separate with "~"
                nKeys = range(len(val))
                val = self._dictToColonList(nKeys, val, "~")
            elif isinstance(val, datetime.datetime):
                val = "{:%d.%m.%Y}".format(val)

            elif isinstance(val, float):
                if forceAbs:
                    val = math.fabs(val)

                val = "{:f}".format(val)
            else:
                val = str(val)
            pd.append(val)

        return(separator.join(pd))


    def importaFactIntrare(self, **kwargs):
        '''
        @param items: array produse; fiecare produs e un dict cu urmatoarele posibile chei:
            - codExternArticol
            - nrDoc
            - nrNir
            - um: unitate masura
            - cant
            - pret
            - data
            - dataNir
            - simbGest: simbol gestiune receptie
            - discount: discount linie
            - simbServ: simbol cont pt. articole de tip serviciu
            - pretInreg: pret inregistrare pentru articole ce au tip contabil implicit cu adaos
            - termenGarantie
            - logOn
            - simbolCarnet
        '''

        items = kwargs.get("items", [])

        # Header factura
        txtWMDoc = (
            "[InfoPachet]\n"
            "AnLucru={}\n"
            "LunaLucru={}\n"
            "TipDocument={}\n"
            "TotalFacturi={}\n"
            "LogOn={}\n"
            "\n"
            ).format(
                self.an,
                self.luna,
                "FACTURA INTRARE",
                1,
                self.logOn,
                )

        # Factura
        txtWMDoc += "[Factura_{}]\n".format(1)
        txtWMDoc += "Operatie=A\n"
        txtWMDoc += "SerieDoc={}\n".format(kwargs.get("serieDoc", ""))
        txtWMDoc += "NrDoc={}\n".format(kwargs.get("nrDoc", ""))
        if kwargs.get("nrNir"):
            txtWMDoc += "NrNIR={}\n".format(kwargs.get("nrNir"))
        if kwargs.get("simbolCarnet"):
            txtWMDoc += "SimbolCarnetNir={}\n".format(kwargs.get("simbolCarnet"))
        txtWMDoc += "Data={:%d.%m.%Y}\n".format(kwargs.get("data", datetime.datetime.now()))
        txtWMDoc += "DataNir={:%d.%m.%Y}\n".format(kwargs.get("dataNir", None))
        txtWMDoc += "Scadenta={:%d.%m.%Y}\n".format(kwargs.get("scadenta", datetime.datetime.now()))
        txtWMDoc += "TotalArticole={}\n".format(len(items))
        txtWMDoc += "CodFurnizor={}\n".format(kwargs.get("codFurnizor", ""))
        if kwargs.get("TVAINCASARE") is True:
            txtWMDoc += "TVAINCASARE={}\n".format("D")
        # txtWMDoc += "Majorari={}\n".format(kwargs.get("majorari", ""))
        if kwargs.get("Discount") is True:
            txtWMDoc += "Discount={:.4f}\n".format(kwargs.get("discount"))
        txtWMDoc += "Observatii={}\n".format(kwargs.get("observatii", ""))
        txtWMDoc += "ObservatiiNIR={}\n".format(kwargs.get("observatiiNIR", ""))

        # Adauga items in factura
        txtWMDoc += "\n[Items_{}]\n".format(1)
        keys = (
                "codExternArticol",
                "um",
                "cant",
                "opPrice",
                "simbGest",
                "discount",
                "simbServ",
                "listPrice",
                "termenGarantie"
                )

        tipContabil = kwargs.get("tipContabil", None)

        for idx, item in enumerate(items, start=1):
            txtProd = self._dictToColonList(keys, item)
            # txtProd += "TC_1314;"
            txtWMDoc += "Item_{}={}\n".format(idx, txtProd)
            if tipContabil is not None:
                txtWMDoc += f"Item_{idx}_TipContabil={tipContabil}\n"

        self.logger.debug("txtWMDoc: \n{}".format(txtWMDoc))

        fact = txtWMDoc.split("\n")

        self._stat.SetDocsData(fact)

        rc = self._stat.FactIntrareValida()
        if rc != 1:
            return False

        try:
            rc = self._stat.ImportaFactIntrare()
        except com_error as e:
            exp_repr = repr(e)

            self.logger.info(exp_repr)

            msg = f"Exceptie la {self.companyName}"

            if util.report_problem(msg, exp_repr, hours=2, emails=["silviu@vectron.ro", ]):
                send_email(msg, msg, toEmails=util.getCfgVal("client", "notificationEmails"), location=False)

            return False

        return (rc == 1)


    def addProduct(self, **kwargs):
        keys = (
                "idArticol",
                "denumire",
                "idProducator",
                "_",
                "um",
                "denProducator",
                "cotaTVA",
                "atributStoc",
                "dataUltimeiModificari",
                "codIntern",
                "simbolClasa",
                "_",
                "_",
                "_",
                "pret"
                )
        self.logger.info("Articol nou:\n"
                "- idArticol: {}\n"
                "- denumire: {}\n".format(
                    kwargs.get("idArticol", "-"),
                    kwargs.get("denumire", "-")
                    )
                )

        prodTxt = self._dictToColonList(keys, kwargs)
        self.logger.debug("prodTxt = {}".format(prodTxt))

        rc = self._stat.AddProduct(prodTxt)

        if rc == 1:
            # Add to new products array:
            self._newProducts.append(
                    { key: kwargs.get(key, "-") for key in keys if key != "_" }
                    )

        # Get again lista articole
        self.getNomenclatorArticole()

        return (rc == 1)

    @decorators.time_log
    def addPartener(self, **kwargs):
        keys = (
                "codFiscal",
                "denumirePartener",
                "idPartener",
                "localitateSediu",
                "adresaSediu",
                "telefonSediu",
                "persoaneContact",
                "simbolClasa",
                "simbolCategoriePret",
                "idAgentImplicit",
                "nrRegistrulComert",
                "observatii",
                "simbolBanca",
                "numeBanca",
                "localitateBanca",
                "contBanca",
                "ziImplicitaPlata",
                "numeSediuSecundar",
                "adresaSediuSecundar",
                "telefonSediuSecundar",
                "localitateSediuSecundar",
                "idAgentSediuSecundar"
                )

        self.logger.info("Adauga partener: \n"
                 "- codFiscal: {}\n"
                 "- denumire: {}\n"
                 "- idPartener: {}".format(
                     kwargs.get("codFiscal", "-"),
                     kwargs.get("denumirePartener", "-"),
                     kwargs.get("idPartener", "-")
                     )
                 )

        partenerTxt = self._dictToColonList(keys, kwargs)
        self.logger.debug("partenerTxt = {}".format(partenerTxt))

        rc = self._stat.AdaugaPartener(partenerTxt)
        if rc:
            # Add to new partners array:
            self.missingPartners.append(
                    { key: kwargs.get(key, "-") for key in keys if key != "_" }
                    )

            # Get again lista parteneri
            self.getListaParteneri()
        else:
            self.logger.error(repr(self.getListaErori()))
            1/0

        return None


    @decorators.time_log
    def existaFacturaIntrare(self, partenerId, serie, nr):
        serii = [serie, '', ]
        for s in serii:
            self.logger.info("testing {} {} {}".format(partenerId, s, nr))

            ret = self._stat.ExistaFacturaIntrare(partenerId, s, nr)
            if ret == 1:
                break

        if ret == 1:
            self.logger.info("Factura exista")
        else:
            self.logger.info("Factura NU exista")

        return ret


    @decorators.time_log
    def getFactura(self, partenerId, serie, nr, data):
        """ @return array de articole from Winmentor care corespund facturii

        """

        if not self.existaFacturaIntrare(partenerId, serie, nr):
            return None

        # make sure we have loaded the existing intrari
        month = data.strftime("%m")
        self.getIntrari(month)

        # Format parameters to string
        data = data.strftime("%d.%m.%Y")
        nr = str(int(nr)) # if I have doc nrs that start with 0
        partenerId = str(partenerId)

        if data not in self.intrari[month][partenerId]:
            ret = -1
        elif nr not in self.intrari[month][partenerId][data]:
            ret = -1
        else:
            ret = self.intrari[month][partenerId][data][nr]
            self.logger.info(json.dumps(
                            ret,
                            sort_keys=True, indent=4, separators=(',', ': '), default=util.defaultJSON))

        return ret


    @decorators.time_log
    def getGestiuni(self):
        if self.gestiuni is None:
            gestiuni, rc = self._stat.GetListaGestiuni()
            self.gestiuni = {}
            if (rc == 0) and isinstance(gestiuni, tuple):
                # keys = (
                #     "simbol",
                #     "denumire"
                #     )
                # for gestiune in gestiuni:
                #     self.gestiuni.append(self._colonListToDict(keys, gestiune))

                for gestiune in gestiuni:
                    strData = gestiune.split(';')
                    if strData[0] != "":
                        self.gestiuni[strData[0]] = strData[1]
            else:
                self.logger.debug("rc = {}".format(rc))
                self.logger.error(repr(self.getListaErori()))

        # self.logger.info(self.gestiuni)

        return self.gestiuni


    @decorators.time_log
    def getIntrari(self, month):
        if month not in self.intrari:
            self.intrari[month]={}
            # Salveaza toate intrarile pentru factura respectiva
            keys = (
                   "partenerId",
                   "data",
                   "nrDoc",
                   "idArticol",
                   "cant", # cantitate
                   "um",
                   "pret",
                   "simbGest",
                   "_"
                    )

            intrariItems, rc = self._stat.GetIntrari()

            if (rc == 0) and isinstance(intrariItems, tuple):
                # self.logger.info(intrariItems)
                # 1/0

                for idx, item in enumerate(intrariItems):
                    self.logger.info(f"{idx} -- {item}")
                    val = self._colonListToDict(keys, item)
                    # 1/0
                    if val["partenerId"] not in self.intrari[month]:
                        self.intrari[month][val["partenerId"]]={}
                    if val["data"] not in self.intrari[month][val["partenerId"]]:
                        self.intrari[month][val["partenerId"]][val["data"]]={}
                    if val["nrDoc"] not in self.intrari[month][val["partenerId"]][val["data"]]:
                        self.intrari[month][val["partenerId"]][val["data"]][val["nrDoc"]]=[]

                    self.intrari[month][val["partenerId"]][val["data"]][val["nrDoc"]].append(val)
                    # self.logger.info(self.intrari)
                    # 1/0
            else:
                self.logger.debug("rc = {}".format(rc))
                self.logger.error(repr(self.getListaErori()))

        # self.logger.info(self.intrari)
        # 1/0


    @decorators.time_log
    def getGestiuneName(self, simbol):
        # make sure we have loaded gestiunile
        self.getGestiuni()

        return self.gestiuni[simbol]


    def sendNewProductsMail(self):
        if len(self._newProducts) != 0:
            txtMail = ""
            for prod in self._newProducts:
                for tag, val in prod.iteritems():
                    txtMail += "{}: {}\n".format(tag, val)
                txtMail += "-" * 20 + "\n"
            send_email(
                    subject = "Produs(e) noi in WinMentor",
                    msg = txtMail
                    )

    def sendIncorrectWinMentorProductsMail(self):
        if len(self.missingCodes) \
        or len(self.missingDefaultGest) \
        or len(self.missingWMCodes) \
        or len(self.productsMissingWMCodes):
            template = loader.get_template("mail/admin/incorrectWinMentorProducts.html")
            subject = "{} produse cu probleme in WinMentor".format(len(self.missingCodes)
                                                                     + len(self.missingDefaultGest)
                                                                     + len(self.productsMissingWMCodes)
                                                                     + len(self.missingWMCodes)
                                                                     )
            html_part = template.render({
                "subject": subject,
                "missingCodes": self.missingCodes,
                "missingDefaultGest": self.missingDefaultGest,
                "productsMissingWMCodes": self.productsMissingWMCodes,
                "missingWMCodes": self.missingWMCodes,
            })

            util.report_problem(subject, html_part, hours=2, emails=util.getCfgVal("client", "notificationEmails"))


    def sendPartnersMail(self):
        if len(self.missingPartners) != 0 or len(self.multiplePartenerIDsForEmail)!=0:
            template = loader.get_template("mail/admin/WinMentorPartenersProblems.html")
            subject = "Probleme la parteneri in WinMentor"
            html_part = template.render({
                "subject": subject,
                "missingPartners": self.missingPartners,
                "multiplePartenerIDsForEmail": self.multiplePartenerIDsForEmail,
            })

            if util.report_problem(subject, html_part, hours=2):
                send_email(subject, html_part, toEmails=util.getCfgVal("client", "notificationEmails"), location=False)


    def genNrNir(self):
        """ Genereaza nr NIR pentru o factura noua

        """

        # rc = self._stat.GetNumarFactura("Note de receptie 2011")

        return "672267"
        # return rc


    @decorators.time_log
    def matchGestiune(self, name, tipGestiune=None):
        """
        @param name: Nume destinatie din Gesto
        @param listaGestiuni: Lista gestiuni din WinMentor

        """

        ret = None

        # Get gestiuni
        gestiuni = self.getGestiuni()
        # self.logger.debug("gestiuni: {}".format(gestiuni))

        simbolGestiuneSearch = name
        # simbolGestiuneSearch = "SEDIU"

        if self.companyName != "SC Pan Partener Spedition Arg SRL":
            matchStr = '^\\s*([0-9]{1,4})\\s*' #+"{}".format(tipGestiune)
            x = re.match(matchStr, name)
            if x:
                no = x.group(1)
                self.logger.debug(repr(no))

                # Find a "gestiune" that matches
                simbolGestiuneSearch = "Magazin {:d}P".format(int(no))

        self.logger.debug("simbolGestiuneSearch: {}".format(simbolGestiuneSearch))

        for gestiune in gestiuni:
            # regex = r"^\\s*" + re.escape(no) + "\\s*Magazin"
            # found = re.match(regex, gestiune["simbol"], re.IGNORECASE)
            # if found:
            #     result.append(gestiune)
            # self.logger.debug("gestiune: {}".format(gestiune))
            if simbolGestiuneSearch == gestiune:
                ret = gestiune
                break

        if ret is None:
            txtMail = "Gestiunile din WinMentor:\n"
            txtMail += repr(self.gestiuni)

            send_email(
                    subject = "WinMentor - nu am gasit gestiunea >{}< - >{}<".format(simbolGestiuneSearch, name),
                    msg = txtMail
                    )

            1/0

        self.logger.info("ret: {}".format(ret))

        return ret


    @decorators.time_log
    def addReception(self, gestoData):
        if gestoData["relatedDocumentNo"] == "nil":
            msg = "Factura {}, {} nu are document de legatura.".format(gestoData["documentNo"], gestoData["destination"]["name"])
            subject = msg

            send_email(subject, msg, toEmails=util.getCfgVal("client", "notificationEmails"), location=False)

            self.logger.error(msg)
            return False

        # eliminate strings at begin and end of relatedDocumentNo, fvz123, FCT-312
        rdnFormats = [
                {"f":'^([^0-9]*)([0-9]*)([^0-9]*)$', "i": 1},
                {"f":'^([^-]*)(-)(.*)$', "i": 2},
                {"f": '.* (\\d+)$', 'i': 0},
                {"f": '.*?(\\d+)$', 'i': 0}

            ]

        found = False
        for rdnf in rdnFormats:
            try:
                gestoData["relatedDocumentNo"] = re.match(rdnf["f"], gestoData["relatedDocumentNo"]).groups()
                gestoData["relatedDocumentNo"] = gestoData["relatedDocumentNo"][rdnf["i"]]
                gestoData["relatedDocumentNo"] = gestoData["relatedDocumentNo"][-9:]
                gestoData["relatedDocumentNo"] = str(int(gestoData["relatedDocumentNo"]))
                found = True
                break
            except (AttributeError, ValueError):
                pass

        if not found:
            subject = "Nu pot determina numarul facturii din: {}, {}".format(gestoData["relatedDocumentNo"], gestoData["destination"]["name"])
            msg = "Data: {}".format(gestoData["documentDateHuman"])
            msg += "\nLocatie: {}".format(gestoData["destination"]["name"])
            msg += "\nNumarul: {}".format(gestoData["relatedDocumentNo"])

            if util.report_problem(subject, msg, hours=1):
                send_email(subject, msg, toEmails=util.getCfgVal("client", "notificationEmails"), location=False)

            self.logger.error(msg)
            return False

        self.logger.info("relatedDocumentNo: {}".format(gestoData["relatedDocumentNo"]))

        # verify I have all gesto codes and defalut gestiuni in WinMentor
        if not self.productsAreOK(gestoData):
            self.logger.info("Factura are articole cu coduri nesetate sau gestiuni lipsa, nu adaug")
            return False

        # # Get gestiuni
        # gestiune = self.getGestiune(gestoData["simbolWinMentor"])

        # Get partener from gesto
        gestoPartener = util.fixupCUI(gestoData["source"]["code"])
        if gestoPartener == '':
            gestoPartener = util.fixupCUI(gestoData["source"]["ro"])
        self.logger.info("gestoPartener = {}".format(gestoPartener))

        if gestoPartener in self.multiplePartenerIDs:
            self.multiplePartenerIDsForEmail.append(gestoPartener)

            self.logger.info(f"Codul fiscal: {gestoPartener} apare de mai multe la parteneri, nu adaug")
            return False

        # Seteaza luna si anul in WinMentor
        opDate = datetime.datetime.fromtimestamp(gestoData["documentDate"])
        if not self.setLunaLucru(opDate.year, opDate.month):
            return False

        # Cod partener exact ca in Winmentor
        if not self.partenerExists(gestoPartener):
            if gestoData["source"]["code"] not in self.missingPartners:
                # only add a missing partener once
                self.missingPartners[gestoData["source"]["code"]] = gestoData["source"]

            self.logger.info("Partenerul {} de pe receptia gesto nu exista, nu adaug".format(gestoPartener))
            return False

            # self.addPartener(
            #         codFiscal = gestoPartener,
            #         denumirePartener = gestoData["source"]["name"]
            #         )

            # if not self.partenerExists(gestoPartener):
            #     self.logger.error("Failed to add new partener correcly.")
            #     return False

        wmPartenerID = self.getPartener(gestoPartener)["idPartener"]
        scadenta = opDate

        if 'invoice_due_days' in gestoData["source"] \
           and gestoData["source"]["invoice_due_days"] not in [None, '', 'nil', 'None', 0]:
            scadenta += timedelta(days = gestoData["source"]["invoice_due_days"])
        else:
            scadenta += timedelta(days = 1)

        self.logger.info("wmPartenerID: {}".format(wmPartenerID))

        # Cauta daca exista deja o factura in Winmentor cu intrarea din gesto
        alreadyAdded = False
        lstArt = self.getFactura(
                partenerId = wmPartenerID,
                serie = "G",
                nr = gestoData["relatedDocumentNo"],
                data = opDate
                )

        if lstArt == -1:
            self.logger.info("Factura are data modificata")
            return False

        self.logger.info(lstArt)

        if lstArt and (len(lstArt) != 0):
            self.logger.info("Gasit intrare in winmentor.")
            if len(lstArt) != len(gestoData["items"]):
                msg = "Lista de produse din Gesto e diferita de cea din WinMentor"

                subject = "Factura {} importata incorect in Winmentor".format(gestoData["documentNo"])
                msg += "\nwmPartenerID:{}, documentNo:{}, relatedDocumentNo:{}".format(wmPartenerID, gestoData["documentNo"], gestoData["relatedDocumentNo"])

                if util.report_problem(subject, msg, hours=2):
                    send_email(subject, msg)

                self.logger.error(msg)
                self.logger.info(f"mentor {len(lstArt)} != gesto {len(gestoData['items'])}")

                return False
            else:
                # Verifica toate produsele din factura daca corespund cu cele din gesto
                alreadyAdded = True

                for artWm in lstArt:
                    wmCode = artWm["idArticol"]
                    # Remove "G_" prefix, if any
                    # wmCode = wmCode[len("G_"):] if wmCode.startswith("G_") else wmCode

                    # Search for article from winmentor in gesto array
                    artGesto = None
                    for a in gestoData["items"]:
                        if wmCode == a["winMentorCode"]:
                            artGesto = a["winMentorCode"]
                            break

                    if artGesto is None:
                        self.logger.error("Product [%s] from winmentor reception not found in gesto reception", wmCode)
                        alreadyAdded = False
                        break

        if alreadyAdded:
            self.logger.info("Factura e deja adaugata")
            return True

        # Get lista articole from gesto, create array of articole pentru factura
        articoleWMDoc = []
        observatii = ""

        for item in gestoData["items"]:
            wmArticol = self.getProduct(item["winMentorCode"])
            # self.logger.info("wmArticol: {}".format(wmArticol))

            if self.companyName == "SC Pan Partener Spedition Arg SRL":
                simbGest = f"MAG_{gestoData['simbolWinMentorDeliveryNote']}"
            else:
                simbGest = wmArticol["GestImplicita"]

            # Adauga produs la lista produse factura
            articoleWMDoc.append(
                    {
                        "codExternArticol": item["winMentorCode"],
                        "um": wmArticol["DenUM"],
                        "cant": item["qty"],
                        "listPrice": item["listPrice"],
                        "opPrice": item["opPrice"],
                        # "simbGest": gestoData["simbolWinMentor"]
                        "simbGest": simbGest
                        }
                    )

            if item["winMentorCode"].startswith("G_MARF"):
                observatii += item["name"]+"; "

        if self.companyName == "SC Pan Partener Spedition Arg SRL":
            observatii = gestoData["destination"]["name"]
            tipContabil = f"TC_{gestoData['simbolWinMentorDeliveryNote']}"
        else:
            tipContabil = None

        # Creaza factura import
        rc = self.importaFactIntrare(
                serieDoc="G",
                nrDoc = gestoData["relatedDocumentNo"],
                nrNir = util.getNextDocumentNumber("NIR_G"),
                simbolCarnet="NIR_G",
                data = opDate,
                dataNir = datetime.datetime.fromtimestamp(gestoData["relatedDocumentDate"]) if gestoData["relatedDocumentDate"] not in ("nil", None) else opDate,
                scadenta = scadenta,
                codFurnizor = wmPartenerID,
                observatii= observatii,
                observatiiNIR=gestoData["destination"]["name"],
                items = articoleWMDoc,
                tipContabil = tipContabil
                )
        if rc:
            self.logger.info("SUCCESS: Adaugare factura")

            return True
        else:
            errors = self.getListaErori()
            self.logger.error(errors)

            self.logger.info("EROARE: Probleme la  adaugarea facturii")
            return False


    @decorators.time_log
    def addWorkOrderFromOperation(self, gestoData):
        if len(gestoData["items"]) == 0:
            self.logger.info("Nu am nici un produs pe operatie")
            return True

        # Seteaza luna si anul in WinMentor
        opDate = datetime.datetime.fromtimestamp(gestoData["documentDate"], datetime.UTC)

        if not self.setLunaLucru(opDate.year, opDate.month):
            return False

        if self.companyName == "Panemar morarit si panificatie SRL":
            nrDoc = int(gestoData["branch"][:2]) * 10000000 + gestoData["documentNo"]
        elif self.companyName == "SC Pan Partener Spedition Arg SRL":
            if gestoData["type"] == "return":
                nrDoc = util.getNextDocumentNumber("RETUR")
            else:
                nrDoc = int(gestoData["simbolWinMentorReception"]) * 10000000 + gestoData["documentNo"]
        else:
            nrDoc = int(gestoData["simbolWinMentorReception"]) * 10000000 + gestoData["documentNo"]

        self.logger.info("nrDoc: {}".format(nrDoc))

        if self.transferExists(nrDoc, opDate):
            return True

        ignoreCodes = []

        if self.companyName == "Panemar morarit si panificatie SRL":
            tipGest = self.getTipGest(gestoData, ignoreCodes)
            if tipGest == "Skip export":
                self.logger.info("Receptia contine dressing/masline/crema, nu trebuie preluata")
                return True
            elif tipGest is None:
                template = loader.get_template("mail/admin/incorrectProductTypeReception.html")
                if gestoData["type"] == "reception":
                    subject = "Receptia {} - {} cu probleme in WinMentor".format(gestoData["relatedDocumentNo"], gestoData["source"]["name"])
                elif gestoData["type"] == "notaConstatareDiferente":
                    subject = "Nota constatare diferente {} - {} cu probleme in WinMentor".format(gestoData["relatedDocumentNo"], gestoData["source"]["name"])
                elif gestoData["type"] == "return":
                    subject = "Returul {} - {} cu probleme in WinMentor".format(gestoData["documentNo"], gestoData["source"]["name"])
                html_part = template.render({
                    "subject": subject,
                    "gestoData": gestoData,
                    'HOME_URL': settings.HOME_URL,
                })

                util.send_email(subject, html_part, toEmails=util.getCfgVal("client", "notificationEmails"), location=False)

                return False
        else:
            tipGest = None

        # verify I have all gesto codes and default gestiuni in WinMentor
        if not self.productsAreOK(gestoData):
            self.logger.info("Articole cu coduri nesetate sau gestiuni lipsa, nu adaug")
            return False

        if self.companyName == "Panemar morarit si panificatie SRL":
            simbGest = self.matchGestiune(gestoData["source"]["name"], tipGest)
        elif self.companyName == "SC Pan Partener Spedition Arg SRL":
            if gestoData["type"] == "return":
                simbGest = f"MAG_{gestoData['simbolWinMentorDeliveryNote']}"
            else:
                if gestoData["source"]["name"] in ["TRANSP_MAGAZINE"]:
                    simbGest = "TR_MAG"
                else:
                    simbGest = f'MAG_{gestoData["source"]["simbolWinMentorDeliveryNote"]}'
        else:

            simbGest = self.matchGestiune(f"MAG_{gestoData['simbolWinMentorDeliveryNote']}")

        if simbGest is None:
            self.logger.info("Nu am gasit gestiunea")
            return False

        if gestoData["type"] == "return":
            # wmGestiune = "DMR"
            if self.companyName == "Panemar morarit si panificatie SRL":
                wmGestiune = "DMP"
            elif self.companyName == "Andalusia":
                wmGestiune = "PER"
            elif self.companyName == "SC Pan Partener Spedition Arg SRL":
                if gestoData["destination"]["name"] in ["BRUTARIE TRIVALE", "LABORATOR CREPITO TRIVALE"]:
                    wmGestiune = "RET_TRIV"
                else:
                    wmGestiune = "RETUR"
        elif gestoData["type"] == "notaConstatareDiferente":
            wmGestiune = "DepProdFinite"
        else:
            if self.companyName == "Panemar morarit si panificatie SRL":
                wmGestiune = self.matchGestiune(gestoData["branch"], tipGest)
            else:

                wmGestiune = self.matchGestiune(f"MAG_{gestoData['simbolWinMentorDeliveryNote']}")

        # Get lista articole from gesto, create array of articole pentru workOrders
        articoleWMDoc = []
        product_problems = False

        for item in gestoData["items"]:
            if int(item["code"]) in ignoreCodes:
                continue

            wmArticol = self.getProduct(item["winMentorCode"])
            self.logger.debug("wmArticol: \n{}".format(wmArticol))

            if self.companyName == "Panemar morarit si panificatie SRL":
                if item["productType_name"] == "Marfa":
                    codExternArticol = "G_MARF_{}_{}".format(item["vat"], gestoData["source"]["name"][:2])
                    pret = item["listPrice"]
                    um = "Lei"
                else:
                    codExternArticol = item["winMentorCode"]
                    um = wmArticol["DenUM"]
                    if tipGest == "MP":
                        pret = 0
                    else:
                        pret = wmArticol["PretVanzareFaraTVA"]
            else:
                codExternArticol = wmArticol["CodExternIntern"]
                um = wmArticol["DenUM"]

                if self.companyName in ["SC Pan Partener Spedition Arg SRL"]:
                    pret = item["listPrice"]
                else:
                    if gestoData["type"] == "return":
                        cheie_pret = "PretReferinta"
                    else:
                        cheie_pret = "PretVanzareFaraTVA"

                    pret = wmArticol[cheie_pret]

                if pret == "":
                    pret = item["listPrice"]

                    # product_problems = True
                    # if codExternArticol not in self.missingWMPrice:
                    #     self.missingWMPrice[codExternArticol] = {
                    #         "nume": item["name"],
                    #         "docs": []
                    #         }

                    #     self.missingWMPrice[codExternArticol]["docs"].append({
                    #         "gestoData": gestoData,
                    #         "cheie": cheie_pret
                    #     })

                    # return False

            articoleWMDoc.append({
                        "codExternArticol": codExternArticol,
                        "um": um,
                        "cant": item["qty"],
                        # "pret": item["listVal"]/item["qty"],
                        "pret": pret,
                        "simbGest": simbGest
                    })

        if product_problems:
            return False

        if gestoData["type"] == "return":
            simbolCarnet = "NTR_G"
        elif gestoData["type"] == "reception":
            simbolCarnet = "NTA_G"
        elif gestoData["type"] == "notaConstatareDiferente":
            simbolCarnet = "NTCD_G"
        else:
            1/0

        if self.companyName == "Panemar morarit si panificatie SRL":
            simbol_carnet_NIR = "GNIR"
            observatii = "{} - {}".format(gestoData["source"]["name"], gestoData["documentNo"])
        elif self.companyName == "SC Pan Partener Spedition Arg SRL":
            simbol_carnet_NIR = "NIR_G"

            if gestoData["type"] == "return":
                observatii = self.getGestiuneName(f"MAG_{gestoData['simbolWinMentorDeliveryNote']}")
                observatii = f'Retur {observatii} - {gestoData["documentNo"]}'
            else:
                observatii = self.gestiuni[wmGestiune]
                try:
                    observatii = f'{observatii} - {gestoData["source"]["address"]}'
                except KeyError:
                    pass
        else:
            simbol_carnet_NIR = "NIR_G"
            observatii = self.gestiuni[wmGestiune]

        # Creaza transferul
        rc = self.importaTransfer(
                nrDoc=nrDoc,
                simbolCarnet = simbolCarnet,
                data = opDate,
                gestiune = wmGestiune,
                operat = "D",
                items = articoleWMDoc,
                simbol_carnet_NIR = simbol_carnet_NIR,
                observatii = observatii,
                )

        if rc:
            self.logger.info("SUCCESS: Adaugare transfer")
        else:
            errors = self.getListaErori()
            self.logger.error(errors)

            if "203;Documentul exista deja in baza de date" in errors[0]:
                return True
            else:
                return False

        return True


    @decorators.time_log
    def addSupplyOrder(self, gestoData):
        # apar in WinMentor in comenzi de la gestiuni
        if len(gestoData["items"]) == 0:
            self.logger.info("Nu am nici un produs pe comanda")
            return

        if gestoData["simbolWinMentorReception"] in [None, "nil",]:
            txtMail = "Locatia {} nu are setat un simbol pentru WinMentor".format(gestoData["destination"]["name"])
            util.send_email(subject=txtMail, msg=txtMail)

            return

        ignoreCodes = []

        # verify I have all gesto codes and default gestiuni in WinMentor
        if not self.productsAreOK(gestoData):
            self.logger.info("Articole cu coduri nesetate sau gestiuni lipsa, nu adaug")
            return

        # Seteaza luna si anul in WinMentor
        opDate = datetime.datetime.fromtimestamp(gestoData["documentDate"], datetime.UTC)
        if not self.setLunaLucru(opDate.year, opDate.month):
            return False

        if self.companyName == "Panemar morarit si panificatie SRL":
            # Get lista articole from gesto, create array of articole pentru comanda
            # materia prima si marfa ajung in gestiuni diferite
            # materia prima are cod > 5000
            for categ_name, categ in gestoData["new_items"].items():

                export_categories = ["congelate", "prajituri", "materii_prime", "materii_prime2", "panificatie", "patiserie"]
                # export_categories = []

                if len(export_categories) != 0 and categ_name not in export_categories:
                    self.logger.info("Categoria este {}, se exporta doar: {}".format(categ_name, export_categories))
                    continue

                articoleWMDoc = []
                observatii = ""

                if "materii_prime" in categ_name:
                    # materia prima
                    gestDest = "Magazin {}MP".format(gestoData["branch"][:2])
                else:
                    # marfa
                    gestDest = "Magazin {}P".format(gestoData["branch"][:2])

                nrDoc = categ["documentNo"]
                self.logger.info("nrDoc: {}".format(nrDoc))

                # Cauta daca exista deja o comanda in Winmentor cu intrarea din gesto
                if self.comandaExista(
                        gestDest = gestDest,
                        nrDoc = nrDoc,
                        data = "{:%d.%m.%Y}".format(opDate),
                        ):
                    return

                observatii = "{}".format(gestoData["source"]["name"])

                for item in categ["items"]:
                    if int(item["code"]) in ignoreCodes:
                        continue

                    # sari peste daca vreau materia prima si produsul nu e materie prima sau
                    # daca vreau marfa si produsul nu e marfa

                    wmArticol = self.getProduct(item["winMentorCode"])
                    self.logger.info("wmArticol: {}".format(wmArticol))

                    simbGest = wmArticol["GestImplicita"]
                    # Adauga produs la lista produse comanda
                    articoleWMDoc.append(
                            {
                                "codExternArticol": item["winMentorCode"],
                                "um": wmArticol["DenUM"],
                                "cant": item["qty"],
                                "listPrice": item["listPrice"],
                                "opPrice": item["opPrice"],
                                "simbGest": simbGest,
                                "PretVanzareFaraTVA": wmArticol["PretVanzareFaraTVA"],
                                "discount": 0,
                                "termenLivr": "{:%d.%m.%Y}".format(opDate)
                            })

                    if item["productType_name"] == "Marfa":
                            observatii += "; "+item["name"]

                if len(articoleWMDoc) > 0:
                    # Creaza comanda
                    rc = self.importaComenzi(
                            gestDest = gestDest,
                            nrDoc = nrDoc,
                            data = opDate,
                            observatii= observatii,
                            items = articoleWMDoc,
                            )
                    if rc:
                        self.logger.info("SUCCESS: Adaugare comanda de la gestiune")
                    else:
                        self.logger.error(repr(self.getListaErori()))
                        1/0
        else:
            articoleWMDoc = []
            observatii = ""

            gestDest = "{}".format(gestoData["simbolWinMentorDeliveryNote"])

            nrDoc = int(gestoData["simbolWinMentorReception"]) * 1000000 + int(str(gestoData["documentNo"])[-5:])

            self.logger.info("nrDoc: {}".format(nrDoc))

            # Cauta daca exista deja o comanda in Winmentor cu intrarea din gesto
            # if self.comandaExista(
            #         gestDest = gestDest,
            #         nrDoc = nrDoc,
            #         data = "{:%d.%m.%Y}".format(opDate),
            #         ):
            #     return

            observatii = "{}".format(gestoData["source"]["name"])

            if self.companyName in ["SC Pan Partener Spedition Arg SRL"]:
                try:
                    observatii = f'{observatii} punct de lucru - {gestoData["source"]["address"]}'
                except KeyError:
                    observatii = f'{observatii} punct de lucru'

            for item in gestoData["items"]:
                if int(item["code"]) in ignoreCodes:
                    continue

                wmArticol = self.getProduct(item["winMentorCode"])
                self.logger.info("wmArticol: {}".format(wmArticol))

                simbGest = wmArticol["GestImplicita"]
                # Adauga produs la lista produse comanda
                articoleWMDoc.append(
                        {
                            "codExternArticol": item["winMentorCode"],
                            "um": wmArticol["DenUM"],
                            "cant": item["qty"],
                            "listPrice": item["listPrice"],
                            "opPrice": item["opPrice"],
                            "simbGest": simbGest,
                            "discount": 0,
                            "termenLivr": "{:%d.%m.%Y}".format(opDate)
                        })

                # if item["productType_name"] == "Marfa":
                #         observatii += "; "+item["name"]

            client_id = ""

            if self.companyName in ["SC Pan Partener Spedition Arg SRL"]:
                if gestoData["destination"]["name"] in ["BRUTARIE TRIVALE", "LABORATOR CREPITO TRIVALE"]:
                    # "BRUTARIE TRIVALE": 1317
                    client_id = 1317
                else:
                    client_id = gestoData['simbolWinMentorDeliveryNote']

            if len(articoleWMDoc) > 0:
                # Creaza comanda
                rc = self.importaComenzi(
                        gestDest = gestDest,
                        nrDoc = nrDoc,
                        data = opDate,
                        observatii= observatii,
                        items = articoleWMDoc,
                        client = client_id,
                    )
                if rc:
                    self.logger.info("SUCCESS: Adaugare comanda de la gestiune")
                    return True
                else:
                    errors = self.getListaErori()
                    self.logger.error(errors)
                    if "230;Documentul este deja implicat in alte tranzactii. Nu-l poti sterge sau reactualiza." in errors[0]:
                        pass

                    return False


    @decorators.time_log
    def addModificarePret(self, gestoData):
        if len(gestoData["items"]) == 0:
            self.logger.info("Nu am nici un produs pe comanda")
            return

        if gestoData["simbolWinMentorReception"] in [None, "nil",]:
            txtMail = "Locatia {} nu are setat un simbol pentru WinMentor".format(gestoData["destination"]["name"])
            util.send_email(subject=txtMail, msg=txtMail)

            return

        ignoreCodes = []

        # verify I have all gesto codes and default gestiuni in WinMentor
        if not self.productsAreOK(gestoData):
            self.logger.info("Articole cu coduri nesetate sau gestiuni lipsa, nu adaug")
            return

        # Seteaza luna si anul in WinMentor
        opDate = datetime.datetime.fromtimestamp(gestoData["documentDate"], datetime.UTC)
        if not self.setLunaLucru(opDate.year, opDate.month):
            return False

        if self.companyName == "SC Pan Partener Spedition Arg SRL":
            articoleWMDoc = []
            observatii = ""

            gestDest = "{}".format(gestoData["simbolWinMentorDeliveryNote"])

            nrDoc = int(gestoData["simbolWinMentorReception"]) * 100000 + int(str(gestoData["documentNo"])[-5:])

            self.logger.info("nrDoc: {}".format(nrDoc))

            # Cauta daca exista deja o comanda in Winmentor cu intrarea din gesto
            # if self.comandaExista(
            #         gestDest = gestDest,
            #         nrDoc = nrDoc,
            #         data = "{:%d.%m.%Y}".format(opDate),
            #         ):
            #     return

            observatii = "{}".format(gestoData["source"]["name"])

            for item in gestoData["items"]:
                if int(item["code"]) in ignoreCodes:
                    continue

                wmArticol = self.getProduct(item["winMentorCode"])
                self.logger.info("wmArticol: {}".format(wmArticol))

                if self.companyName not in ["SC Pan Partener Spedition Arg SRL"]:
                    simbGest = wmArticol["GestImplicita"]
                else:
                    simbGest = f"MAG_{gestoData['simbolWinMentorDeliveryNote']}"

                # Adauga produs la lista produse comanda
                articoleWMDoc.append(
                        {
                            "codExternArticol": item["winMentorCode"],
                            "um": wmArticol["DenUM"],
                            "cant": item["qty"],
                            "listPrice": item["listPrice"],
                            "opPrice": item["opPrice"],
                            "simbGest": simbGest,
                            "discount": 0,
                            "termenLivr": "{:%d.%m.%Y}".format(opDate)
                        })

                # if item["productType_name"] == "Marfa":
                #         observatii += "; "+item["name"]

            # client_id = ""

            # if self.companyName in ["SC Pan Partener Spedition Arg SRL"]:
            #     client_ids = {
            #         "Romancuta": 3317,
            #         "Albina": 1315
            #     }

            #     client_id = client_ids[gestoData["source"]["name"]]

            if len(articoleWMDoc) > 0:
                # Creaza comanda
                rc = self.importaModificarePret(
                        gestDest = gestDest,
                        nrDoc = nrDoc,
                        data = opDate,
                        observatii= observatii,
                        items = articoleWMDoc,
                        # client = client_id,
                    )
                if rc:
                    self.logger.info("SUCCESS: Adaugare modificare pret")
                    return True
                else:
                    errors = self.getListaErori()
                    self.logger.error(errors)
                    if "230;Documentul este deja implicat in alte tranzactii. Nu-l poti sterge sau reactualiza." in errors[0]:
                        pass

                    return False


    def importaComenzi(self, **kwargs):

        items = kwargs.get("items", [])

        # Header factura
        txtWMDoc = (
            "[InfoPachet]\n"
            "AnLucru={}\n"
            "LunaLucru={}\n"
            "Tipdocument={}\n"
            "TotalComenzi={}\n"
            "LogOn={}\n"
            ).format(
                self.an,
                self.luna,
                "COMANDA",
                1,
                self.logOn,
                )

        # Comanda
        txtWMDoc += "\n"
        txtWMDoc += "[Comanda_{}]\n".format(1)
        # txtWMDoc += "NrDoc={}\n".format(util.getNextDocumentNumber("COM"))
        txtWMDoc += "Operatie=A\n"
        txtWMDoc += "NrDoc={}\n".format(kwargs.get("nrDoc", ""))
        txtWMDoc += "Agent=212\n"
        client = kwargs.get("client", "")
        if client != "":
            txtWMDoc += f"CodClient={client}\n"
        txtWMDoc += "Locatie=sediul 1\n"
        txtWMDoc += "SimbolCarnet={}\n".format("C_G")
        txtWMDoc += "Data={:%d.%m.%Y}\n".format(kwargs.get("data", datetime.datetime.now()))
        # txtWMDoc += "SectieProductie={}\n".format(kwargs.get("gestDest", ""))
        txtWMDoc += "SectieProductie={}\n".format("PF")
        txtWMDoc += "TotalArticole={}\n".format(len(items))
        txtWMDoc += "Observatii={}\n".format(kwargs.get("observatii", ""))

        # Adauga items in comanda
        # codExtern articol;denum;cant;termen livrare;Observatii
        txtWMDoc += "\n"
        txtWMDoc += "[Items_{}]\n".format(1)

        if self.companyName in ["Andalusia", "CARMIC IMPEX SRL", "CARMIC 2 S.R.L.", "SC La Nadiniere SRL", "SC Pan Partener Spedition Arg SRL"]:
            price_field = "listPrice"
        else:
            price_field = "PretVanzareFaraTVA"

        keys = (
                "codExternArticol",
                "um",
                "cant",
                price_field,
                "discount",
                "termenLivr"
                )

        for idx, item in enumerate(items, start=1):
            txtProd = self._dictToColonList(keys, item)
            txtWMDoc += "Item_{}={}\n".format(idx , txtProd)

        self.logger.debug("txtWMDoc: \n{}".format(txtWMDoc))

        fact = txtWMDoc.split("\n")

        self._stat.SetDocsData(fact)

        # pentru identificarea clientului
        self._stat.SetIDPartField('CodIntern')

        rc = self._stat.ComenziValide()
        if rc != 1:
            return False

        rc = self._stat.ImportaComenzi()
        self._stat.SetIDPartField('CodFiscal')
        return (rc == 1)


    def importaModificarePret(self, **kwargs):
        items = kwargs.get("items", [])

        # Header factura
        txtWMDoc = (
            "[InfoPachet]\n"
            "AnLucru={}\n"
            "LunaLucru={}\n"
            "Tipdocument={}\n"
            "TotalModifPret={}\n"
            "LogOn={}\n"
            ).format(
                self.an,
                self.luna,
                "MODIFICARE PRET",
                1,
                self.logOn,
                )

        # Comanda
        txtWMDoc += "\n"
        txtWMDoc += "[PV_{}]\n".format(1)
        # txtWMDoc += "NrDoc={}\n".format(util.getNextDocumentNumber("COM"))
        txtWMDoc += "Operatie=A\n"
        txtWMDoc += "Operat=D\n"
        txtWMDoc += "NrDoc={}\n".format(kwargs.get("nrDoc", ""))
        # txtWMDoc += "Agent=92\n"
        # client = kwargs.get("client", "")
        # if client != "":
        #     txtWMDoc += f"CodClient={client}\n"
        # txtWMDoc += "Locatie=sediul 1\n"
        txtWMDoc += "SimbolCarnet={}\n".format("MP_G")
        txtWMDoc += "Data={:%d.%m.%Y}\n".format(kwargs.get("data", datetime.datetime.now()))
        # txtWMDoc += "SectieProductie={}\n".format(kwargs.get("gestDest", ""))
        # txtWMDoc += "SectieProductie={}\n".format("PF")
        txtWMDoc += "TotalArticole={}\n".format(len(items))
        txtWMDoc += "Observatii={}\n".format(kwargs.get("observatii", ""))

        # Adauga items in comanda
        # codExtern articol;denum;cant;termen livrare;Observatii
        txtWMDoc += "\n"
        txtWMDoc += "[Items_{}]\n".format(1)

        if self.companyName in ["Andalusia", "CARMIC IMPEX SRL", "CARMIC 2 S.R.L.", "SC La Nadiniere SRL", "SC Pan Partener Spedition Arg SRL"]:
            price_field = "listPrice"
        else:
            price_field = "PretVanzareFaraTVA"

        keys = (
                "codExternArticol",
                "um",
                "cant",
                price_field,
                "simbGest",
                )

        for idx, item in enumerate(items, start=1):
            txtProd = self._dictToColonList(keys, item)
            txtWMDoc += "Item_{}={}\n".format(idx , txtProd)

        self.logger.debug("txtWMDoc: \n{}".format(txtWMDoc))

        fact = txtWMDoc.split("\n")

        self._stat.SetDocsData(fact)


        rc = self._stat.ModifPretValide()
        if rc != 1:
            return False

        rc = self._stat.ImportaModifPret()
        return (rc == 1)


    def importaReglareInventar(self, **kwargs):
        items = kwargs.get("items", [])

        util.log_json(items)

        Tipdocument = kwargs.get("Tipdocument")

        if Tipdocument == "DIMINUARE DE STOC":
            total_text = "TotalDiminuari"
            param = 0
        else:
            total_text = "TotalMariri"
            param = 1

        # Header
        txtWMDoc = (
            "[InfoPachet]\n"
            "AnLucru={}\n"
            "LunaLucru={}\n"
            "Tipdocument={}\n"
            "{}=1\n"
            "LogOn={}\n"
            "\n"
            ).format(
                self.an,
                self.luna,
                Tipdocument,
                total_text,
                self.logOn,
                )

        simbolCarnet = kwargs.get("simbolCarnet")
        # Transfer
        txtWMDoc += "[PV_{}]\n".format(1)
        txtWMDoc += "Operat={}\n".format(kwargs.get("operat"))
        txtWMDoc += "NrDoc={}\n".format(kwargs.get("nrDoc", ""))
        txtWMDoc += "SimbolCarnet={}\n".format(simbolCarnet)
        txtWMDoc += "Operatie={}\n".format("A")
        txtWMDoc += "Data={:%d.%m.%Y}\n".format(kwargs.get("data"))
        # txtWMDoc += "GestDest={}\n".format(kwargs.get("gestiune"))
        txtWMDoc += "TotalArticole={}\n".format(len(items))

        # txtWMDoc += "SimbolCarnetLivr={}\n".format("DL_G")
        # txtWMDoc += "NrLivr={}\n".format(util.getNextDocumentNumber("LIV"))

        # txtWMDoc += "SimbolCarnetNir={}\n".format(kwargs.get("simbol_carnet_NIR"))
        # txtWMDoc += "NrNIR={}\n".format(util.getNextDocumentNumber("NIR"))
        txtWMDoc += "Observatii={}\n".format(kwargs.get("observatii", ""))
        # txtWMDoc += "ObservatiiNIR={}\n\n".format(kwargs.get("observatii", ""))

        # Adauga items in factura
        txtWMDoc += "\n[Items_{}]\n".format(1)
        keys = [
                "codExternArticol",
                "um",
                "cant",
                "simbGest",
                "pret",
                "pret",
                ]

        for idx, item in enumerate(items, start=1):
            txtProd = self._dictToColonList(keys, item)
            txtWMDoc += "Item_{}={}\n".format(idx, txtProd)
            # txtWMDoc += "G_224;Buc;1;Magazin 37DF;4,59;658.06;658.06;658.06;658.06;658.06;658.06"

        self.logger.debug("txtWMDoc: \n{}".format(txtWMDoc))

        fact = txtWMDoc.split("\n")

        self._stat.SetDocsData(fact)

        # 1 = marire inventar
        # 0 = diminuare inventar

        rc = self._stat.ReglareInventarValida(param)
        if rc != 1:
            # print(self.getListaErori())
            return False

        rc = self._stat.ImportaReglareInventar(param)
        if rc != 1:
            # print(self.getListaErori())
            return False

        return True


    @decorators.time_log
    def ImportaNotePredare(self, **kwargs):
        items = kwargs.get("items", [])

        # Header transfer
        txtWMDoc = (
            "[InfoPachet]\n"
            "AnLucru={}\n"
            "LunaLucru={}\n"
            "TipDocument={}\n"
            # "TotalNote={}\n"
            "TotalFacturi={}\n"
            "LogOn={}\n"
            "TipDocImpus=7\n"
            "\n"
            ).format(
                self.an,
                self.luna,
                # "NOTA PREDARE",
                "FACTURA INTRARE",
                1,
                self.logOn,
            )

        txtWMDoc += "[Factura_{}]\n".format(1)
        txtWMDoc += "Operatie=A\n"
        txtWMDoc += "SimbolCarnet={}\n".format("NP_G")
        txtWMDoc += "NrDoc={}\n".format(util.getNextDocumentNumber("NP"))
        txtWMDoc += "SimbolCarnetNir={}\n".format("NIR_G")
        txtWMDoc += "NrNIR={}\n".format(util.getNextDocumentNumber("NIR_G"))
        txtWMDoc += "DataNir={:%d.%m.%Y}\n".format(kwargs.get("data"))
        txtWMDoc += "Data={:%d.%m.%Y}\n".format(kwargs.get("data"))
        # txtWMDoc += "Gestsursa={}\n".format(kwargs.get("gestiune"))
        # txtWMDoc += "GestDest={}\n".format(kwargs.get("gestiune"))
        txtWMDoc += "GestProd={}\n".format(kwargs.get("gestiune"))
        txtWMDoc += "TotalArticole={}\n".format(len(items))

        # Adauga items in factura
        txtWMDoc += "\n[Items_{}]\n".format(1)
        keys = (
                "codExternArticol",
                "um",
                "cant",
                "pret",
                "simbGest",
                )

        for idx, item in enumerate(items, start=1):
            txtProd = self._dictToColonList(keys, item)
            txtWMDoc += "Item_{}={}\n".format(idx, txtProd)

        self.logger.debug("txtWMDoc: \n{}".format(txtWMDoc))

        fact = txtWMDoc.split("\n")

        self._stat.SetDocsData(fact)

        rc = self._stat.FactIntrareValida()
        if rc != 1:
            return False

        rc = self._stat.ImportaFactIntrare()
        return (rc == 1)


    @decorators.time_log
    def addIntrariDinProductie(self, gestoData):
        if len(gestoData["items"]) == 0:
            self.logger.info("Nu am nici un produs pe raport")
            return True

        # Get gestiune in WinMentor
        # wmGestiune = self.matchGestiune(gestoData["branch"])

        if self.companyName == "SC Pan Partener Spedition Arg SRL":
            simbGest = f"MAG_{gestoData['branch_winMentorCode']}"
        elif self.companyName == 'S.C. Kattana Black SRL':
            simbGest = 'ARIES'
        else:
            1/0

        wmGestiune = self.matchGestiune(simbGest)
        if wmGestiune is None:
            self.logger.info("Nu am gasit gestiunea")
            return False

        # Seteaza luna si anul in WinMentor
        opDate = datetime.datetime.fromtimestamp(gestoData["dateBegin"], datetime.UTC)
        self.setLunaLucruPentruExport(opDate, f'intrari din productie {gestoData["branch"]}')

        ignoreCodes = []
        if self.companyName == "Panemar morarit si panificatie SRL":
            ignoreCodes = [1105, 819, ]

        # verify I have all gesto codes and default gestiuni in WinMentor
        if not self.productsAreOK(gestoData):
            self.logger.info("Articole cu coduri nesetate sau gestiuni lipsa, nu adaug")
            return False

        # Get lista articole from gesto, create array of articole pentru workOrders
        articoleWMDoc = []
        for item in gestoData["items"]:
            if int(item["code"]) in ignoreCodes:
                continue

            # Adauga produs la lista produse
            wmArticol = self.getProduct(item["winMentorCode"])
            self.logger.debug("wmArticol: \n{}".format(wmArticol))

            # pret_fara_TVA = round(item["listVal"]/item["qty"]/((100.0+item["vat"]) /100), 2)
            pret_cu_TVA = round(item["listVal"]/item["qty"], 2)
            # pret = wmArticol["PretVanzareFaraTVA"]

            articoleWMDoc.append({
                        "codExternArticol": item["winMentorCode"],
                        "um": wmArticol["DenUM"],
                        "cant": item["qty"],
                        # "pret": item["listVal"]/item["qty"],
                        "pret": pret_cu_TVA,
                        # "simbGest": wmArticol["GestImplicita"]
                        "simbGest": wmGestiune
                    })

        if self.companyName == 'SC Pan Partener Spedition Arg SRL':
            Tipdocument = 'MARIRE DE STOC'
            simbolCarnet = 'MS_G'
            # folosim numarul local doar pentru maririre de stoc pe baza intrarilor din productie
            # pentru notele de reglare stoc se creeaza numarul pe baza documentului sursa
            nrDoc = util.getNextDocumentNumber(simbolCarnet)
            simbol_carnet_NIR = 'NIR_G'
            observatii = gestoData["branch"]

            # Creeaza marire de stoc
            rc = self.importaReglareInventar(
                Tipdocument = Tipdocument,
                nrDoc = nrDoc,
                simbolCarnet = simbolCarnet,
                data = opDate,
                gestiune = wmGestiune,
                items = articoleWMDoc,
                operat = 'D',
                simbol_carnet_NIR = simbol_carnet_NIR,
                observatii = observatii
            )
        else:
            # Creaza transferul
            rc = self.ImportaNotePredare(
                    data = opDate,
                    gestiune = wmGestiune,
                    items = articoleWMDoc
                    )

        if rc:
            self.logger.info("SUCCESS: Adaugare nota predare/ nota intrare din productie/ marire de stoc")
            ret = True
        else:
            errors = repr(self.getListaErori())
            self.logger.error(errors)
            msg = "{}".format(errors)

            util.send_email(
                    subject = "WinMentor - Eroare la adaugare nota intrare din productie la {}, {}".format(gestoData["branch"], opDate),
                    msg = msg
                    )
            ret = False

        self.logger.info("ret: {}".format(ret))
        return ret


    @decorators.time_log
    def addNotaModificareStoc(self, gestoData, modif_type="Diminuare"):
        # gestoData["items"][0]["winMentorCode"] = "G_1005"

        if len(gestoData["items"]) == 0:
            self.logger.info(f'Nu am nici un produs pe {gestoData["type"]}')
            return True

        # Get gestiune in WinMentor

        if self.companyName == "Panemar morarit si panificatie SRL":
            campPret = "PretVanzareFaraTVA"
            simbGest = "Magazin {}P".format(gestoData["branch"][:2])
        elif self.companyName == "SC Pan Partener Spedition Arg SRL":
            campPret = "PretReferinta"
            simbGest = f"MAG_{gestoData['simbolWinMentorDeliveryNote']}"
        else:
            1/0

        wmGestiune = self.matchGestiune(simbGest)
        if wmGestiune is None:
            self.logger.info("Nu am gasit gestiunea")
            return False

        # Seteaza luna si anul in WinMentor
        opDate = datetime.datetime.fromtimestamp(gestoData["documentDate"], datetime.UTC)
        if not self.setLunaLucru(opDate.year, opDate.month):
            return False

        ignoreCodes = []

        if self.companyName == "Panemar morarit si panificatie SRL":
            tipGest = self.getTipGest(gestoData, ignoreCodes)
            if tipGest in ["Skip export", "MP"]:
                self.logger.info("tipGest={}".format(tipGest))
                return True
            elif tipGest is None:
                template = loader.get_template("mail/admin/incorrectProductTypeReception.html")
                if gestoData["type"] == "scrap":
                    subject = "Rebutul {} - {} cu probleme in WinMentor".format(gestoData["documentNo"], gestoData["source"]["name"])

                html_part = template.render({
                    "subject": subject,
                    "gestoData": gestoData,
                    'HOME_URL': settings.HOME_URL,
                })

                util.send_email(subject, html_part,
                                toEmails=util.getCfgVal("client", "notificationEmails"),
                                # toEmails=["silviu@vectron.ro"],
                                location=False)

                return True
        else:
            tipGest = None

        # verify I have all gesto codes and default gestiuni in WinMentor
        if not self.productsAreOK(gestoData):
            self.logger.info("Articole cu coduri nesetate sau gestiuni lipsa, nu adaug")
            return False

        # Get lista articole from gesto, create array of articole pentru workOrders
        articoleWMDoc = []
        for item in gestoData["items"]:
            if int(item["code"]) in ignoreCodes:
                continue

            wmArticol = self.getProduct(item["name2"])
            self.logger.debug("wmArticol: \n{}".format(wmArticol))

            pret = item["listPrice"]
            # pret = wmArticol[campPret]

            articoleWMDoc.append({
                        "codExternArticol": item["name2"],
                        "um": wmArticol["DenUM"],
                        "cant": abs(item["qty"]),
                        "pret": pret,
                        "simbGest": simbGest
                    })

        operat = "D"

        msgs = [gestoData["category"], gestoData["details"], gestoData["branch"]]
        observatii = ", ".join([msg for msg in msgs if msg not in [None, "", "nil"]])

        if self.companyName == "Panemar morarit si panificatie SRL":
            simbol_carnet_NIR = "GNIR"
        else:
            simbol_carnet_NIR = "NIR_G"

        if self.companyName == "SC Pan Partener Spedition Arg SRL":
            nrDoc = int(gestoData["simbolWinMentorReception"]) * 10000000 + gestoData["documentNo"]
        else:
            nrDoc = int(gestoData["branch"][:2]) * 10000000 + gestoData["documentNo"]

        if modif_type=="Diminuare":
            Tipdocument = "DIMINUARE DE STOC"
            simbolCarnet = "DS_G"

        else:
            Tipdocument = "MARIRE DE STOC"
            simbolCarnet = "MS_G"

        rc = self.importaReglareInventar(
                Tipdocument = Tipdocument,
                nrDoc = nrDoc,
                simbolCarnet = simbolCarnet,
                data = opDate,
                gestiune = wmGestiune,
                items = articoleWMDoc,
                operat = operat,
                simbol_carnet_NIR = simbol_carnet_NIR,
                observatii = observatii,
                )

        if rc:
            self.logger.info("SUCCESS: Adaugare modificare stoc")
        else:
            self.logger.error(repr(self.getListaErori()))
            return False

        return True


    def importaMonetare(self, **kwargs):
        '''
        @param items: array produse; fiecare produs e un dict cu urmatoarele posibile chei:
            - codExternArticol
            - nrDoc
            - nrNir
            - um: unitate masura
            - cant
            - pret
            - data
            - dataNir
            - simbGest: simbol gestiune receptie
            - discount: discount linie
            - simbServ: simbol cont pt. articole de tip serviciu
            - pretInreg: pret inregistrare pentru articole ce au tip contabil implicit cu adaos
            - termenGarantie
            - logOn
            - simbolCarnet
        '''

        branch = kwargs.get("branch")
        pos = kwargs.get("pos")

        self.logger.info(f"{kwargs=}")

        if self.companyName in ["SC Pan Partener Spedition Arg SRL", ]:
            branch_winMentorCode = kwargs.get("branch_winMentorCode")
            if int(branch_winMentorCode) < 4862:
                monetarCasa = f"MAGAZIN {branch.upper()}"
            else:
                monetarCasa = f"MAGAZIN MIOVENI"
        else:
            monetarCasa = util.getCfgVal("winmentor", "monetareCasaDefault")

            self.logger.info("branch: {}".format(branch))

            if util.cfg_has_option("monetareCasa", branch):
                monetarCasa = util.getCfgVal("monetareCasa", branch)

        self.logger.info(f"{monetarCasa=}")

        items = kwargs.get("items", [])

        self.logger.info(f"{items=}")

        # Header transfer
        txtWMDoc = (
            "[InfoPachet]\n"
            "AnLucru={}\n"
            "LunaLucru={}\n"
            "Tipdocument={}\n"
            "TotalMonetare={}\n"
            "LogOn={}\n"
            "\n"
            ).format(
                self.an,
                self.luna,
                "MONETAR",
                1,
                self.logOn,
                )

        # Transfer
        txtWMDoc += "[Monetar_{}]\n".format(1)
        if self.companyName in ["CARMIC IMPEX SRL", "CARMIC 2 S.R.L.", "SC La Nadiniere SRL",]:
            operat = "N"
        else:
            operat = "D"
        txtWMDoc += f"Operat={operat}\n"
        txtWMDoc += "NrDoc={}\n".format(kwargs.get("nrDoc", ""))
        txtWMDoc += "SimbolCarnet={}\n".format(kwargs.get("simbolCarnet"))
        txtWMDoc += "Operatie={}\n".format("A")
        txtWMDoc += "CasaDeMarcat={}\n".format("D")
        txtWMDoc += "NumarBonuri={}\n".format(kwargs.get("clientsNo", ""))
        txtWMDoc += "Data={:%d.%m.%Y}\n".format(kwargs.get("data"))
        txtWMDoc += "Casa={}\n".format(monetarCasa)
        txtWMDoc += "TotalArticole={}\n".format(len(items))
        payment = kwargs.get("payment")
        txtWMDoc += "CEC={}\n".format(payment["bank transfer"] if "bank transfer" in payment else 0)

        card_sum = 0
        for key, value in payment.items():
            if 'card' in key.lower():
                card_sum += value

        txtWMDoc += "CARD={}\n".format(card_sum)
        txtWMDoc += "BONVALORIC={}\n".format(payment["food vouchers"] if "food vouchers" in payment else 0)

        if self.companyName in ["SC Pan Partener Spedition Arg SRL", ]:
            txtWMDoc += "Observatii={}\n".format(pos)
        else:
            txtWMDoc += "Observatii={}\n".format(branch)
        txtWMDoc += "Discount={}\n".format(0)
        txtWMDoc += "TVADiscount={}\n".format(0)

        # Adauga items in monetar
        txtWMDoc += "\n[Items_{}]\n".format(1)
        keys = (
                "codExternArticol",
                "um",
                "cant",
                "pret",
                "simbGest",
                )

        if self.companyName in ["Andalusia", "CARMIC IMPEX SRL", "CARMIC 2 S.R.L.", "SC La Nadiniere SRL", "SC Pan Partener Spedition Arg SRL", "S.C. Kattana Black SRL"]:
            for idx, item in enumerate(items, start=1):
                txtProd = self._dictToColonList(keys, item)

                key = item["codExternArticol"][:item["codExternArticol"].rfind("_")]
                txtWMDoc += "Item_{}={}\n".format(idx, txtProd)

                if item["tip_contabil"] is not None:
                    txtWMDoc += f"Item_{idx}_TipContabil={item["tip_contabil"]}\n"

        else:
            prodIdx = {}
            prodIdx["G_PROD_9"] = 1
            prodIdx["G_MARF_9"] = 2
            prodIdx["G_MARF_19"] = 3
            prodIdx["G_PROD_19"] = 4

            for item in items:
                txtProd = self._dictToColonList(keys, item)
                key = item["codExternArticol"][:item["codExternArticol"].rfind("_")]
                self.logger.debug("key: {}".format(key))
                self.logger.debug("idx: {}".format(prodIdx[key]))
                txtWMDoc += "Item_{}={}\n".format(prodIdx[key], txtProd) # items start at 1

        self.logger.debug("txtWMDoc: \n{}".format(txtWMDoc))

        fact = txtWMDoc.split("\n")

        self._stat.SetDocsData(fact)

        rc = self._stat.MonetareValide()
        if rc != 1:
            return False

        rc = self._stat.ImportaMonetare()

        return (rc == 1)


    @decorators.time_log
    def addMonetare(self, gestoData):
        start = datetime.datetime.now()

        self.logger.debug("\n%s",
                        json.dumps(
                            gestoData,
                            sort_keys=True,
                            indent=4,
                            separators=(',', ': '),
                            default=util.defaultJSON
                            )
                        )

        if len(gestoData["items"]) == 0:
            self.logger.info("Nu am nici un produs pe monetar")
            return False

        # Get gestiune in WinMentor
        # wmGestiune = self.matchGestiune(gestoData["branch"], "PRODUSE")

        # Seteaza luna si anul in WinMentor
        opDate = datetime.datetime.fromtimestamp(gestoData["dateBegin"])
        self.setLunaLucruPentruExport(opDate, f'monetar {gestoData["branch"]}')

        # verify I have all gesto codes and default gestiuni in WinMentor
        # if not self.productsAreOK(gestoData):
        #     self.logger.info("Monetarul are articole cu coduri nesetate sau gestiuni lipsa, nu adaug")
        #     return False

        if not self.productsAreOK(gestoData):
            self.logger.info("Monetarul are articole cu coduri nesetate sau gestiuni lipsa, nu adaug")
            return False

       #  Get lista articole from gesto, create array of articole pentru factura

        newItems = {}
        ret = True

        for item in gestoData["items"]:
            if self.companyName in ["Andalusia", "CARMIC IMPEX SRL", "CARMIC 2 S.R.L.", "SC La Nadiniere SRL", "SC Pan Partener Spedition Arg SRL", 'S.C. Kattana Black SRL']:
                codExternArticol = item["winMentorCode"]
            else:
                if item["winMentorCode"].startswith("G_MARF"):
                    codExternArticol = item["winMentorCode"]
                else:
                    codExternArticol = "G_PROD_{}_{}".format(item["vat"], gestoData["branch"][:2])

            if not self.productExists(codExternArticol):
                ret = False
                if codExternArticol not in self.missingWMCodes:
                    self.logger.info("Nu exista in Mentor produsul cu codul : {}".format(codExternArticol))

                    # only add a code once
                    self.missingWMCodes[codExternArticol] = {
                            "item": item,
                            "details": "{} - {}".format(gestoData["dateBeginHuman"],
                                                             gestoData["branch"],
                                                             )
                        }
            else:
                # Adauga produs la lista produse transfer
                wmArticol = self.getProduct(codExternArticol)
                # self.logger.info("wmArticol: {}".format(wmArticol))

                if self.companyName in ["Andalusia", "CARMIC IMPEX SRL", "CARMIC 2 S.R.L.", "SC La Nadiniere SRL", "SC Pan Partener Spedition Arg SRL", \
                                        "S.C. Kattana Black SRL"]:
                    item.update({
                        "codExternArticol": codExternArticol,
                        "um": wmArticol["DenUM"],
                        "cant": item["qty"],
                        "pret": item["opVal"] / item["qty"],
                        "tip_contabil": None,
                    })

                    if self.companyName in ['S.C. Kattana Black SRL']:
                        item["simbGest"] = 'ARIES'
                    elif self.companyName in ['SC Pan Partener Spedition Arg SRL']:
                        item["simbGest"] = f"MAG_{gestoData['branch_winMentorCode']}"
                        if item["code"] in ["21000", "21001", "21002", "21003"]:
                            item["tip_contabil"] = "TC_AVANS"
                        elif item["code"] in ["102", "103", "104", "105"]:
                            item["tip_contabil"] = "TC_ROPET"
                    else:
                        item["simbGest"] = wmArticol["GestImplicita"]
                else:
                    if codExternArticol not in newItems:
                        newItems[codExternArticol] = {
                                    "codExternArticol": codExternArticol,
                                    "um": wmArticol["DenUM"],
                                    "cant": 1,
                                    "pret": 0,
                                    "simbGest": wmArticol["GestImplicita"],
                                    "tip_contabil": None,
                                }

                    newItems[codExternArticol]["pret"] += item["opVal"]

        self.logger.info(f"{newItems=}")
        self.logger.info(f'{gestoData["items"]=}')

        if ret == True:
            # Creaza transferul doar daca am coduri pentru toate produsele

            if self.companyName in ["Andalusia", "CARMIC IMPEX SRL", "CARMIC 2 S.R.L.", "SC La Nadiniere SRL", "SC Pan Partener Spedition Arg SRL", \
                                        "S.C. Kattana Black SRL"]:
                articoleWMDoc = gestoData["items"]
            else:
                articoleWMDoc = []
                for (key, item) in newItems.items():
                    articoleWMDoc.append(
                            {
                                "codExternArticol": item["codExternArticol"],
                                "um": item["um"],
                                "cant": item["cant"],
                                "pret": item["pret"],
                                "simbGest": item["simbGest"],
                                "tip_contabil": item["tip_contabil"]
                                }
                            )

            if self.companyName in ["CARMIC IMPEX SRL", "CARMIC 2 S.R.L."]:
                try:
                    nrDoc = gestoData["cash_register_report"]["last_documentNoFiscal"]
                except KeyError:
                    nrDoc = 100000

                simbolCarnet = "{}{}".format(gestoData["branch_winMentorCode"], gestoData["pos_no"])

            else:
                # nrDoc = 28000
                # simbolCarnet = "MMR"
                nrDoc = util.getNextDocumentNumber("MON")
                simbolCarnet = "M_G"

            rc = self.importaMonetare(
                    # nrDoc = gestoData["documentNo"],
                    nrDoc = nrDoc,
                    simbolCarnet = simbolCarnet,
                    data = opDate,
                    items = articoleWMDoc,
                    payment = gestoData["payment"],
                    branch = gestoData["branch"],
                    branch_winMentorCode = gestoData["branch_winMentorCode"],
                    pos = gestoData["pos_name"],
                    clientsNo = gestoData["clientsNo"] if gestoData["clientsNo"] not in ("nil", None) else 0,
                    )

            if rc:
                self.logger.info("SUCCESS: Adaugare monetar")
                ret = True
            else:
                subject = f'Eroare export monetar {gestoData["branch"]}'

                util.report_problem(subject, repr(self.getListaErori()), hours=2)

                ret = False

        self.logger.info("ret: {}".format(ret))
        return ret


    def importaTransfer(self, **kwargs):
        '''
        @param items: array produse; fiecare produs e un dict cu urmatoarele posibile chei:
            - codExternArticol
            - nrDoc
            - nrNir
            - um: unitate masura
            - cant
            - pret
            - data
            - dataNir
            - simbGest: simbol gestiune receptie
            - discount: discount linie
            - simbServ: simbol cont pt. articole de tip serviciu
            - pretInreg: pret inregistrare pentru articole ce au tip contabil implicit cu adaos
            - termenGarantie
            - logOn
            - simbolCarnet
        '''

        items = kwargs.get("items", [])

        # Header transfer
        txtWMDoc = (
            "[InfoPachet]\n"
            "AnLucru={}\n"
            "LunaLucru={}\n"
            "Tipdocument={}\n"
            "TotalTransferuri={}\n"
            "LogOn={}\n"
            "\n"
            ).format(
                self.an,
                self.luna,
                "TRANSFER",
                1,
                self.logOn,
                )

        # Transfer
        txtWMDoc += "[Transfer_{}]\n".format(1)
        txtWMDoc += "SimbolCarnet={}\n".format(kwargs.get("simbolCarnet"))
        txtWMDoc += "NrDoc={}\n".format(kwargs.get("nrDoc", ""))
        txtWMDoc += "Data={:%d.%m.%Y}\n".format(kwargs.get("data"))
        txtWMDoc += "GestDest={}\n".format(kwargs.get("gestiune"))
        txtWMDoc += "Operatie={}\n".format("A")
        txtWMDoc += "Operat={}\n".format(kwargs.get("operat"))
        txtWMDoc += "TotalArticole={}\n".format(len(items))
        txtWMDoc += "Observatii={}\n\n".format(kwargs.get("observatii"))

        # Adauga items in factura
        txtWMDoc += "\n[Items_{}]\n".format(1)
        keys = (
                "codExternArticol",
                "um",
                "cant",
                "pret",
                "simbGest",
                )

        for idx, item in enumerate(items):
            txtProd = self._dictToColonList(keys, item)
            txtWMDoc += "Item_{}={}\n".format(idx + 1, txtProd) # articolele incep de la 1

        self.logger.debug("txtWMDoc: \n{}".format(txtWMDoc))

        fact = txtWMDoc.split("\n")

        self._stat.SetDocsData(fact)

        rc = self._stat.TransferuriValide()
        if rc != 1:
            return False

        rc = self._stat.ImportaTransferuri()
        return (rc == 1)


    @decorators.time_log
    def getTransferuri(self, opDate):
        if not self.setLunaLucru(opDate.year, opDate.month):
            return {}

        alreadyAdded = False
        transferuri, rc = self._stat.GetTransferuri()
        if rc != 0:
            self.logger.error(repr(self.getListaErori()))

        sources = util.getCfgVal("deliveryNote", "sources")
        destinations = util.getCfgVal("deliveryNote", "destinations")
        dnDate = "{}.{}.{}".format(opDate.day, opDate.month, opDate.year)

        self.logger.info("dnDate: {}".format(dnDate))

        deliveryNotes = {}

        self.logger.info("{} transferuri".format(len(transferuri)))
        # self.logger.info(transferuri)
        # 1/0

        ret = True

        for item in transferuri:
            # self.logger.info(item)
            items = item.split(";")
            # self.logger.info(items)

            source = str(items[0])
            date = items[3]
            destination = str(items[1])
            transferNo = items[2]

            if self.companyName not in ["SC Pan Partener Spedition Arg SRL"]:
                if source not in sources:
                    continue
            else:
                source = destination

            if destination not in destinations:
                continue
            if date != dnDate:
                continue

            if source not in deliveryNotes:
                deliveryNotes[source] = {}

            if self.companyName in ["SC Pan Partener Spedition Arg SRL"]:
                # numerele de document fac diferenta pentru destinatie
                transferNo_int = int(transferNo)

                if transferNo_int < 10000:
                    1/0
                elif transferNo_int < 20000:
                    destination = "3317"
                elif transferNo_int < 30000:
                    destination = "1307"
                elif transferNo_int < 40000:
                    destination = "1308"
                elif transferNo_int < 50000:
                    destination = "1312"
                elif transferNo_int < 60000:
                    destination = "1892"
                elif transferNo_int < 70000:
                    destination = "1314"
                elif transferNo_int < 80000:
                    destination = "1313"
                elif transferNo_int < 90000:
                    destination = "1326"
                elif transferNo_int < 100000:
                    destination = "1310"
                elif transferNo_int < 110000:
                    destination = "1315"
                elif transferNo_int < 120000:
                    destination = "2091"
                elif transferNo_int < 130000:
                    destination = "1309"
                elif transferNo_int < 140000:
                    destination = "1316"
                elif transferNo_int < 150000:
                    destination = "1306"
                elif transferNo_int < 160000:
                    destination = "3732"
                elif transferNo_int < 170000:
                    destination = "3809"
                elif transferNo_int < 180000:
                    destination = "4243"
                elif transferNo_int < 190000:
                    destination = "4702"
                elif transferNo_int < 200000:
                    destination = "4722"
                elif transferNo_int < 210000:
                    destination = "4862"
                else:
                    self.logger.info(f"{transferNo_int=} nu il am in lista de destinatii")
                    1/0

            if date not in deliveryNotes[source]:
                deliveryNotes[source][date] = {}

            if destination not in deliveryNotes[source][date]:
                deliveryNotes[source][date][destination] = {}

            if transferNo not in deliveryNotes[source][date][destination]:
                deliveryNotes[source][date][destination][transferNo] = {
                    "items": [],
                    "transferNo": transferNo,
                    "value": 0
                }

            productCode = items[4]
            productName = items[5]

            if productCode == "":
                if productName not in self.productsMissingWMCodes:
                    ret = False
                    # only add a code once
                    self.productsMissingWMCodes.append(items[5])

            if items[6] != "":
                if self.companyName in ["Andalusia", "CARMIC IMPEX SRL", "CARMIC 2 S.R.L.", "SC La Nadiniere SRL", "SC Pan Partener Spedition Arg SRL"]:
                    opPrice = Decimal(items[8].replace(",", "."))
                else:
                    opPrice = Decimal(items[7].replace(",", "."))

                qty = Decimal(items[6].replace(",","."))

                val_add = opPrice * qty
                # val_add = Decimal("{:.3f}".format(val_add)).quantize(Decimal('.01'), rounding=ROUND_HALF_UP)
                val_add = val_add.quantize(Decimal('.01'), rounding=ROUND_HALF_UP)

                deliveryNotes[source][date][destination][transferNo]["value"] += val_add
                deliveryNotes[source][date][destination][transferNo]["items"].append({
                                "winMentorCode": productCode,
                                "name": productName,
                                "opPrice": opPrice,
                                "listPrice": float(items[8].replace(",", ".")),
                                "qty": qty
                        })

        if ret == False:
            deliveryNotes = {}

        ret = deliveryNotes

        util.log_json(ret)

        return ret


    @decorators.time_log
    def addWorkOrders(self, gestoData):
        self.logger.debug("\n%s",
                        json.dumps(
                            gestoData,
                            sort_keys=True,
                            indent=4,
                            separators=(',', ': '),
                            default=util.defaultJSON
                            )
                        )

        if len(gestoData["items"]) == 0:
            self.logger.info("Nu am nici un produs pe transfer")
            return False

        # Get gestiune in WinMentor
        wmGestiune = self.matchGestiune(gestoData["branch"])

        # Seteaza luna si anul in WinMentor
        opDate = datetime.datetime.fromtimestamp(gestoData["dateBegin"])
        self.setLunaLucruPentruExport(opDate, f'transfer {gestoData["branch"]}')

        # verify I have all gesto codes and defalut gestiuni in WinMentor
        if not self.productsAreOK(gestoData):
            self.logger.info("Factura are articole cu coduri nesetate sau gestiuni lipsa, nu adaug")
            return False

        # Get lista articole from gesto, create array of articole pentru workOrders
        articoleWMDoc = []
        for item in gestoData["items"]:
            # Adauga produs la lista produse
            if self.companyName in ["Andalusia", "CARMIC IMPEX SRL", "CARMIC 2 S.R.L.", "SC La Nadiniere SRL", "SC Pan Partener Spedition Arg SRL"]:
                simbGest = "DEP_CENTRAL"
                pret = item["opVal"] / item["qty"]
            else:
                pret = wmArticol["PretVCuTVA"]

                if self.isDrink(int(item["code"])):
                    simbGest = "PF-Bauturi"
                elif self.isSdwSalad(int(item["code"])):
                    simbGest = "PF Sandwich"
                else:
                    # I need to have a gestiune for these articles too
                    continue

            wmArticol = self.getProduct(item["winMentorCode"])
            self.logger.info(wmArticol)

            articoleWMDoc.append({
                        "codExternArticol": item["winMentorCode"],
                        "um": wmArticol["DenUM"],
                        "cant": item["qty"],
                        "pret": pret,
                        "simbGest": simbGest
                    })

        # Creaza transferul
        rc = self.importaTransfer(
                # nrDoc = gestoData["documentNo"],
                nrDoc = util.getNextDocumentNumber("NT"),
                data = opDate,
                gestiune = wmGestiune,
                items = articoleWMDoc
                )

        if rc:
            self.logger.info("SUCCESS: Adaugare transfer")
        else:
            self.logger.error(repr(self.getListaErori()))


    @decorators.time_log
    def addBonConsum(self, **kwargs):
        items = kwargs.get("items", [])

        # Header transfer
        txtWMDoc = (
            "[InfoPachet]\n"
            "AnLucru={}\n"
            "LunaLucru={}\n"
            "Tipdocument={}\n"
            "TotalBonuri={}\n"
            "LogOn={}\n"
            "\n"
            ).format(
                self.an,
                self.luna,
                "BON DE CONSUM",
                1,
                self.logOn,
            )

        # Transfer
        txtWMDoc += "[BON_{}]\n".format(1)
        txtWMDoc += "SimbolCarnet={}\n".format(kwargs.get("simbolCarnet"))
        txtWMDoc += "NrDoc={}\n".format(util.getNextDocumentNumber(kwargs.get("simbolCarnet")))
        txtWMDoc += "Data={:%d.%m.%Y}\n".format(kwargs.get("data"))
        txtWMDoc += "GestConsum={}\n".format(kwargs.get("gestiune"))
        txtWMDoc += "Operatie={}\n".format("A")
        txtWMDoc += "Operat={}\n".format(kwargs.get("operat"))
        txtWMDoc += "TotalArticole={}\n".format(len(items))
        # txtWMDoc += "SimbolCarnetLivr={}\n".format("DL_G")
        txtWMDoc += "SimbolCarnetLivr={}\n".format("DL_G")
        # txtWMDoc += "NrLivr={}\n".format(util.getNextDocumentNumber("LIV"))
        txtWMDoc += "Observatii={}\n".format(kwargs.get("observatii"))
        # txtWMDoc += "ObservatiiLivr={}\n".format("aiurea 1")
        # txtWMDoc += "ObservatiiNIR={}\n\n".format("aiurea 2")

        # Adauga items in factura
        txtWMDoc += "\n[Items_{}]\n".format(1)
        keys = [
                "codExternArticol",
                "um",
                "cant",
                "pret",
                "simbGest",
                # "tip_contabil"
                # "pret",
                # "pret",
                # "pret",
        ]

        for idx, item in enumerate(items, start=1):
            txtProd = self._dictToColonList(keys, item, forceAbs=True)
            txtWMDoc += "Item_{}={}\n".format(idx, txtProd)
            # txtWMDoc += f"Item_{idx}_TipContabil={item['tip_contabil']}\n"

            if item["tip_contabil"] is not None:
                txtWMDoc += f"Item_{idx}_TipContabil={item["tip_contabil"]}\n"

        self.logger.debug("txtWMDoc: \n{}".format(txtWMDoc))

        fact = txtWMDoc.split("\n")

        self._stat.SetDocsData(fact)

        rc = self._stat.BonuriConsumValide()
        if rc != 1:
            return False

        rc = self._stat.ImportaBonuriConsum()

        return (rc == 1)


    @decorators.time_log
    def addProductSummary(self, gestoData, opDate=None, monthly=False):
        if len(gestoData["items"]) == 0:
            self.logger.info("Nu am nici un produs pe raport")
            return True

        # Get gestiune in WinMentor

        if self.companyName == "SC Pan Partener Spedition Arg SRL":
            simbGest = f"MAG_{gestoData['branch_winMentorCode']}"
        elif self.companyName == 'S.C. Kattana Black SRL':
            simbGest = 'ARIES'
        else:
            1/0

        wmGestiune = self.matchGestiune(simbGest)
        if wmGestiune is None:
            self.logger.info("Nu am gasit gestiunea")
            return False

        # Seteaza luna si anul in WinMentor
        if opDate is None:
            opDate = datetime.datetime.fromtimestamp(gestoData["dateBegin"], datetime.UTC)

        self.setLunaLucruPentruExport(opDate, f'bon de consum {gestoData["branch"]}')

        ignoreCodes = []
        if self.companyName == "Panemar morarit si panificatie SRL":
            ignoreCodes = [729, 5200, 5201, 5329]
            if monthly:
                ignoreCodes += [5220, 5221, 5222, 5223]

        # verify I have all gesto codes and default gestiuni in WinMentor
        if not self.productsAreOK(gestoData):
            self.logger.info("Articole cu coduri nesetate sau gestiuni lipsa, nu adaug")
            return False

        tip_contabil = None

        if monthly:
            simbolCarnet = "BC_MP_G"
            simbGest = "Magazin {}MP".format(gestoData["branch"][:2])
            operat="N"
        else:
            simbolCarnet = "BC_G"
            operat="D"
            if self.companyName == "SC Pan Partener Spedition Arg SRL":
                simbGest = f"MAG_{gestoData['branch_winMentorCode']}"
                tip_contabil = f"TC_{gestoData['branch_winMentorCode']}"

        # Get lista articole from gesto, create array of articole pentru workOrders
        articoleWMDoc = []
        for item in gestoData["items"]:
            if int(item["code"]) in ignoreCodes:
                continue

            if item["qty"] == 0:
                continue

            # Adauga produs la lista produse
            # if self.isDrink(int(item["code"])):
            #     simbGest = "PF-BauRsl727uiv!turi"
            # elif self.isSdwSalad(int(item["code"])):
            #     simbGest = "PF Sandwich"
            # else:
            #     # I need to have a gestiune for these articles too
            #     continue

            wmArticol = self.getProduct(item["winMentorCode"])
            self.logger.debug("wmArticol: {}".format(wmArticol))

            pret = wmArticol["PretReferinta"]
            if self.companyName == "SC Pan Partener Spedition Arg SRL" or pret == "":
                pret = item["listVal"]

            articoleWMDoc.append({
                        "codExternArticol": item["winMentorCode"],
                        "um": wmArticol["DenUM"],
                        "cant": item["qty"],
                        # "pret": item["listVal"]/item["qty"],
                        "pret": pret,
                        # "simbGest": wmArticol["GestImplicita"]
                        "simbGest": simbGest,
                        "tip_contabil": tip_contabil,
                    })

        rc = self.addBonConsum(
                data = opDate,
                simbolCarnet = simbolCarnet,
                observatii = gestoData["branch"],
                observatiiLivr = gestoData["branch"],
                gestiune = wmGestiune,
                items = articoleWMDoc,
                operat = operat
            )

        if rc:
            self.logger.info("SUCCESS: Adaugare BonConsum")
            ret = True
        else:
            self.logger.error(repr(self.getListaErori()))
            ret = False

        self.logger.info("ret: {}".format(ret))
        return ret

