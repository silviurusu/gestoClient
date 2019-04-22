'''
Facade (wrapper) for WinMentor OLE wrapper

@date 20/09/2017
@author Radu Cucu
'''

import pythoncom, win32com.client
from datetime import datetime as dt, timedelta
from numbers import Number
import collections
import logging
import util
import traceback
import inspect
import re
import json
import math
from util import send_email
from django.template import loader, Context
import datetime
import settings


class WinMentor(object):
    ''' classdocs
    '''

    parteneri = None
    multiplePartenerIDs = {}
    multiplePartenerIDsForEmail = []
    products = None
    gestiuni = None
    intrari = {}
    iesiri = {}
    comenzi = {}
    transfers = {}

    productCodesBauturi = [[1005, 1006], [700, 728], [731, 798],]
    productCodesSdwSalate = [[799, 882], [1100, 1150],]

    documentNoInitWeb = 1000000

    missingCodes = {}
    missingDefaultGest = {}
    productsMissingWMCodes =[]
    missingWMCodes = {}
    missingPartners = {}


    def __init__(self, **kwargs):
        self.logger = logging.getLogger(__name__)

        self._fdm = pythoncom.LoadTypeLib('WMDocImpServer.tlb')
        self._stat = None

        if self._fdm is None:
            return

        for idx in xrange(0, self._fdm.GetTypeInfoCount()):
            fdoc = self._fdm.GetDocumentation(idx)
            if fdoc[0] == 'WMDocImpObject':
                type_iid = self._fdm.GetTypeInfo(idx).GetTypeAttr().iid
                self._stat = win32com.client.Dispatch(type_iid)

        if self._stat is None:
            1/0

        rc = self._stat.LogOn("vectron", "1")
        # rc = self._stat.LogOn("mircea", "2")
        self.logger.info("LogOn rc = {}".format(rc))
        if rc != 1:
            errors = self.getListaErori()
            self.logger.error(repr(errors))
            print errors
            exit()

        # seteaza firma de lucru
        self.firma = kwargs.get("firma")
        self.logger.info("firma: {}".format(self.firma))

        if self.firma is not None:
            rc = self._stat.SetNumeFirma(self.firma)
            self.logger.info("SetNumeFirma rc = {}".format(rc))
            if rc != 1:
                self.logger.error(repr(self.getListaErori()))
                1/0

        # Seteaza luna lucru
        self.an = kwargs.get("an")
        self.logger.info("an: {}".format(self.an))
        self.luna = kwargs.get("luna")
        self.logger.info("luna: {}".format(self.luna))

        if self.an and self.luna:
            rc = self._stat.SetLunaLucru(self.an, self.luna)
            self.logger.info("SetLunaLucru rc = {}".format(rc))
            if rc != 1:
                self.logger.error(repr(self.getListaErori()))
                1/0

        # TODO check this values ...
        self._stat.SetIDPartField('CodFiscal')
        self._stat.SetIDArtField('CodExtern')

        self._newProducts = []
        self.missingPartners = {}
        self.missingCodes = {}
        self.missingDefaultGest = {}
        self.productsMissingWMCodes =[]
        self.missingWMCodes = {}
        self.allowMissingDefaultGest = util.getCfgVal("products", "allowMissingDefaultGest")

        self.parteneri = self.getListaParteneri()
        self.products = self.getNomenclatorArticole()


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
        self._stat.SetNumeFirma(firma)


    def setLunaLucru(self, luna, an):
        self.logger.info(">>> {}()".format(inspect.stack()[0][3]))
        start = dt.now()

        self.luna = luna
        self.an = an
        self.logger.info("luna: {}".format(self.luna))
        self.logger.info("an: {}".format(self.an))

        if self._stat is None:
            return False

        rc = self._stat.SetLunaLucru(self.an, self.luna)
        if (rc != 1):
            self.logger.error(
                    repr(self.getListaErori())
                    )
            1/0

        self.logger.info("<<< {}() - duration = {}".format(inspect.stack()[0][3], dt.now() - start))
        return (rc == 1)


    def _colonListToDict(self, keys, myStr):
        ''' Generate a dict from a list of keys and a colon-separated string
        '''
        myDict = {}

        strData = myStr.split(';')
        count = min(len(strData), len(keys))
        for i in xrange(0, count):
            vals = strData[i].split("~")
            if len(vals) == 1:
                myDict[keys[i]] = vals[0]
            elif len(vals) > 1:
                myDict[keys[i]] = vals

        return myDict

    def _colonListToDict2(self, keys, myStr):
        ''' Generate a dict from a list of keys and a colon-separated string
        '''
        myDict = {}

        strData = myStr.split(';')
        for key in keys:
            myDict[key[1]] = strData[key[0]]

        # self.logger.info(myDict)

        return myDict


    def productsAreOK(self, gestoData, ignoreCodes=[]):
        self.logger.info(">>> {}()".format(inspect.stack()[0][3]))
        start = dt.now()

        ret = True
        self.logger.info("ignoreCodes: {}".format(ignoreCodes))

        for item in gestoData["items"]:

            if int(item["code"]) in ignoreCodes:
                self.logger.info("code: {}, ignore".format(item["code"]))
                continue

            if item["winMentorCode"] == "nil" \
            or item["winMentorCode"] == ""  \
            or not self.productExists(item["winMentorCode"]):
                ret = False
                if item["code"] not in self.missingCodes:
                    # only add a code once

                    if "operationDateHuman" in gestoData:
                        dateHuman = gestoData["operationDateHuman"]
                    elif "dateBeginHuman" in gestoData:
                        dateHuman = gestoData["dateBeginHuman"]

                    source = ""
                    if "source" in gestoData:
                        source = gestoData["source"]["name"]

                    relatedDocumentNo = ""
                    if "relatedDocumentNo" in gestoData:
                        relatedDocumentNo = gestoData["relatedDocumentNo"]

                    self.missingCodes[item["code"]] = {
                            "item": item,
                            "details": "{} - {} - {} - {}".format(dateHuman,
                                                             gestoData["branch"],
                                                             source,
                                                             relatedDocumentNo
                                                             )
                        }
            elif self.getProduct(item["winMentorCode"])["GestImplicita"] == "" \
            and item["winMentorCode"] not in self.allowMissingDefaultGest:
                ret = False
                if item["code"] not in self.missingDefaultGest:
                    # only add a code once
                    self.missingDefaultGest[item["code"]] = {
                            "item": item,
                            "details": "{} - {} - {} - {}".format(gestoData["operationDateHuman"],
                                                             gestoData["branch"],
                                                             gestoData["source"]["name"],
                                                             gestoData["relatedDocumentNo"],
                                                             )
                        }

        self.logger.info("ret: {}".format(ret))
        self.logger.info("<<< {}() - duration = {}".format(inspect.stack()[0][3], dt.now() - start))
        return ret


    def getTipGest(self, gestoData, ignoreCodes=[]):
        self.logger.info(">>> {}()".format(inspect.stack()[0][3]))
        start = dt.now()

        # verify if all products are of same type marfa/product
        ret = None

        for item in gestoData["items"]:
            if int(item["code"]) in ignoreCodes:
                continue

            if int(item["code"]) >= 5000:
                expectedRet = "MP"
            elif item["winMentorCode"].startswith("G_MARF"):
                expectedRet = "M"
            else:
                expectedRet = "P"

            if ret is None:
                ret = expectedRet

            if ret != expectedRet:
                ret = None
                break

        self.logger.info("ret: {}".format(ret))
        self.logger.info("<<< {}() - duration = {}".format(inspect.stack()[0][3], dt.now() - start))
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
            parteneri.append(self._colonListToDict(keys, partenerStr))

        self.multiplePartenerIDs = {}
        retParteneri = {}
        for p in parteneri:
            id = util.fixupCUI(p["idPartener"])
            # self.logger.debug("{} - {} ".format(p["idPartener"], id))
            if id in retParteneri:
                if id not in self.multiplePartenerIDs:
                    self.multiplePartenerIDs[id] = p
            else:
                retParteneri[id] = p

        self.logger.debug("partners count: {}".format(len(retParteneri)))
        # self.logger.debug("partners : {}".format(retParteneri))

        return retParteneri


    def getNomenclatorArticole(self):
        keys = [
            [0, "CodExternIntern"],
            [1, "Denumire"],
            [2, "DenUM"],
            [3, "PretVanzareFaraTVA"],
            [8, "GestImplicita"],
            [10, "CotaTVA"],
            [31, "PretVanzareCuTVA"],
        ]

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

        produse = []
        for idx, prodStr in enumerate(lista):
            # self.logger.info(prodStr)
            produse.append(self._colonListToDict2(keys, prodStr))

        ret = { p["CodExternIntern"] : p for p in produse }
        self.logger.debug("products count: {}".format(len(ret)))
        # self.logger.info(json.dumps(
        #                     ret,
        #                     sort_keys=True, indent=4, separators=(',', ': '), default=util.defaultJSON))

        return ret


    def getProducts(self):
        return self.products


    def getProduct(self, id):
        return self.products[id]


    def partenerExists(self, partenerID):
        self.logger.info(">>> {}()".format(inspect.stack()[0][3]))
        start = dt.now()

        self.logger.info("partenerID: {}".format(partenerID))

        if partenerID not in self.parteneri:
            ret = False
        else:
            ret = True

        self.logger.info("ret: {}".format(ret))
        self.logger.info("<<< {}() - duration = {}".format(inspect.stack()[0][3], dt.now() - start))
        return ret


    def getPartener(self, partenerID):
        self.logger.info(">>> {}()".format(inspect.stack()[0][3]))
        start = dt.now()

        self.logger.info("partenerID: {}".format(partenerID))

        if partenerID not in self.parteneri:
            ret = None
        else:
            ret = self.parteneri[partenerID]

        self.logger.info("ret: {}".format(ret))
        self.logger.info("<<< {}() - duration = {}".format(inspect.stack()[0][3], dt.now() - start))
        return ret


    def productExists(self, code):
        if code not in self.products:
            return False
        else:
            return True


    def _dictToColonList(self, keys, args, separator = ";", forceAbs = False):
        pd = []
        for key in keys:
            val = args.get(key, "") if isinstance(args, dict) else args[key]
            if util.isArray(val):
                # It's an iterable type (ex: array, tuple), iterate it and separate with "~"
                nKeys = range(len(val))
                val = self._dictToColonList(nKeys, val, "~")
            if isinstance(val, dt):
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

        items = kwargs.get("items", [])

        # Header factura
        txtWMDoc = (
            "[InfoPachet]\n"
            "AnLucru={}\n"
            "LunaLucru={}\n"
            "TipDocument={}\n"
            "TotalFacturi={}\n"
            "\n"
            ).format(
                self.an,
                self.luna,
                "FACTURA INTRARE",
                1,
                )

        # Factura
        txtWMDoc += "[Factura_{}]\n".format(1)
        txtWMDoc += "Operatie=A\n"
        txtWMDoc += "SerieDoc={}\n".format(kwargs.get("serieDoc", ""))
        txtWMDoc += "NrDoc={}\n".format(kwargs.get("nrDoc", ""))
        txtWMDoc += "NrNIR={}\n".format(util.getNextDocumentNumber("NIR"))
        txtWMDoc += "SimbolCarnetNir={}\n".format("GNIR")
        txtWMDoc += "Data={:%d.%m.%Y}\n".format(kwargs.get("data", dt.now()))
        txtWMDoc += "DataNir={:%d.%m.%Y}\n".format(kwargs.get("dataNir", None))
        # txtWMDoc += "Scadenta={:%d.%m.%Y}\n".format(kwargs.get("scadenta", dt.now()))
        txtWMDoc += "TotalArticole={}\n".format(len(items))
        txtWMDoc += "CodFurnizor={}\n".format(kwargs.get("codFurnizor", ""))
        if kwargs.get("TVAincasare") is True:
            txtWMDoc += "TVAincasare={}\n".format("D")
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

        for idx, item in enumerate(items):
            txtProd = self._dictToColonList(keys, item)
            txtWMDoc += "Item_{}={}\n".format(idx + 1, txtProd) # articolele incep de la 1

        self.logger.debug("txtWMDoc: \n{}".format(txtWMDoc))

        fact = txtWMDoc.split("\n")

        self._stat.SetDocsData(fact)

        rc = self._stat.FactIntrareValida()
        if rc != 1:
            return False

        rc = self._stat.ImportaFactIntrare()
        return (rc == 1)


    def importaFacturaIesire(self, **kwargs):
        items = kwargs.get("items", [])

        self.logger.info(json.dumps(
                            items,
                            sort_keys=True, indent=4, separators=(',', ': '), default=util.defaultJSON))

        # Header factura
        txtWMDoc = (
            "[InfoPachet]\n"
            "AnLucru={}\n"
            "LunaLucru={}\n"
            "TipDocument={}\n"
            "TotalFacturi={}\n"
            "\n"
            ).format(
                self.an,
                self.luna,
                "FACTURA IESIRE",
                1,
                )

        # Discount=6.7

        # Factura
        txtWMDoc += "[Factura_{}]\n".format(1)
        txtWMDoc += "Operatie=A\n"
        txtWMDoc += "Operat=D\n"
        # txtWMDoc += "SerieDoc={}\n".format(kwargs.get("serieDoc", ""))
        # txtWMDoc += "NrDoc={}\n".format(util.getNextDocumentNumber("FACTI"))
        txtWMDoc += "NrDoc={}\n".format(kwargs.get("nrDoc", ""))
        txtWMDoc += "SimbolCarnet={}\n".format("FI_G")
        txtWMDoc += "SimbolCarnetLivr={}\n".format("DL_G")
        txtWMDoc += "NrLivr={}\n".format(util.getNextDocumentNumber("LIV"))
        txtWMDoc += "Data={:%d.%m.%Y}\n".format(kwargs.get("data", dt.now()))
        txtWMDoc += "TotalArticole={}\n".format(len(items))
        txtWMDoc += "Moneda={}\n".format("LEI")
        txtWMDoc += "Curs={}\n".format(1)
        txtWMDoc += "CodClient={}\n".format(kwargs.get("codClient", ""))
        txtWMDoc += "CasaDeMarcat=D\n"
        if kwargs.get("Discount") is True:
            txtWMDoc += "Discount={:.4f}\n".format(kwargs.get("discount"))
        txtWMDoc += "Observatii={}\n".format(kwargs.get("observatii", ""))

        # Adauga items in factura
        txtWMDoc += "\n[Items_{}]\n".format(1)
        keys = (
                "codExternArticol",
                "um",
                "cant",
                "opPrice",
                "simbGest"
                )

        for idx, item in enumerate(items, start=1):
            txtProd = self._dictToColonList(keys, item)
            txtWMDoc += "Item_{}={}\n".format(idx, txtProd)

        self.logger.debug("txtWMDoc: \n{}".format(txtWMDoc))

        fact = txtWMDoc.split("\n")

        self._stat.SetDocsData(fact)
        rc = self._stat.DateValide()
        if rc != 1:
            self.logger.debug("rc: {}".format(txtWMDoc))
            return False

        rc = self._stat.ImportaFacturi()
        return (rc == 1)


    def importaComenziGest(self, **kwargs):

        items = kwargs.get("items", [])

        # Header factura
        txtWMDoc = (
            "[InfoPachet]\n"
            "AnLucru={}\n"
            "LunaLucru={}\n"
            "Tipdocument={}\n"
            "TotalComenzi={}\n"
            "\n"
            ).format(
                self.an,
                self.luna,
                "COMANDA GESTIUNE",
                1,
                )

        # Comanda
        txtWMDoc += "[Comanda_{}]\n".format(1)
        txtWMDoc += "Operatie=A\n"
        # txtWMDoc += "NrDoc={}\n".format(util.getNextDocumentNumber("COM"))
        txtWMDoc += "NrDoc={}\n".format(kwargs.get("nrDoc", ""))
        txtWMDoc += "SimbolCarnet={}\n".format("COM_G")
        txtWMDoc += "Data={:%d.%m.%Y}\n".format(kwargs.get("data", dt.now()))
        txtWMDoc += "GestDest={}\n".format(kwargs.get("gestDest", ""))
        txtWMDoc += "TotalArticole={}\n".format(len(items))
        txtWMDoc += "Observatii={}\n".format(kwargs.get("observatii", ""))

        # Adauga items in comanda
        # codExtern articol;denum;cant;termen livrare;Observatii
        txtWMDoc += "\n[Items_{}]\n".format(1)
        keys = (
                "codExternArticol",
                "Denumire",
                "cant",
                "listPrice",
                "termenLivr"
                )

        for idx, item in enumerate(items):
            txtProd = self._dictToColonList(keys, item)
            txtWMDoc += "Item_{}={}\n".format(idx + 1, txtProd) # articolele incep de la 1

        self.logger.debug("txtWMDoc: \n{}".format(txtWMDoc))

        fact = txtWMDoc.split("\n")

        self._stat.SetDocsData(fact)

        rc = self._stat.ComenziGestValide()
        if rc != 1:
            return False

        rc = self._stat.ImportaComenziGest()
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
        self.products = self.getNomenclatorArticole()

        return (rc == 1)

    def addPartener(self, **kwargs):
        self.logger.info(">>> {}()".format(inspect.stack()[0][3]))
        start = dt.now()

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
            self.parteneri = self.getListaParteneri()
        else:
            self.logger.error(repr(self.getListaErori()))
            self.logger.info("<<< {}() - duration = {}".format(inspect.stack()[0][3], dt.now() - start))
            1/0

        self.logger.info("<<< {}() - duration = {}".format(inspect.stack()[0][3], dt.now() - start))
        return None


    def getFactura(self, partenerId, serie, nr, data, iesire=False):
        """ @return array de articole from Winmentor care corespund facturii

        """

        self.logger.info(">>> {}()".format(inspect.stack()[0][3]))
        start = dt.now()

        self.logger.info("partenerId: {}".format(partenerId))
        self.logger.info("serie: {}".format(serie))
        self.logger.info("nr: {}".format(nr))
        self.logger.info("data: {}".format(data))
        self.logger.info("iesire: {}".format(iesire))

        # make sure we have loaded the existing facturi
        month = data.strftime("%m")
        if iesire:
            self.getIesiri(month)
        else:
            self.getIntrari(month)

        # if not self.existaFactura(partenerId, serie, nr):
        #     self.logger.info("<<< {}() - duration = {}".format(inspect.stack()[0][3], dt.now() - start))
        #     return None

        # Format parameters to string
        data = data.strftime("%d.%m.%Y")
        try:
            nr = str(int(nr)) # if I have doc nrs that start with 0
        except ValueError:
            pass

        partenerId = str(partenerId)

        # if data not in self.intrari[month][partenerId]:
        #     ret = -1
        # el
        if iesire:
            facturi = self.iesiri
        else:
            facturi = self.intrari

        # self.logger.info(json.dumps(
        #                     facturi,
        #                     sort_keys=True, indent=4, separators=(',', ': '), default=util.defaultJSON))

        if partenerId not in facturi[month]:
            ret = None
        elif nr not in facturi[month][partenerId]:
            ret = None
        else:
            ret = facturi[month][partenerId][nr]

        if ret is None:
            self.logger.info("Factura nu exista")
        elif ret["data"] != data:
            self.logger.info("Factura are data modificata")
        else:
            self.logger.info(json.dumps(
                            ret,
                            sort_keys=True, indent=4, separators=(',', ': '), default=util.defaultJSON))

        self.logger.info("<<< {}() - duration = {}".format(inspect.stack()[0][3], dt.now() - start))
        return ret


    def transferExists(self, nrDoc, documentDate):
        """ @return daca transferul exista sau nu in Mentor
        """

        self.logger.info(">>> {}()".format(inspect.stack()[0][3]))
        start = dt.now()

        self.logger.info("nrDoc: {}".format(nrDoc))
        self.logger.info("documentDate: {}".format(documentDate))

        workDate = documentDate.strftime("%d.%m.%Y")

        # make sure we have loaded the existing transfers for the day
        if workDate not in self.transfers:
            self.transfers[workDate] = []

            transferuri, rc = self._stat.GetTransferuri(workDate, workDate)
            if rc != 0:
                self.logger.error(repr(self.getListaErori()))

            self.logger.info("{} transferuri".format(len(transferuri)))
            for item in transferuri:
                # self.logger.info(item)
                items = item.split(";")
                if items[0] not in self.transfers[workDate]:
                    self.transfers[workDate].append(items[0])

            # self.logger.info(json.dumps(
            #         self.transfers,
            #         sort_keys=True, indent=4, separators=(',', ': '), default=util.defaultJSON))

        if str(nrDoc) not in self.transfers[workDate]:
            ret = False
        else:
            ret = True

        if ret:
            self.logger.info("Transferul este adaugat deja")
        else:
            self.logger.info("Transferul nu exista in WinMentor")

        self.logger.info("<<< {}() - duration = {}".format(inspect.stack()[0][3], dt.now() - start))
        return ret


    def comandaExista(self, gestDest, nrDoc, data):
        """ @return daca comanda exista sau nu
        """

        self.logger.info(">>> {}()".format(inspect.stack()[0][3]))
        start = dt.now()

        self.logger.info("gestDest: {}".format(gestDest))
        self.logger.info("nrDoc: {}".format(nrDoc))
        self.logger.info("data: {}".format(data))

        # make sure we have loaded the existing supplyOrders

        if len(self.comenzi) == 0:
            comenziItems, rc = self._stat.GetInfoComenziGest()
            if rc != 0:
                self.logger.debug("rc = {}".format(rc))
                self.logger.error(repr(self.getListaErori()))
                1/0

            # self.logger.info(comenziItems)

            keys = (
                   "gestDest",
                   "data",
                   "nrDoc",
                    )

            for item in comenziItems:
                # self.logger.info(item)
                val = self._colonListToDict(keys, item)
                # self.logger.info(val)
                # 1/0
                if val["gestDest"] not in self.comenzi:
                    self.comenzi[val["gestDest"]]={}

                valNrDoc = int(val["nrDoc"])
                if valNrDoc not in self.comenzi[val["gestDest"]]:
                    self.comenzi[val["gestDest"]][valNrDoc]={
                        "items": [],
                        "data": val["data"]
                    }

            # self.logger.info(json.dumps(
            #         self.comenzi,
            #         sort_keys=True, indent=4, separators=(',', ': '), default=util.defaultJSON))

        if gestDest not in self.comenzi:
            self.logger.info("{} nu exista".format(gestDest))
            ret = False
        elif nrDoc not in self.comenzi[gestDest]:
            self.logger.info("{} nu exista".format(nrDoc))
            ret = False
        elif data != self.comenzi[gestDest][nrDoc]["data"]:
            self.logger.info("data comenzii este diferita: {}, {}".format(data, self.comenzi[gestDest][nrDoc]))
            ret = False
            1/0
        else:
            ret = True

        if ret:
            self.logger.info("Comanda este adaugata deja")
        else:
            self.logger.info("Comanda nu exista in WinMentor")

        self.logger.info("<<< {}() - duration = {}".format(inspect.stack()[0][3], dt.now() - start))
        return ret


    def getGestiuni(self):
        self.logger.info(">>> {}()".format(inspect.stack()[0][3]))
        start = dt.now()

        if self.gestiuni is None:
            gestiuni, rc = self._stat.GetListaGestiuni()
            self.gestiuni = {}
            if (rc == 0) and util.isArray(gestiuni):
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
        self.logger.info("<<< {}() - duration = {}".format(inspect.stack()[0][3], dt.now() - start))

        return self.gestiuni


    def getIntrari(self, month):
        self.logger.info(">>> {}()".format(inspect.stack()[0][3]))
        start = dt.now()

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

            if (rc == 0) and util.isArray(intrariItems):
                # self.logger.info(intrariItems)
                # 1/0

                for item in intrariItems:
                    val = self._colonListToDict(keys, item)
                    # self.logger.info(val)
                    # 1/0
                    if val["partenerId"] not in self.intrari[month]:
                        self.intrari[month][val["partenerId"]]={}
                    if val["nrDoc"] not in self.intrari[month][val["partenerId"]]:
                        self.intrari[month][val["partenerId"]][val["nrDoc"]]={
                            "items": [],
                            "data": val["data"]
                        }

                    self.intrari[month][val["partenerId"]][val["nrDoc"]]["items"].append(val)

                    # self.logger.info(self.intrari)
                    # 1/0
            else:
                self.logger.debug("rc = {}".format(rc))
                self.logger.error(repr(self.getListaErori()))

        # self.logger.info(self.intrari)
        # 1/0
        self.logger.info("<<< {}() - duration = {}".format(inspect.stack()[0][3], dt.now() - start))


    def getIesiri(self, month):
        self.logger.info(">>> {}()".format(inspect.stack()[0][3]))
        start = dt.now()

        if month not in self.iesiri:
            self.iesiri[month]={}
            # Salveaza toate iesirile pentru factura respectiva

            keys = (
                   "nrDoc",
                   "data",
                   "partenerId",
                    )

            iesiriItems, rc = self._stat.GetIesiri("15.03.2018", "15.03.2018")
            # self.logger.info(iesiriItems)

            if rc != 0:
                self.logger.debug("rc = {}".format(rc))
                self.logger.error(repr(self.getListaErori()))
                1/0

            if (rc == 0) and util.isArray(iesiriItems):
                for item in iesiriItems:
                    # self.logger.info(item)
                    val = self._colonListToDict(keys, item)
                    # self.logger.info(val)
                    # 1/0
                    if val["partenerId"] not in self.iesiri[month]:
                        self.iesiri[month][val["partenerId"]]={}
                    if val["nrDoc"] not in self.iesiri[month][val["partenerId"]]:
                        self.iesiri[month][val["partenerId"]][val["nrDoc"]]={
                            "items": [],
                            "data": val["data"]
                        }

                    # self.iesiri[month][val["partenerId"]][val["nrDoc"]]["items"].append(val)

                    # self.logger.info(self.iesiri)
                    # 1/0
            else:
                self.logger.error(repr(self.getListaErori()))

        self.logger.info(self.iesiri)
        self.logger.info("<<< {}() - duration = {}".format(inspect.stack()[0][3], dt.now() - start))


    def getGestiuneName(self, simbol):
        self.logger.info(">>> {}()".format(inspect.stack()[0][3]))
        start = dt.now()

        # make sure we have loaded gestiunile
        self.getGestiuni()

        self.logger.info("<<< {}() - duration = {}".format(inspect.stack()[0][3], dt.now() - start))
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
            send_email(subject, html_part, toEmails=util.getCfgVal("client", "notificationEmails"), location=False)


    def sendPartnersMail(self):
        if len(self.missingPartners) != 0 or len(self.multiplePartenerIDsForEmail)!=0:
            template = loader.get_template("mail/admin/WinMentorPartenersProblems.html")
            subject = "Probleme la parteneri in WinMentor"
            html_part = template.render({
                "subject": subject,
                "missingPartners": self.missingPartners,
                "multiplePartenerIDsForEmail": self.multiplePartenerIDsForEmail,
            })
            send_email(subject, html_part, toEmails=util.getCfgVal("client", "notificationEmails"), location=False)


    def genNrNir(self):
        """ Genereaza nr NIR pentru o factura noua

        """

        # rc = self._stat.GetNumarFactura("Note de receptie 2011")

        return "672267"
        # return rc


    def matchGestiune(self, name, tip="P", operation_id=None):
        """
        @param name: Nume destinatie din Gesto
        @param listaGestiuni: Lista gestiuni din WinMentor
        @param tip: tipul gestiunii M - marfa, P - produse

        """

        self.logger.info(">>> {}()".format(inspect.stack()[0][3]))
        start = dt.now()

        self.logger.info("name: {}".format(name))

        ret = None

        # Get gestiuni
        gestiuni = self.getGestiuni()
        # self.logger.debug("gestiuni: {}".format(gestiuni))

        matchStr = '^\s*([0-9]{1,4})\s*'
        simbolGestiuneSearch = name
        x = re.match(matchStr, name)
        if x:
            no = x.group(1)
            self.logger.debug(repr(no))

            # Find a "gestiune" that matches
            simbolGestiuneSearch = "Magazin {:02d}{}".format(int(no), tip)
            self.logger.debug("simbolGestiuneSearch: {}".format(simbolGestiuneSearch))

            for gestiune in gestiuni:
                # regex = r"^\s*" + re.escape(no) + "\s*Magazin"
                # found = re.match(regex, gestiune["simbol"], re.IGNORECASE)
                # if found:
                #     result.append(gestiune)
                # self.logger.debug("gestiune: {}".format(gestiune))
                if simbolGestiuneSearch == gestiune:
                    ret = gestiune
                    break

        if ret is None:
            template = loader.get_template("mail/admin/missingInventory.html")
            subject = "WinMentor - nu am gasit gestiunea >{}< - >{}<".format(simbolGestiuneSearch, name)
            html_part = template.render({
                "subject": subject,
                "operation_id": operation_id,
            })

            # self.logger.info("Gestiunile din WinMentor")
            # self.logger.info(self.gestiuni)

            send_email(
                    subject=subject,
                    msg = html_part,
                    toEmails=util.getCfgVal("client", "notificationEmails"),
                    location=False
                    )

            ret = None

        self.logger.info("ret: {}".format(ret))
        self.logger.info("<<< {}() - duration = {}".format(inspect.stack()[0][3], dt.now() - start))
        return ret


    def addReception(self, gestoData):
        self.logger.info(">>> {}()".format(inspect.stack()[0][3]))
        start = dt.now()

        self.logger.debug(json.dumps(
                            gestoData,
                            sort_keys=True,
                            indent=4,
                            separators=(',', ': '),
                            default=util.defaultJSON
                            )
                        )

        self.logger.info("documentNo: {}".format(gestoData["documentNo"]))
        self.logger.info("operationID: {}".format(gestoData["id"]))
        self.logger.info("source: {}".format(gestoData["source"]["name"]))
        self.logger.info("destination: {}".format(gestoData["destination"]["name"]))
        self.logger.info("simbolWinMentorReception: {}".format(gestoData["simbolWinMentorReception"]))
        self.logger.info("relatedDocumentNo: {}".format(gestoData["relatedDocumentNo"]))

        if len(gestoData["items"]) == 0:
            self.logger.info("Nu am nici un produs pe receptie")
            self.logger.info("<<< {}() - duration = {}".format(inspect.stack()[0][3], dt.now() - start))
            return

        if gestoData["relatedDocumentNo"] == "nil":
            msg = "Factura {}, {} nu are document de legatura.".format(gestoData["documentNo"], gestoData["destination"]["name"])
            subject = msg

            send_email(subject, msg, toEmails=util.getCfgVal("client", "notificationEmails"), location=False)

            self.logger.error(msg)
            self.logger.info("<<< {}() - duration = {}".format(inspect.stack()[0][3], dt.now() - start))
            return

        # eliminate strings at begin and end of relatedDocumentNo, fvz123, FCT-312
        rdnFormats = [
                {"f":'^([^0-9]*)([0-9]*)([^0-9]*)$', "i":1},
                {"f":'^([^-]*)(-)(.*)$', "i":2},
            ]

        found = False
        for rdnf in rdnFormats:
            try:
                gestoData["relatedDocumentNo"] = re.match(rdnf["f"], gestoData["relatedDocumentNo"]).groups()
                gestoData["relatedDocumentNo"] = gestoData["relatedDocumentNo"][rdnf["i"]]
                # gestoData["relatedDocumentNo"] = gestoData["relatedDocumentNo"][-9:]
                found = True
                break
            except AttributeError:
                pass

        if not found:
            subject = "Nu pot determina numarul facturii din: {}, {}".format(gestoData["relatedDocumentNo"], gestoData["destination"]["name"])
            msg = "Data: {}".format(gestoData["documentDateHuman"])
            msg += "\nLocatie: {}".format(gestoData["destination"]["name"])
            msg += "\nNumarul: {}".format(gestoData["relatedDocumentNo"])

            send_email(subject, msg, toEmails=util.getCfgVal("client", "notificationEmails"), location=False)

            self.logger.error(msg)
            self.logger.info("<<< {}() - duration = {}".format(inspect.stack()[0][3], dt.now() - start))
            return

        self.logger.info("relatedDocumentNo: {}".format(gestoData["relatedDocumentNo"]))

        ignoreCodes = []
        ignoreCodes = [1325, 1326, ]

        # verify I have all gesto codes and default gestiuni in WinMentor
        if not self.productsAreOK(gestoData, ignoreCodes):
            self.logger.info("Articole cu coduri nesetate sau gestiuni lipsa, nu adaug")
            self.logger.info("<<< {}() - duration = {}".format(inspect.stack()[0][3], dt.now() - start))
            return

        # # Get gestiuni
        # gestiune = self.getGestiune(gestoData["simbolWinMentor"])

        # Get partener from gesto
        gestoPartener = util.fixupCUI(gestoData["source"]["code"])
        self.logger.info("gestoPartener = {}".format(gestoPartener))

        if gestoPartener in self.multiplePartenerIDs:
            self.multiplePartenerIDsForEmail.append(gestoPartener)

            self.logger.info("Codul fiscal: {} apare de mai multe la parteneri, nu adaug")
            self.logger.info("<<< {}() - duration = {}".format(inspect.stack()[0][3], dt.now() - start))
            return

        # Seteaza luna si anul in WinMentor
        opDate = dt.utcfromtimestamp(gestoData["documentDate"])
        self.setLunaLucru(opDate.month, opDate.year)

        # Cod partener exact ca in Winmentor
        if not self.partenerExists(gestoPartener):
            if gestoData["source"]["code"] not in self.missingPartners:
                # only add a missing partener once
                self.missingPartners[gestoData["source"]["code"]] = {
                    "company": gestoData["source"],
                    "details": "{} - {} - {}".format(gestoData["operationDateHuman"],
                                                             gestoData["branch"],
                                                             gestoData["relatedDocumentNo"],
                                                             )
                    }

            self.logger.info("Partenerul {} de pe receptia gesto nu exista, nu adaug".format(gestoPartener))
            self.logger.info("<<< {}() - duration = {}".format(inspect.stack()[0][3], dt.now() - start))
            return

            # self.addPartener(
            #         codFiscal = gestoPartener,
            #         denumirePartener = gestoData["source"]["name"]
            #         )

            # if not self.partenerExists(gestoPartener):
            #     self.logger.error("Failed to add new partener correcly.")
            #     self.logger.info("<<< {}() - duration = {}".format(inspect.stack()[0][3], dt.now() - start))
            #     return

        wmPartenerID = self.getPartener(gestoPartener)["idPartener"]
        self.logger.info("wmPartenerID: {}".format(wmPartenerID))

        # Cauta daca exista deja o factura in Winmentor cu intrarea din gesto
        alreadyAdded = False
        fact = self.getFactura(
                partenerId = wmPartenerID,
                serie = "G",
                nr = gestoData["relatedDocumentNo"],
                data = opDate
                )

        # fact = None

        if fact is not None and len(fact["items"]) != 0:
            self.logger.info("Gasit intrare in winmentor.")

            gestoItemsCnt = 0
            for item in gestoData["items"]:
                if int(item["code"]) not in ignoreCodes:
                    gestoItemsCnt += 1

            if len(fact["items"]) != gestoItemsCnt:
                self.logger.error("Product list from gesto is different than product list from winmentor")
                subject = "Factura {} - {} importata incorect in Winmentor".format(gestoData["relatedDocumentNo"],
                                                                                   gestoData["source"]["name"])
                template = loader.get_template("mail/admin/incorrectReception.html")

                html_part = template.render({
                    "subject": subject,
                    "gestoData": gestoData,
                    "fact": fact,
                    'HOME_URL': settings.HOME_URL,
                })
                send_email(subject, html_part, location=False)
                # send_email(subject, html_part, toEmails=util.getCfgVal("client", "notificationEmails"), location=False)
                self.logger.info("<<< {}() - duration = {}".format(inspect.stack()[0][3], dt.now() - start))

                return
            else:
                # Verifica toate produsele din factura daca corespund cu cele din gesto
                alreadyAdded = True

                for artWm in fact["items"]:
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
                    self.logger.info("<<< {}() - duration = {}".format(inspect.stack()[0][3], dt.now() - start))
                    return

        # Get lista articole from gesto, create array of articole pentru factura
        articoleWMDoc = []
        observatii = "{}".format(gestoData["destination"]["name"])

        for item in gestoData["items"]:
            if int(item["code"]) in ignoreCodes:
                self.logger.info("ignora wmArticol: {}".format(wmArticol))
                continue

            wmArticol = self.getProduct(item["winMentorCode"])
            self.logger.info("wmArticol: {}".format(wmArticol))

            simbGest = wmArticol["GestImplicita"]
            april1st = datetime.datetime.strptime("2018-04-01", "%Y-%m-%d")
            if opDate > april1st:
                # s-a schimbat gestiunea articolelor, se face pentru fiecare magazin in parte.
                if simbGest in ["MP sandwich", "MP-Bauturi",]:
                    simbGest = "Magazin {}MP".format(gestoData["branch"][:2])

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
                observatii += "; "+item["name"]

        # Creaza factura import
        rc = self.importaFactIntrare(
                serieDoc="G",
                nrDoc = gestoData["relatedDocumentNo"],
                dataNir = opDate,
                data = dt.utcfromtimestamp(gestoData["relatedDocumentDate"]) if gestoData["relatedDocumentDate"] not in ("nil", None) else opDate,
                scadenta = opDate + timedelta(days = 1),
                codFurnizor = wmPartenerID,
                observatii= observatii,
                observatiiNIR=gestoData["destination"]["name"],
                items = articoleWMDoc,
                TVAincasare = gestoData["source"]["cashingInVAT"] if "cashingInVAT" in gestoData["source"] else False,
                )
        if rc:
            self.logger.info("SUCCESS: Adaugare factura")
        else:
            self.logger.error(repr(self.getListaErori()))
            1/0

        self.logger.info("<<< {}() - duration = {}".format(inspect.stack()[0][3], dt.now() - start))


    def addSupplyOrder(self, gestoData):
        self.logger.info(">>> {}()".format(inspect.stack()[0][3]))
        start = dt.now()

        # apar in WinMentor in comenzi de la gestiuni

        self.logger.debug(json.dumps(
                            gestoData,
                            sort_keys=True,
                            indent=4,
                            separators=(',', ': '),
                            default=util.defaultJSON
                            )
                        )

        self.logger.info("documentNo: {}".format(gestoData["documentNo"]))
        self.logger.info("operation id: {}".format(gestoData["id"]))
        self.logger.info("source: {}".format(gestoData["source"]["name"]))

        if len(gestoData["items"]) == 0:
            self.logger.info("Nu am nici un produs pe comanda")
            self.logger.info("<<< {}() - duration = {}".format(inspect.stack()[0][3], dt.now() - start))
            return

        # verify I have all gesto codes and default gestiuni in WinMentor
        if not self.productsAreOK(gestoData):
            self.logger.info("Articole cu coduri nesetate sau gestiuni lipsa, nu adaug")
            self.logger.info("<<< {}() - duration = {}".format(inspect.stack()[0][3], dt.now() - start))
            return

        # Seteaza luna si anul in WinMentor
        opDate = dt.utcfromtimestamp(gestoData["documentDate"])
        self.setLunaLucru(opDate.month, opDate.year)

        # Get lista articole from gesto, create array of articole pentru comanda
        # materia prima si marga ajung in gestiuni diferite
        # materia prima are cod > 5000
        for i in range(2):
            articoleWMDoc = []
            observatii = ""

            if i==0:
                # materia prima
                gestDest = "Magazin {}MP".format(gestoData["branch"][:2])
            else:
                # marfa
                gestDest = "Magazin {}P".format(gestoData["branch"][:2])

            # newNrDocDate = datetime.datetime.strptime("2018-07-05", "%Y-%m-%d")
            # if opDate > newNrDocDate:
            #     if gestoData["documentNo"] > 99999999:
            #         1/0
            #     nrDoc = (int(gestoData["branch"][:2])*100 + i) * 100000000 + gestoData["documentNo"]
            # else:
            #     nrDoc = (int(gestoData["branch"][:2])*100 + i) * 100000 + int(str(gestoData["documentNo"])[-5:])
            nrDoc = (int(gestoData["branch"][:2])*100 + i) * 100000 + int(str(gestoData["documentNo"])[-5:])

            self.logger.info("nrDoc: {}".format(nrDoc))

            # Cauta daca exista dej o comanda in Winmentor cu intrarea din gesto
            if self.comandaExista(
                    gestDest = gestDest,
                    nrDoc = nrDoc,
                    data = "{:%d.%m.%Y}".format(opDate),
                    ):
                self.logger.info("<<< {}() - duration = {}".format(inspect.stack()[0][3], dt.now() - start))
                return

            observatii = "{}".format(gestoData["source"]["name"])

            for item in gestoData["items"]:
                # sari peste daca vreau materia prima si produsul nu e materie prima sau
                # daca vreau marfa si produsul nu e marfa
                if i==0 and int(item["code"]) < 5000 \
                or i==1 and int(item["code"]) >= 5000: # marfa
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
                            "termenLivr": "{:%d.%m.%Y}".format(opDate)
                        })

                if item["winMentorCode"].startswith("G_MARF"):
                        observatii += "; "+item["name"]

            if len(articoleWMDoc) > 0:
                # Creaza comanda
                rc = self.importaComenziGest(
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

        self.logger.info("<<< {}() - duration = {}".format(inspect.stack()[0][3], dt.now() - start))


    def addSale(self, gestoData):
        self.logger.info(">>> {}()".format(inspect.stack()[0][3]))
        start = dt.now()
        # in WinMentor sunt facturi de iesire

        self.logger.debug(json.dumps(
                            gestoData,
                            sort_keys=True,
                            indent=4,
                            separators=(',', ': '),
                            default=util.defaultJSON
                            )
                        )

        self.logger.info("documentNo: {}".format(gestoData["documentNo"]))
        self.logger.info("operationID: {}".format(gestoData["id"]))
        self.logger.info("source: {}".format(gestoData["source"]["name"]))
        self.logger.info("destination: {}".format(gestoData["destination"]["name"]))
        self.logger.info("simbolWinMentorReception: {}".format(gestoData["simbolWinMentorReception"]))
        self.logger.info("relatedDocumentNo: {}".format(gestoData["relatedDocumentNo"]))

        if len(gestoData["items"]) == 0:
            self.logger.info("Nu am nici un produs pe vanzare")
            self.logger.info("<<< {}() - duration = {}".format(inspect.stack()[0][3], dt.now() - start))
            return

        ignoreCodes = [ 832, 830, 831, 834, 841, 1325, 1302, 840, 862, 1200, 1510, 825, 5503,]
        # verify I have all gesto codes and default gestiuni in WinMentor
        if not self.productsAreOK(gestoData, ignoreCodes):
            self.logger.info("Articole cu coduri nesetate sau gestiuni lipsa, nu adaug")
            self.logger.info("<<< {}() - duration = {}".format(inspect.stack()[0][3], dt.now() - start))
            return

        # Get partener from gesto
        gestoPartener = util.fixupCUI(gestoData["destination"]["code"])
        self.logger.info("gestoPartener = {}".format(gestoPartener))

        if gestoPartener in self.multiplePartenerIDs:
            self.multiplePartenerIDsForEmail.append(gestoPartener)

            self.logger.info("Codul fiscal: {} apare de mai multe la parteneri, nu adaug")
            self.logger.info("<<< {}() - duration = {}".format(inspect.stack()[0][3], dt.now() - start))
            return

        # Seteaza luna si anul in WinMentor
        opDate = dt.utcfromtimestamp(gestoData["documentDate"])
        self.setLunaLucru(opDate.month, opDate.year)

        # Cod partener exact ca in Winmentor
        if not self.partenerExists(gestoPartener):
            if gestoData["destination"]["code"] not in self.missingPartners:
                # only add a missing partener once
                self.missingPartners[gestoData["destination"]["code"]] = {
                    "company": gestoData["destination"],
                    "details": "{} - {}".format(gestoData["operationDateHuman"],
                                                             gestoData["branch"],
                                                             )
                    }

            self.logger.error("Partenerul {} de pe vanzare gesto nu exista, nu adaug vanzarea facturata".format(gestoPartener))
            self.logger.info("<<< {}() - duration = {}".format(inspect.stack()[0][3], dt.now() - start))
            return

        wmPartenerID = self.getPartener(gestoPartener)["idPartener"]
        self.logger.info("wmPartenerID: {}".format(wmPartenerID))

        # Cauta daca exista deja o factura in Winmentor cu intrarea din gesto
        alreadyAdded = False
        fact = self.getFactura(
                partenerId = wmPartenerID,
                serie = "G",
                nr = gestoData["relatedDocumentNo"],
                data = opDate,
                iesire = True,
                )

        self.logger.info("fact: {}".format(fact))

        if fact is not None:
            self.logger.info("Gasit intrare in winmentor.")
            self.logger.info("Factura e deja adaugata")
            self.logger.info("<<< {}() - duration = {}".format(inspect.stack()[0][3], dt.now() - start))
            return

        # Get lista articole from gesto, create array of articole pentru factura
        articoleWMDoc = []
        observatii = ""

        vat_total = {"9": 0, "19": 0}
        for item in gestoData["items"]:
            key = str(int(item["vat"]))
            self.logger.debug("{} * {} = {}".format(item["qty"], item["opPrice"], item["qty"] * item["opPrice"]))
            vat_total[key] += item["qty"] * item["opPrice"]
            # self.logger.debug(vat_total[key])

        self.logger.debug(vat_total)

        for (key, total) in vat_total.items():
            if total != 0:
                winMentorCode = "G_VZBF{}".format(key)

                wmArticol = self.getProduct(winMentorCode)
                self.logger.info("wmArticol: {}".format(wmArticol))

                # Adauga produs la lista produse factura
                articoleWMDoc.append(
                        {
                            "codExternArticol": winMentorCode,
                            "um": wmArticol["DenUM"],
                            "cant": 1,
                            "opPrice": round(total / (1 + float(key) / 100), 2),
                            # "simbGest": gestoData["simbolWinMentor"]
                            # "simbGest": wmArticol["GestImplicita"]
                            "simbGest": "DepProdFinite"
                        })

        observatii= "{} - {}, {}".format(opDate.strftime("%d/%m/%Y"), gestoData["documentNo"], gestoData["source"]["name"])

        # Creaza factura de iesire
        rc = self.importaFacturaIesire(
                gestDest="Magazin {}MP".format(gestoData["branch"][:2]),
                nrDoc=gestoData["relatedDocumentNo"].split("/")[1],
                data=opDate,
                observatii=observatii,
                items=articoleWMDoc,
                codClient=wmPartenerID,
                )
        if rc:
            self.logger.info("SUCCESS: Adaugare factura de iesire")
        else:
            errors = self.getListaErori()
            self.logger.info(errors)

            for error in errors:
                if "213;" in error:
                    # "213;Nu gasesc informatii privind partenerul cu codul precizat Factura_1"
                    1/0

        self.logger.info("<<< {}() - duration = {}".format(inspect.stack()[0][3], dt.now() - start))


    def importaMonetare(self, **kwargs):
        items = kwargs.get("items", [])

        # Header transfer
        txtWMDoc = (
            "[InfoPachet]\n"
            "AnLucru={}\n"
            "LunaLucru={}\n"
            "Tipdocument={}\n"
            "TotalMonetare={}\n"
            "\n"
            ).format(
                self.an,
                self.luna,
                "MONETAR",
                1,
                )

        # Transfer
        txtWMDoc += "[Monetar_{}]\n".format(1)
        txtWMDoc += "Operat={}\n".format("N")
        txtWMDoc += "NrDoc={}\n".format(util.getNextDocumentNumber("MON"))
        txtWMDoc += "SimbolCarnet={}\n".format("M_G")
        txtWMDoc += "Operatie={}\n".format("A")
        txtWMDoc += "CasaDeMarcat={}\n".format("D")
        txtWMDoc += "NumarBonuri={}\n".format(kwargs.get("clientsNo", ""))
        txtWMDoc += "Data={:%d.%m.%Y}\n".format(kwargs.get("data"))
        txtWMDoc += "CasaCash={}\n".format("Casa lei")
        txtWMDoc += "CasaCard={}\n".format("Incasare card")
        txtWMDoc += "CasaBonValoric={}\n".format("Tichete")
        txtWMDoc += "TotalArticole={}\n".format(len(items))
        payment = kwargs.get("payment")
        txtWMDoc += "CEC={}\n".format(payment["bank transfer"] if "bank transfer" in payment else 0)
        txtWMDoc += "CARD={}\n".format(payment["card"] if "card" in payment else 0)
        txtWMDoc += "BONVALORIC={}\n".format(payment["food vouchers"] if "food vouchers" in payment else 0)
        txtWMDoc += "Observatii={}\n".format(kwargs.get("observatii", ""))
        txtWMDoc += "Discount={}\n".format(0)
        txtWMDoc += "TVADiscount={}\n".format(0)
        txtWMDoc += "SimbolCarnetLivr={}\n".format("DL_G")
        txtWMDoc += "NrLivr={}\n\n".format(util.getNextDocumentNumber("LIV"))

        # Adauga items in monetar
        txtWMDoc += "\n[Items_{}]\n".format(1)
        keys = (
                "codExternArticol",
                "um",
                "cant",
                "pret",
                "simbGest",
                )

        prodIdx = {}
        prodIdx["G_PROD_9"] = 1
        prodIdx["G_MARF_19"] = 2
        prodIdx["G_MARF_9"] = 3
        prodIdx["G_PROD_19"] = 4

        for item in items:
            txtProd = self._dictToColonList(keys, item)
            key = item["codExternArticol"][:item["codExternArticol"].rfind("_")]
            self.logger.debug("key: {}".format(key))
            self.logger.debug("idx: {}".format(prodIdx[key]))
            txtWMDoc += "Item_{}={}\n".format(prodIdx[key], txtProd) # articolele incep de la 1

        self.logger.debug("txtWMDoc: \n{}".format(txtWMDoc))

        fact = txtWMDoc.split("\n")

        self._stat.SetDocsData(fact)

        rc = self._stat.MonetareValide()
        if rc != 1:
            return False

        rc = self._stat.ImportaMonetare()
        return (rc == 1)


    def addMonetare(self, gestoData):
        self.logger.info(">>> {}()".format(inspect.stack()[0][3]))
        start = dt.now()

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
            self.logger.info("<<< {}() - duration = {}".format(inspect.stack()[0][3], dt.now() - start))
            return

        # Get gestiune in WinMentor
        # wmGestiune = self.matchGestiune(gestoData["branch"])

        # Seteaza luna si anul in WinMentor
        opDate = dt.utcfromtimestamp(gestoData["dateBegin"])
        self.setLunaLucru(opDate.month, opDate.year)

        # verify I have all gesto codes and default gestiuni in WinMentor
        # if not self.productsAreOK(gestoData):
        #     self.logger.info("Articole cu coduri nesetate sau gestiuni lipsa, nu adaug")
        #     self.logger.info("<<< {}() - duration = {}".format(inspect.stack()[0][3], dt.now() - start))
        #     return

       #  Get lista articole from gesto, create array of articole pentru factura

        newItems = {}
        ret = True

        for item in gestoData["items"]:
            if item["winMentorCode"].startswith("G_MARF"):
                codExternArticol = item["winMentorCode"]
            else:
                codExternArticol = "G_PROD_{}_{}".format(item["vat"], gestoData["branch"][:2])

            if not self.productExists(codExternArticol):
                ret = False
                if codExternArticol not in self.missingWMCodes:
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

                if codExternArticol not in newItems:
                    newItems[codExternArticol] = {
                                "codExternArticol": codExternArticol,
                                "um": wmArticol["DenUM"],
                                "cant": 1,
                                "pret": 0,
                                "simbGest": wmArticol["GestImplicita"]
                            }

                newItems[codExternArticol]["pret"] += item["opVal"]

        self.logger.info("newItems: {}".format(newItems))

        if ret == True:
            # Creaza transferul doar daca am coduri pentru toate produsele

            articoleWMDoc = []
            for (key, item) in newItems.items():
                articoleWMDoc.append(
                        {
                            "codExternArticol": item["codExternArticol"],
                            "um": item["um"],
                            "cant": item["cant"],
                            "pret": item["pret"],
                            "simbGest": item["simbGest"]
                            }
                        )

            rc = self.importaMonetare(
                    data = opDate,
                    items = articoleWMDoc,
                    payment = gestoData["payment"],
                    observatii = gestoData["branch"],
                    clientsNo = gestoData["clientsNo"] if gestoData["clientsNo"] not in ("nil", None) else 0,
                    )

            if rc:
                self.logger.info("SUCCESS: Adaugare monetar")
            else:
                self.logger.error(repr(self.getListaErori()))

        self.logger.info("<<< {}() - duration = {}".format(inspect.stack()[0][3], dt.now() - start))


    def importaTransfer(self, **kwargs):
        items = kwargs.get("items", [])

        # Header transfer
        txtWMDoc = (
            "[InfoPachet]\n"
            "AnLucru={}\n"
            "LunaLucru={}\n"
            "Tipdocument={}\n"
            "TotalTransferuri={}\n"
            "\n"
            ).format(
                self.an,
                self.luna,
                "TRANSFER",
                1,
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
        txtWMDoc += "SimbolCarnetLivr={}\n".format("DL_G")
        txtWMDoc += "NrLivr={}\n".format(util.getNextDocumentNumber("LIV"))
        txtWMDoc += "SimbolCarnetNir={}\n".format("GNIR")
        txtWMDoc += "NrNIR={}\n".format(util.getNextDocumentNumber("NIR"))
        txtWMDoc += "Observatii={}\n".format(kwargs.get("observatii", ""))
        txtWMDoc += "ObservatiiNIR={}\n\n".format(kwargs.get("observatii", ""))

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


    def ImportaNotePredare(self, **kwargs):
        items = kwargs.get("items", [])

        # Header transfer
        txtWMDoc = (
            "[InfoPachet]\n"
            "AnLucru={}\n"
            "LunaLucru={}\n"
            "Tipdocument={}\n"
            "TotalNotePredare={}\n"
            "\n"
            ).format(
                self.an,
                self.luna,
                "NOTA PREDARE",
                1
                )

        txtWMDoc += "[Nota_{}]\n".format(1)
        txtWMDoc += "SimbolCarnet={}\n".format("NP_G")
        txtWMDoc += "NrDoc={}\n".format(util.getNextDocumentNumber("NP"))
        txtWMDoc += "SimbolCarnetNir={}\n".format("GNIR")
        txtWMDoc += "NrNIR={}\n".format(util.getNextDocumentNumber("NIR"))
        txtWMDoc += "Data={:%d.%m.%Y}\n".format(kwargs.get("data"))
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

        for idx, item in enumerate(items):
            txtProd = self._dictToColonList(keys, item)
            txtWMDoc += "Item_{}={}\n".format(idx + 1, txtProd) # articolele incep de la 1

        self.logger.debug("txtWMDoc: \n{}".format(txtWMDoc))

        fact = txtWMDoc.split("\n")

        self._stat.SetDocsData(fact)

        rc = self._stat.NotePredareValide()
        if rc != 1:
            return False

        rc = self._stat.ImportaNotePredare()
        return (rc == 1)


    def addBonConsum(self, **kwargs):
        items = kwargs.get("items", [])

        # Header transfer
        txtWMDoc = (
            "[InfoPachet]\n"
            "AnLucru={}\n"
            "LunaLucru={}\n"
            "Tipdocument={}\n"
            "TotalBonuri={}\n"
            "\n"
            ).format(
                self.an,
                self.luna,
                "BON DE CONSUM",
                1
                )

        # Transfer
        txtWMDoc += "[BON_{}]\n".format(1)
        txtWMDoc += "SimbolCarnet={}\n".format("BC_G")
        txtWMDoc += "NrDoc={}\n".format(util.getNextDocumentNumber("BC"))
        txtWMDoc += "Data={:%d.%m.%Y}\n".format(kwargs.get("data"))
        txtWMDoc += "GestConsum={}\n".format(kwargs.get("gestiune"))
        txtWMDoc += "Operatie={}\n".format("A")
        txtWMDoc += "Operat={}\n".format("N")
        txtWMDoc += "TotalArticole={}\n".format(len(items))
        txtWMDoc += "SimbolCarnetLivr={}\n".format("DL_G")
        txtWMDoc += "NrLivr={}\n".format(util.getNextDocumentNumber("LIV"))
        txtWMDoc += "Observatii={}\n".format(kwargs.get("observatii"))
        # txtWMDoc += "ObservatiiLivr={}\n\n".format(kwargs.get("observatiiLivr"))

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
            txtProd = self._dictToColonList(keys, item, forceAbs=True)
            txtWMDoc += "Item_{}={}\n".format(idx + 1, txtProd) # articolele incep de la 1

        self.logger.debug("txtWMDoc: \n{}".format(txtWMDoc))

        fact = txtWMDoc.split("\n")

        self._stat.SetDocsData(fact)

        rc = self._stat.BonuriConsumValide()
        if rc != 1:
            return False

        rc = self._stat.ImportaBonuriConsum()

        return (rc == 1)


    def getTransferuri(self, opDate):
        self.logger.info(">>> {}()".format(inspect.stack()[0][3]))
        start = dt.now()

        self.setLunaLucru(opDate.month, opDate.year)

        alreadyAdded = False
        transferuri, rc = self._stat.GetTransferuri()
        if rc != 0:
            self.logger.error(repr(self.getListaErori()))

        sources = util.getCfgVal("deliveryNote", "sources")
        destinations = util.getCfgVal("deliveryNote", "destinations")
        dnDate = "{}.{}.{}".format(opDate.day, opDate.month, opDate.year)

        self.logger.info("dnDate: {}".format(dnDate))

        company = util.getCfgVal("winmentor", "companyName")
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

            if source not in sources:
                continue
            if destination not in destinations:
                continue
            if date != dnDate:
                continue

            if source not in deliveryNotes:
                deliveryNotes[source] = {}

            if date not in deliveryNotes[source]:
                deliveryNotes[source][date] = {}

            if destination not in deliveryNotes[source][date]:
                deliveryNotes[source][date][destination] = {}

            if transferNo not in deliveryNotes[source][date][destination]:
                deliveryNotes[source][date][destination][transferNo] = []

            productCode = items[4]

            if items[4] == "":
                if items[5] not in self.productsMissingWMCodes:
                    ret = False
                    # only add a code once
                    self.productsMissingWMCodes.append(items[5])

            if items[6] != "":
                if company == "Andalusia":
                    opPrice = float(items[8].replace(",", "."))
                else:
                    opPrice = float(items[7].replace(",", "."))

                deliveryNotes[source][date][destination][transferNo].append({
                                "winMentorCode": items[4],
                                "name": items[5],
                                "opPrice": opPrice,
                                "listPrice": float(items[8].replace(",", ".")),
                                "qty": float(items[6].replace(",","."))
                        })

        self.logger.info(
                json.dumps(
                    deliveryNotes,
                    sort_keys=True,
                    indent=4,
                    separators=(',', ': '),
                    default=util.defaultJSON
                    )
                )

        if ret == False:
            deliveryNotes = {}

        self.logger.info(
                json.dumps(
                    deliveryNotes,
                    sort_keys=True,
                    indent=4,
                    separators=(',', ': '),
                    default=util.defaultJSON
                    )
                )

        ret = deliveryNotes
        self.logger.info("<<< {}() - duration = {}".format(inspect.stack()[0][3], dt.now() - start))
        return ret


    def addWorkOrders(self, gestoData):
        self.logger.info(">>> {}()".format(inspect.stack()[0][3]))
        start = dt.now()

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
            self.logger.info("<<< {}() - duration = {}".format(inspect.stack()[0][3], dt.now() - start))
            return

        # Get gestiune in WinMentor
        wmGestiune = self.matchGestiune(gestoData["branch"], )
        if wmGestiune is None:
            self.logger.info("Nu am gasit gestiunea")
            return

        # Seteaza luna si anul in WinMentor
        opDate = dt.utcfromtimestamp(gestoData["dateBegin"])
        self.setLunaLucru(opDate.month, opDate.year)

        ignoreCodes = []
        ignoreCodes = [1105, 819,]

        # verify I have all gesto codes and default gestiuni in WinMentor
        if not self.productsAreOK(gestoData, ignoreCodes):
            self.logger.info("Articole cu coduri nesetate sau gestiuni lipsa, nu adaug")
            self.logger.info("<<< {}() - duration = {}".format(inspect.stack()[0][3], dt.now() - start))
            return

            # Get lista articole from gesto, create array of articole pentru workOrders
        articoleWMDoc = []
        for item in gestoData["items"]:
            if int(item["code"]) in ignoreCodes:
                continue

            # Adauga produs la lista produse
            if self.isDrink(int(item["code"])):
                simbGest = "PF-Bauturi"
            elif self.isSdwSalad(int(item["code"])):
                simbGest = "PF Sandwich"
            else:
                # I need to have a gestiune for these articles too
                continue

            wmArticol = self.getProduct(item["winMentorCode"])
            self.logger.debug("wmArticol: \n{}".format(wmArticol))

            articoleWMDoc.append({
                        "codExternArticol": item["winMentorCode"],
                        "um": wmArticol["DenUM"],
                        "cant": item["qty"],
                        # "pret": item["listVal"]/item["qty"],
                        "pret": wmArticol["PretVanzareCuTVA"],
                        "simbGest": simbGest
                    })

        # Creaza transferul
        rc = self.importaTransfer(
                nrDoc=util.getNextDocumentNumber("NT"),
                simbolCarnet = "NT_G",
                data = opDate,
                gestiune = wmGestiune,
                items = articoleWMDoc,
                operat = "N",
                )

        if rc:
            self.logger.info("SUCCESS: Adaugare transfer")
        else:
            self.logger.error(repr(self.getListaErori()))

        self.logger.info("<<< {}() - duration = {}".format(inspect.stack()[0][3], dt.now() - start))


    def addWorkOrderFromOperation(self, gestoData):
        self.logger.info(">>> {}()".format(inspect.stack()[0][3]))
        start = dt.now()

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
            self.logger.info("Nu am nici un produs pe operatie")
            self.logger.info("<<< {}() - duration = {}".format(inspect.stack()[0][3], dt.now() - start))
            return

        # Seteaza luna si anul in WinMentor
        opDate = dt.utcfromtimestamp(gestoData["documentDate"])
        self.setLunaLucru(opDate.month, opDate.year)

        self.logger.info("documentNo: {}".format(gestoData["documentNo"]))
        self.logger.info("id: {}".format(gestoData["id"]))

        newNrDocDate = datetime.datetime.strptime("2018-07-05", "%Y-%m-%d")
        if opDate > newNrDocDate:
            if gestoData["documentNo"] > 9999999:
                1/0
            elif gestoData["documentNo"] < self.documentNoInitWeb:
                if gestoData["id"] in [59650919, 62057910, 63639647, ]:
                    nrDoc = (int(gestoData["branch"][:2]) * 10 + 1) * 1000000 + gestoData["documentNo"]
                elif gestoData["branch"] in ["43 Turda 1", ] \
                and gestoData["type"] == "return":
                    nrDoc = (int(gestoData["branch"][:2]) * 10 + gestoData["vcomID"] % 10) * 1000000 + gestoData["documentNo"]
                elif gestoData["id"] > 64756894:
                    nrDoc = (int(gestoData["branch"][:2]) * 10 + gestoData["vcomID"] % 10) * 1000000 + gestoData["documentNo"]
                else:
                    nrDoc = int(gestoData["branch"][:2]) * 10000000 + gestoData["documentNo"]
            else:
                nrDoc = int(gestoData["branch"][:2]) * 10000000 + gestoData["documentNo"]
        else:
            nrDoc = int(gestoData["branch"][:2]) * 1000000 + int(str(gestoData["documentNo"])[-6:])

        self.logger.info("nrDoc: {}".format(nrDoc))

        if self.transferExists(nrDoc, opDate):
            self.logger.info("<<< {}() - duration = {}".format(inspect.stack()[0][3], dt.now() - start))
            return

        ignoreCodes = []
        ignoreCodes = [1105,]

        # verify I have all gesto codes and default gestiuni in WinMentor
        if not self.productsAreOK(gestoData, ignoreCodes):
            self.logger.info("Articole cu coduri nesetate sau gestiuni lipsa, nu adaug")
            self.logger.info("<<< {}() - duration = {}".format(inspect.stack()[0][3], dt.now() - start))
            return

        tipGest = self.getTipGest(gestoData, ignoreCodes)
        if tipGest is None:
            template = loader.get_template("mail/admin/incorrectProductTypeReception.html")
            if gestoData["type"] == "reception":
                subject = "Receptia {} - {} cu probleme in WinMentor".format(gestoData["relatedDocumentNo"], gestoData["source"]["name"])
            elif gestoData["type"] == "return":
                subject = "Returul {} - {} cu probleme in WinMentor".format(gestoData["relatedDocumentNo"], gestoData["source"]["name"])
            html_part = template.render({
                "subject": subject,
                "gestoData": gestoData,
                'HOME_URL': settings.HOME_URL,
            })

            send_email(subject, html_part, toEmails=util.getCfgVal("client", "notificationEmails"), location=False)

            self.logger.info("<<< {}() - duration = {}".format(inspect.stack()[0][3], dt.now() - start))
            return

        simbGest = self.matchGestiune(gestoData["source"]["name"], tipGest, gestoData["id"])
        if simbGest is None:
            self.logger.info("Nu am gasit gestiunea")
            return

        if gestoData["type"] == "return":
            # wmGestiune = "DMR"
            wmGestiune = "DMP"
        else:
            wmGestiune = self.matchGestiune(gestoData["branch"], tipGest, gestoData["id"])

        # Get lista articole from gesto, create array of articole pentru workOrders
        articoleWMDoc = []
        for item in gestoData["items"]:
            if int(item["code"]) in ignoreCodes:
                continue

            wmArticol = self.getProduct(item["winMentorCode"])
            self.logger.debug("wmArticol: \n{}".format(wmArticol))

            if item["winMentorCode"].startswith("G_MARF"):
                codExternArticol = "{}{}".format(item["winMentorCode"][:-2], gestoData["source"]["name"][:2])
                pret = item["listPrice"]
            else:
                codExternArticol = item["winMentorCode"]
                if tipGest == "MP":
                    pret = 0
                else:
                    pret = wmArticol["PretVanzareFaraTVA"]

            articoleWMDoc.append({
                        "codExternArticol": codExternArticol,
                        "um": wmArticol["DenUM"],
                        "cant": item["qty"],
                        # "pret": item["listVal"]/item["qty"],
                        "pret": pret,
                        "simbGest": simbGest
                    })

        self.logger.info(articoleWMDoc)

        if gestoData["type"] == "return":
            simbolCarnet = "NTR_G"
        elif gestoData["type"] == "reception":
            simbolCarnet = "NTA_G"
        else:
            1/0

        # Creaza transferul
        rc = self.importaTransfer(
                nrDoc=nrDoc,
                simbolCarnet = simbolCarnet,
                data = opDate,
                gestiune = wmGestiune,
                operat = "D",
                items = articoleWMDoc,
                observatii = "{} - {}".format(gestoData["source"]["name"], gestoData["documentNo"])
                )

        if rc:
            self.logger.info("SUCCESS: Adaugare transfer")
        else:
            self.logger.error(repr(self.getListaErori()))

        self.logger.info("<<< {}() - duration = {}".format(inspect.stack()[0][3], dt.now() - start))


    def addIntrariDinProductie(self, gestoData):
        self.logger.info(">>> {}()".format(inspect.stack()[0][3]))
        start = dt.now()

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
            self.logger.info("Nu am nici un produs pe raport")
            self.logger.info("<<< {}() - duration = {}".format(inspect.stack()[0][3], dt.now() - start))
            return

        # Get gestiune in WinMentor
        # wmGestiune = self.matchGestiune(gestoData["branch"])
        wmGestiune = self.matchGestiune(gestoData["branch"], "DF")

        if wmGestiune is None:
            self.logger.info("Nu am gasit gestiunea")
            return

        # Seteaza luna si anul in WinMentor
        opDate = dt.utcfromtimestamp(gestoData["dateBegin"])
        self.setLunaLucru(opDate.month, opDate.year)

        ignoreCodes = []
        ignoreCodes = [1105, 819, ]

        # verify I have all gesto codes and default gestiuni in WinMentor
        if not self.productsAreOK(gestoData, ignoreCodes):
            self.logger.info("Articole cu coduri nesetate sau gestiuni lipsa, nu adaug")
            self.logger.info("<<< {}() - duration = {}".format(inspect.stack()[0][3], dt.now() - start))
            return

        # Get lista articole from gesto, create array of articole pentru workOrders
        articoleWMDoc = []
        for item in gestoData["items"]:
            if int(item["code"]) in ignoreCodes:
                continue

            # Adauga produs la lista produse
            wmArticol = self.getProduct(item["winMentorCode"])
            self.logger.debug("wmArticol: \n{}".format(wmArticol))

            articoleWMDoc.append({
                        "codExternArticol": item["winMentorCode"],
                        "um": wmArticol["DenUM"],
                        "cant": item["qty"],
                        # "pret": item["listVal"]/item["qty"],
                        "pret": wmArticol["PretVanzareFaraTVA"],
                        # "simbGest": wmArticol["GestImplicita"]
                        "simbGest": wmGestiune
                    })

        # Creaza transferul
        rc = self.ImportaNotePredare(
                data = opDate,
                gestiune = wmGestiune,
                items = articoleWMDoc
                )

        if rc:
            self.logger.info("SUCCESS: Adaugare nota predare/ nota intrare din productie")
        else:
            errors = repr(self.getListaErori())
            self.logger.error(errors)
            msg = "{}".format(errors)

            send_email(
                    subject = "WinMentor - Eroare la adaugare nota intrare din productie la {}, {}".format(gestoData["branch"], opDate),
                    msg = msg
                    )

        self.logger.info("<<< {}() - duration = {}".format(inspect.stack()[0][3], dt.now() - start))


    def addProductSummary(self, gestoData, opDate):
        self.logger.info(">>> {}()".format(inspect.stack()[0][3]))
        start = dt.now()

        # TODO comment me

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
            self.logger.info("Nu am nici un produs pe raport")
            self.logger.info("<<< {}() - duration = {}".format(inspect.stack()[0][3], dt.now() - start))
            return

        # Get gestiune in WinMentor
        wmGestiune = self.matchGestiune(gestoData["branch"])
        if wmGestiune is None:
            self.logger.info("Nu am gasit gestiunea")
            return

        # Seteaza luna si anul in WinMentor
        self.setLunaLucru(opDate.month, opDate.year)

        ignoreCodes = []
        ignoreCodes = [729, 5200, 5201, ]
        # verify I have all gesto codes and default gestiuni in WinMentor
        if not self.productsAreOK(gestoData, ignoreCodes):
            self.logger.info("Articole cu coduri nesetate sau gestiuni lipsa, nu adaug")
            self.logger.info("<<< {}() - duration = {}".format(inspect.stack()[0][3], dt.now() - start))
            return

            # Get lista articole from gesto, create array of articole pentru workOrders
        articoleWMDoc = []
        for item in gestoData["items"]:
            if int(item["code"]) in ignoreCodes:
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

            pret = wmArticol["PretVanzareFaraTVA"]
            if pret == "":
                pret = wmArticol["PretVanzareCuTVA"]

            articoleWMDoc.append({
                        "codExternArticol": item["winMentorCode"],
                        "um": wmArticol["DenUM"],
                        "cant": item["qty"],
                        # "pret": item["listVal"]/item["qty"],
                        "pret": pret,
                        "simbGest": wmArticol["GestImplicita"]
                        # "simbGest": "Magazin 20P"
                    })

        rc = self.addBonConsum(
                data = opDate,
                observatii = gestoData["branch"],
                observatiiLivr = gestoData["branch"],
                gestiune = wmGestiune,
                items = articoleWMDoc
                )

        if rc:
            self.logger.info("SUCCESS: Adaugare BonConsum")
        else:
            self.logger.error(repr(self.getListaErori()))

        self.logger.info("<<< {}() - duration = {}".format(inspect.stack()[0][3], dt.now() - start))

#
# UT Starts here
#
if __name__ == "__main__":
    winmentor = WinMentor(firma = 'PAN2016', an = 2017, luna = 7)
    rc = winmentor._stat.ExistaFacturaIntrare("RO 4844886","", 807460)
    print(repr(rc))
    print(repr(winmentor.getListaErori()))

    rc = winmentor.getFactura("RO 4844886", "", 807460, dt(day = 19, month = 7, year = 2017))
    print(len(rc))
    print(repr(winmentor.getListaErori()))

    # print(repr(winmentor.getListaFirme()))
    # print(repr(winmentor.getListaErori()))
    # prods = winmentor.getNomenclatorArticole()
    # print(repr(winmentor.getListaErori()))
    # for prod in prods:
    #     if prod['CodExternIntern'] == "1234455":
    #         print(repr(prod))

    # rc = winmentor.addPartener(
    #         codFiscal = 444446,
    #         denumirePartener = "Radu Cucu",
    #         idPartener = 11,
    #         localitateSediu = 12,
    #         adresaSediu = 13,
    #         telefonSediu = 14,
    #         persoaneContact = 15,
    #         # simbolClasa = 16,
    #         # simbolCategoriePret = 17,
    #         # idAgentImplicit = 18,
    #         nrRegistrulComert = 19,
    #         observatii = 20,
    #         # simbolBanca = 21,
    #         numeBanca = 22,
    #         localitateBanca = 23,
    #         contBanca = 24,
    #         ziImplicitaPlata = 25,
    #         numeSediuSecundar = 26,
    #         adresaSediuSecundar = 27,
    #         telefonSediuSecundar = 28,
    #         localitateSediuSecundar = 29,
    #         # idAgentSediuSecundar = 30
    #         )
    # if not rc:
    #     print(repr(winmentor.getListaErori()))

    # for a in xrange(20):
    #     rc = winmentor.addProduct(
    #             idArticol = 999000 + a,
    #             denumire = "Mere padurete",
    #             um = "buc",
    #             denProducator = "13",
    #             atributStoc = "14",
    #             dataUltimeiModificari = "16",
    #             codIntern = "444444",
    #             simbolClasa = "18",
    #             pret = 17.6
    #             )
    #     if not rc:
    #         print(repr(winmentor.getListaErori()))
    #     print("Gata")
    # a = winmentor.getListaParteneri()
    # for partener in a:
    #     print(repr(partener))
    # print("-- Start factura")
    # rc = winmentor.importaFactIntrare(
    #         logOn = "Master",
    #         nrDoc = "7123",
    #         nrNir = "672267",
    #         data = dt(2017, 07, 21),
    #         dataNir = dt(2017, 07, 21),
    #         scadenta = dt(2017, 07, 22),
    #         codFurnizor = "RO29963394",
    #         items = [
    #            {
    #                 "codExternArticol": "G_5101",
    #                 "um": "kg",
    #                 "cant": 27.,
    #                 "pret": 4.587037,
    #                 "simbGest": "Magazin1"
    #                 }
    #             ]
    #         )
    # if not rc:
    #     print(winmentor.getListaErori())
    #

    # winmentor.addProduct(
    #     idArticol = 12344555,
    #     denumire = "Pipote",
    #     cotaTVA = 9,
    #     codIntern = "fasfsdf"
    #     )
    # print(repr(winmentor.getListaErori()))
    #

    # winmentor.addPartener(
    #         idPartener = "TM12323",
    #         denumirePartener = "Adrian Lalaul",
    #         numeBanca = ("BCR", "BRD", "Raiffeisen")
    #         )
    #
