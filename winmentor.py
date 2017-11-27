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
from util import send_email
from django.template import loader, Context


class WinMentor(object):
    ''' classdocs
    '''

    parteneri = None
    multiplePartenerIDs = {}
    multiplePartenerIDsForEmail = []
    products = None
    gestiuni = None
    panemarCUI = None
    intrari = {}

    productCodesBauturi = [[1005, 1006], [700, 728], [731, 798],]
    productCodesSdwSalate = [[799, 882], [1100, 1150],]

    missingCodes = {}
    missingDefaultGest = {}


    def __init__(self, **kwargs):
        self.logger = logging.getLogger(__name__)

        self._fdm = pythoncom.LoadTypeLib('DocImpServer.tlb')
        self._stat = None

        if self._fdm is None:
            return

        for idx in xrange(0, self._fdm.GetTypeInfoCount()):
            fdoc = self._fdm.GetDocumentation(idx)

            if fdoc[0] == 'DocImpObject':
                type_iid = self._fdm.GetTypeInfo(idx).GetTypeAttr().iid
                self._stat = win32com.client.Dispatch(type_iid)

        if self._stat is None:
            return

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
        self.luna = luna
        self.an = an
        if self._stat is None:
            return False
        rc = self._stat.SetLunaLucru(an, luna)
        if (rc != 1):
            self.logger.error(
                    repr(self.getListaErori())
                    )
            1/0
        return (rc == 1)


    def setPanemarCUI(self, CUI):
        self.panemarCUI = util.fixupCUI(CUI)


    def getPanemarCUI(self):
        return self.panemarCUI


    def _colonListToDict(self, keys, myStr):
        ''' Generate a dict from a list of keys and a color-separated string
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


    def productsAreOK(self, items):
        self.logger.info(">>> {}()".format(inspect.stack()[0][3]))
        start = dt.now()

        ret = True

        for item in items:
            if item["winMentorCode"] == "nil" \
            or item["winMentorCode"] == ""  \
            or not self.productExists(item["winMentorCode"]):
                ret = False
                if item["code"] not in self.missingCodes:
                    # only add a code once
                    self.missingCodes[item["code"]] = item
            elif self.getProduct(item["winMentorCode"])["GestImplicita"] == "" \
            and item["winMentorCode"] not in self.allowMissingDefaultGest:
                ret = False
                if item["code"] not in self.missingDefaultGest:
                    # only add a code once
                    self.missingDefaultGest[item["code"]] = item

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

        produse = []
        for idx, prodStr in enumerate(lista):
            produse.append(self._colonListToDict(keys, prodStr))

        ret = { p["CodExternIntern"] : p for p in produse }
        self.logger.debug("products count: {}".format(len(ret)))
        # self.logger.info("products: {}".format(ret))

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


    def _dictToColonList(self, keys, args, separator = ";"):
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
            "TipDocument=FACTURA INTRARE\n"
            "TotalFacturi={}\n"
            "LogOn={}\n"
            "\n"
            ).format(
                self.an,
                self.luna,
                1,
                kwargs.get("logOn", "")
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
        txtWMDoc += "Data={:%d.%m.%Y}\n".format(kwargs.get("data", dt.now()))
        txtWMDoc += "DataNir={:%d.%m.%Y}\n".format(kwargs.get("dataNir", None))
        txtWMDoc += "Scadenta={:%d.%m.%Y}\n".format(kwargs.get("scadenta", dt.now()))
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

        itemStr = ""
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


    def existaFacturaIntrare(self, partenerId, serie, nr):
        self.logger.info(">>> {}()".format(inspect.stack()[0][3]))
        start = dt.now()

        self.logger.info("{} - {} - {}".format(partenerId, serie, nr))

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

        self.logger.info("<<< {}() - duration = {}".format(inspect.stack()[0][3], dt.now() - start))
        return ret


    def getFactura(self, partenerId, serie, nr, data):
        """ @return array de articole from Winmentor care corespund facturii

        """

        self.logger.info(">>> {}()".format(inspect.stack()[0][3]))
        start = dt.now()

        self.logger.info("partenerId: {}".format(partenerId))
        self.logger.info("serie: {}".format(serie))
        self.logger.info("nr: {}".format(nr))
        self.logger.info("data: {}".format(data))

        if not self.existaFacturaIntrare(partenerId, serie, nr):
            self.logger.info("<<< {}() - duration = {}".format(inspect.stack()[0][3], dt.now() - start))
            return None

        # make sure we have loaded the existing intrari
        month = data.strftime("%m")
        self.getIntrari(month)

        # Format parameters to string
        data = data.strftime("%d.%m.%Y")
        nr = str(int(nr)) # if I have doc nrs that start with 0
        partenerId = str(partenerId)

        ret = self.intrari[month][partenerId][data][nr]
        self.logger.info(json.dumps(
                            ret,
                            sort_keys=True, indent=4, separators=(',', ': '), default=util.defaultJSON))

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
        if len(self.missingCodes) or len(self.missingDefaultGest):
            template = loader.get_template("mail/admin/incorrectWinMentorProducts.html")
            subject = "{} produse cu probleme in WinMentor".format(len(self.missingCodes) + len(self.missingDefaultGest))
            html_part = template.render({
                "subject": subject,
                "missingCodes": self.missingCodes,
                "missingDefaultGest": self.missingDefaultGest
            })
            send_email(subject, html_part, toEmails=util.getCfgVal("client", "notificationEmails"))


    def sendPartnersMail(self):
        if len(self.missingPartners) != 0 or len(self.multiplePartenerIDsForEmail)!=0:
            template = loader.get_template("mail/admin/WinMentorPartenersProblems.html")
            subject = "Probleme la parteneri in WinMentor"
            html_part = template.render({
                "subject": subject,
                "missingPartners": self.missingPartners,
                "multiplePartenerIDsForEmail": self.multiplePartenerIDsForEmail,
            })
            send_email(subject, html_part, toEmails=util.getCfgVal("client", "notificationEmails"))


    def genNrNir(self):
        """ Genereaza nr NIR pentru o factura noua

        """

        # rc = self._stat.GetNumarFactura("Note de receptie 2011")

        return "672267"
        # return rc


    def matchGestiune(self, name, tipGestiune=None):
        """
        @param name: Nume destinatie din Gesto
        @param listaGestiuni: Lista gestiuni din WinMentor

        """

        self.logger.info(">>> {}()".format(inspect.stack()[0][3]))
        start = dt.now()

        ret = None

        # Get gestiuni
        gestiuni = self.getGestiuni()
        # self.logger.debug("gestiuni: {}".format(gestiuni))

        matchStr = '^\s*([0-9]{1,4})\s*' #+"{}".format(tipGestiune)
        x = re.match(matchStr, name)
        if x:
            no = x.group(1)
            self.logger.debug(repr(no))

            # Find a "gestiune" that matches
            simbolGestiuneSearch = "Magazin {:d}P".format(int(no))
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
            txtMail = "Gestiunile din WinMentor:\n"
            txtMail += repr(self.gestiuni)

            send_email(
                    subject = "WinMentor - nu am gasit gestiunea >{}<".format(name),
                    msg = txtMail
                    )

            1/0

        self.logger.info("ret: {}".format(ret))
        self.logger.info("<<< {}() - duration = {}".format(inspect.stack()[0][3], dt.now() - start))
        return ret


    def addReception(self, gestoData):
        self.logger.info(">>> {}()".format(inspect.stack()[0][3]))
        start = dt.now()

        # TODO comment me
        # TODO rename me

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
        self.logger.info("simbolWinMentor: {}".format(gestoData["simbolWinMentor"]))

        # eliminate strings at begin end end of relatedDocumentNo, fvz123, FCT-312
        matchStr = '^([^0-9]*)([0-9]*)([^0-9]*)$'
        gestoData["relatedDocumentNo"] = re.match(matchStr, gestoData["relatedDocumentNo"]).groups()[1]
        gestoData["relatedDocumentNo"] = gestoData["relatedDocumentNo"][-9:]

        self.logger.info("relatedDocumentNo: {}".format(gestoData["relatedDocumentNo"]))

        self.logger.info("CUI Panemar: {}".format(self.panemarCUI))

        # verify I have all gesto codes and defalut gestiuni in WinMentor
        if not self.productsAreOK(gestoData["items"]):
            self.logger.info("Factura are articole cu coduri nesetate sau gestiuni lipsa, nu adaug")
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

        # # Get gestiune in WinMentor
        # magazine = self.matchGestiune(gestoData["simbolWinMentor"], gestiuni)
        # self.logger.info("magazine: {}".format(magazine))

        # wmGestiune = None
        # fromPanemar = (self.panemarCUI == gestoPartener)
        # for magazin in magazine:
        #     self.logger.info("magazin: {}".format(magazin))
        #     den = magazin["denumire"]
        #     if (fromPanemar and re.search("PRODUSE", den, re.IGNORECASE)) or \
        #             re.search("marfa", den, re.IGNORECASE):
        #         wmGestiune = magazin["simbol"]
        #         break
        # self.logger.info("gestiune in WinMentor: {}".format(wmGestiune))

        # Seteaza luna si anul in WinMentor
        opDate = dt.fromtimestamp(gestoData["operationDate"])
        self.setLunaLucru(opDate.month, opDate.year)

        # Cod partener exact ca in Winmentor
        if not self.partenerExists(gestoPartener):
            if gestoData["source"]["code"] not in self.missingPartners:
                # only add a missing partener once
                self.missingPartners[gestoData["source"]["code"]] = gestoData["source"]

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
        lstArt = self.getFactura(
                partenerId = wmPartenerID,
                serie = "G",
                nr = gestoData["relatedDocumentNo"],
                data = opDate
                )

        self.logger.info(lstArt)

        if lstArt and (len(lstArt) != 0):
            self.logger.info("Gasit intrare in winmentor.")
            if len(lstArt) != len(gestoData["items"]):
                self.logger.error("Product list from gesto is different than product list from winmentor")
                subject = "Factura {} importata incorect in Winmentor".format(gestoData["documentNo"])

                msg = "wmPartenerID:{}, documentNo:{}, relatedDocumentNo:{}".format(wmPartenerID, gestoData["documentNo"], gestoData["relatedDocumentNo"])
                send_email(subject, msg)

                self.logger.error(msg)
                self.logger.info("<<< {}() - duration = {}".format(inspect.stack()[0][3], dt.now() - start))
                return
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
            self.logger.info("<<< {}() - duration = {}".format(inspect.stack()[0][3], dt.now() - start))
            return

        # Get lista articole from gesto, create array of articole pentru factura
        articoleWMDoc = []
        observatii = ""
        for item in gestoData["items"]:
            wmArticol = self.getProduct(item["winMentorCode"])
            # self.logger.info("wmArticol: {}".format(wmArticol))

            # Adauga produs la lista produse factura
            articoleWMDoc.append(
                    {
                        "codExternArticol": item["winMentorCode"],
                        "um": wmArticol["DenUM"],
                        "cant": item["qty"],
                        "listPrice": item["listPrice"],
                        "opPrice": item["opPrice"],
                        # "simbGest": gestoData["simbolWinMentor"]
                        "simbGest": wmArticol["GestImplicita"]
                        }
                    )

            if item["winMentorCode"].startswith("G_MARF"):
                observatii += item["name"]+"; "

        # Creaza factura import
        rc = self.importaFactIntrare(
                logOn = "Master",
                serieDoc="G",
                nrDoc = gestoData["relatedDocumentNo"],
                nrNir = util.getNextDocumentNumber("NIR"),
                simbolCarnet="GNIR",
                data = opDate,
                dataNir = dt.fromtimestamp(gestoData["relatedDocumentDate"]) if gestoData["relatedDocumentDate"] not in ("nil", None) else opDate,
                scadenta = opDate + timedelta(days = 1),
                codFurnizor = wmPartenerID,
                observatii= observatii,
                observatiiNIR=gestoData["destination"]["name"],
                items = articoleWMDoc
                )
        if rc:
            self.logger.info("SUCCESS: Adaugare factura")
        else:
            self.logger.error(repr(self.getListaErori()))
            1/0

        self.logger.info("<<< {}() - duration = {}".format(inspect.stack()[0][3], dt.now() - start))


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

        items = kwargs.get("items", [])

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
                kwargs.get("logOn", "")
                )

        # Transfer
        txtWMDoc += "[Monetar_{}]\n".format(1)
        txtWMDoc += "Operat={}\n".format("N")
        txtWMDoc += "NrDoc={}\n".format(kwargs.get("nrDoc", ""))
        txtWMDoc += "SimbolCarnet={}\n".format("M_G")
        txtWMDoc += "Operatie={}\n".format("A")
        txtWMDoc += "CasaDeMarcat={}\n".format("D")
        txtWMDoc += "NumarBonuri={}\n".format(kwargs.get("clientsNo", ""))
        txtWMDoc += "Data={:%d.%m.%Y}\n".format(kwargs.get("data"))
        txtWMDoc += "Casa={}\n".format("Casa lei")
        txtWMDoc += "TotalArticole={}\n".format(len(items))
        payment = kwargs.get("payment")
        txtWMDoc += "CEC={}\n".format(payment["bank transfer"] if "bank transfer" in payment else 0)
        txtWMDoc += "CARD={}\n".format(payment["card"] if "card" in payment else 0)
        txtWMDoc += "BONVALORIC={}\n".format(payment["food vouchers"] if "food vouchers" in payment else 0)
        txtWMDoc += "Observatii={}\n".format("Gesto")
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

        itemStr = ""
        for idx, item in enumerate(items):
            txtProd = self._dictToColonList(keys, item)
            txtWMDoc += "Item_{}={}\n".format(idx + 1, txtProd) # articolele incep de la 1

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

        # Get gestiune in WinMentor
        # wmGestiune = self.matchGestiune(gestoData["branch"], "PRODUSE")

        # Seteaza luna si anul in WinMentor
        opDate = dt.fromtimestamp(gestoData["dateBegin"])
        self.setLunaLucru(opDate.month, opDate.year)

        # verify I have all gesto codes and defalut gestiuni in WinMentor
        # if not self.productsAreOK(gestoData["items"]):
        #     self.logger.info("Monetarul are articole cu coduri nesetate sau gestiuni lipsa, nu adaug")
        #     self.logger.info("<<< {}() - duration = {}".format(inspect.stack()[0][3], dt.now() - start))
        #     return

       #  Get lista articole from gesto, create array of articole pentru factura

        newItems = {}
        for item in gestoData["items"]:
            if item["winMentorCode"].startswith("G_MARF"):
                codExternArticol = item["winMentorCode"]
            else:
                codExternArticol = "G_PROD_{}_{}".format(item["vat"], gestoData["branch"][:2])

            wmArticol = self.getProduct(codExternArticol)
            # self.logger.info("wmArticol: {}".format(wmArticol))

            # Adauga produs la lista produse transfer

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

        # Creaza transferul
        rc = self.importaMonetare(
                logOn = "Master", # TODO what's this?
                # nrDoc = gestoData["documentNo"],
                nrDoc = util.getNextDocumentNumber("MON"),
                data = opDate,
                items = articoleWMDoc,
                payment = gestoData["payment"],
                clientsNo = gestoData["clientsNo"] if gestoData["clientsNo"] not in ("nil", None) else 0,
                )

        if rc:
            self.logger.info("SUCCESS: Adaugare monetar")
        else:
            self.logger.error(repr(self.getListaErori()))

        self.logger.info("<<< {}() - duration = {}".format(inspect.stack()[0][3], dt.now() - start))


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
                kwargs.get("logOn", "")
                )

        # Transfer
        txtWMDoc += "[Transfer_{}]\n".format(1)
        txtWMDoc += "SimbolCarnet={}\n".format("NT_G")
        txtWMDoc += "NrDoc={}\n".format(kwargs.get("nrDoc", ""))
        txtWMDoc += "Data={:%d.%m.%Y}\n".format(kwargs.get("data"))
        txtWMDoc += "GestDest={}\n".format(kwargs.get("gestiune"))
        txtWMDoc += "Operatie={}\n".format("A")
        txtWMDoc += "Operat={}\n".format("T")
        txtWMDoc += "TotalArticole={}\n".format(len(items))
        txtWMDoc += "Observatii={}\n\n".format("")

        # Adauga items in factura
        txtWMDoc += "\n[Items_{}]\n".format(1)
        keys = (
                "codExternArticol",
                "um",
                "cant",
                "pret",
                "simbGest",
                )

        itemStr = ""
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


    def getTransferuri (self, opDate):
        self.logger.info(">>> {}()".format(inspect.stack()[0][3]))
        start = dt.now()

        self.setLunaLucru(opDate.month, opDate.year)

        alreadyAdded = False
        transferuri, rc = self._stat.GetTransferuri()
        if rc != 0:
            self.logger.error(repr(self.getListaErori()))

        deliveryNotes = {}

        # self.logger.info(transferuri)
        for item in transferuri:
            # self.logger.info(item)
            items = item.split(";")
            # self.logger.info(items)

            date = items[3]
            if date not in deliveryNotes:
                deliveryNotes[date] = {}

            transferNo = items[2]
            if transferNo not in deliveryNotes[date]:
                deliveryNotes[date][transferNo] = {}

            destination = items[1]
            if destination not in deliveryNotes[date][transferNo]:
                deliveryNotes[date][transferNo][destination] = {}

            source = items[0]
            if source not in deliveryNotes[date][transferNo][destination]:
                deliveryNotes[date][transferNo][destination][source] = []

            productCode = items[4]

            deliveryNotes[date][transferNo][destination][source].append({
                                "winMentorCode": items[4],
                                "name": items[5],
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

        ret = deliveryNotes
        self.logger.info("<<< {}() - duration = {}".format(inspect.stack()[0][3], dt.now() - start))
        return ret


    def addWorkOrders(self, gestoData):
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

        # Get gestiune in WinMentor
        wmGestiune = self.matchGestiune(gestoData["branch"], "PRODUSE")

        # Seteaza luna si anul in WinMentor
        opDate = dt.fromtimestamp(gestoData["dateBegin"])
        self.setLunaLucru(opDate.month, opDate.year)

        # verify I have all gesto codes and defalut gestiuni in WinMentor
        if not self.productsAreOK(gestoData["items"]):
            self.logger.info("Factura are articole cu coduri nesetate sau gestiuni lipsa, nu adaug")
            self.logger.info("<<< {}() - duration = {}".format(inspect.stack()[0][3], dt.now() - start))
            return

            # Get lista articole from gesto, create array of articole pentru workOrders
        articoleWMDoc = []
        for item in gestoData["items"]:
            # Adauga produs la lista produse
            if self.isDrink(int(item["code"])):
                simbGest = "PF-Bauturi"
            elif self.isSdwSalad(int(item["code"])):
                simbGest = "PF Sandwich"
            else:
                # I need to have a gestiune for these articles too
                continue

            wmArticol = self.getProduct(item["winMentorCode"])

            articoleWMDoc.append({
                        "codExternArticol": item["winMentorCode"],
                        "um": wmArticol["DenUM"],
                        "cant": item["qty"],
                        # "pret": item["listVal"]/item["qty"],
                        "pret": wmArticol["PretVCuTVA"],
                        "simbGest": simbGest
                    })

        # Creaza transferul
        rc = self.importaTransfer(
                logOn = "Master",
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
