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
    products = None
    gestiuni = None
    panemarCUI = None

    productCodesBauturi = [[1005, 1006], [700, 728], [731, 798],]
    productCodesSdwSalate = [[799, 882], [1100, 1150],]

    missingCodes = []


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
        if self.firma is not None:
            self._stat.SetNumeFirma(self.firma)

        # Seteaza luna lucru
        self.an = kwargs.get("an")
        self.luna = kwargs.get("luna")
        if self.an and self.luna:
            self._stat.SetLunaLucru(self.an, self.luna)

        # TODO check this values ...
        self._stat.SetIDPartField('CodFiscal')
        self._stat.SetIDArtField('CodExtern')

        self._newProducts = []
        self._newPartners = []
        self.missingCodes = []

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
        return (rc == 1)


    def setPanemarCUI(self, CUI):
        _, self.panemarCUI = util.fixupCUI(CUI)


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


    def verifyWinMentorCodes(self, items):
        self.logger.info(">>> {}()".format(inspect.stack()[0][3]))
        start = dt.now()

        ret = False

        for item in items:
            if item["winMentorCode"] == "nil" or not self.productExists(item["winMentorCode"]):
                ret = True

                found = False
                for mc in self.missingCodes:
                    # only add a code once
                    # self.logger.info("{} - {}, {} - {}".format(mc["code"], item["code"], type(mc["code"]), type(item["code"])))

                    if mc["code"] == item["code"]:
                        found = True
                        break

                if not found:
                    # add code if it was not found
                    self.missingCodes.append(item)

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

        ret = { util.fixupCUI(p["idPartener"])[1]: p for p in parteneri}
        self.logger.debug("partners count: {}".format(len(ret)))

        return ret


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
            self.logger.error(repr(msg))
            send_email(
                    subject = "WinMentor - GetNomenclatorArticole eroare >{}<".format(name),
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
        if partenerID not in self.parteneri:
            return False
        else:
            return True


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
                val = "{:.2f}".format(val)
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
        txtFactura = (
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
        txtFactura += "[Factura_{}]\n".format(1)
        txtFactura += "Operatie=A\n"
        txtFactura += "SerieDoc={}\n".format(kwargs.get("serieDoc", ""))
        txtFactura += "NrDoc={}\n".format(kwargs.get("nrDoc", ""))
        if kwargs.get("nrNir"):
            txtFactura += "NrNIR={}\n".format(kwargs.get("nrNir"))
        if kwargs.get("simbolCarnet"):
            txtFactura += "SimbolCarnetNir={}\n".format(kwargs.get("simbolCarnet"))
        txtFactura += "Data={:%d.%m.%Y}\n".format(kwargs.get("data", dt.now()))
        txtFactura += "DataNir={:%d.%m.%Y}\n".format(kwargs.get("dataNir", None))
        txtFactura += "Scadenta={:%d.%m.%Y}\n".format(kwargs.get("scadenta", dt.now()))
        txtFactura += "TotalArticole={}\n".format(len(items))
        txtFactura += "CodFurnizor={}\n".format(kwargs.get("codFurnizor", ""))
        if kwargs.get("TVAINCASARE") is True:
            txtFactura += "TVAINCASARE={}\n".format("D")
        # txtFactura += "Majorari={}\n".format(kwargs.get("majorari", ""))
        if kwargs.get("Discount") is True:
            txtFactura += "Discount={:.4f}\n".format(kwargs.get("discount"))

        # Adauga items in factura
        txtFactura += "\n[Items_{}]\n".format(1)
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
            txtFactura += "Item_{}={}\n".format(idx + 1, txtProd) # articolele incep de la 1

        self.logger.debug("txtFactura: \n{}".format(txtFactura))

        fact = txtFactura.split("\n")

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
            self._newPartners.append(
                    { key: kwargs.get(key, "-") for key in keys if key != "_" }
                    )

            # Get again lista parteneri
            self.parteneri = self.getListaParteneri()
        else:
            self.logger.error(repr(self.getListaErori()))
            self.logger.info("<<< {}() - duration = {}".format(inspect.stack()[0][3], dt.now() - start))
            1/0

        return None


    def existaFacturaIntrare(self, partenerId, serie, nr):
        self.logger.info(">>> {}()".format(inspect.stack()[0][3]))
        start = dt.now()

        self.logger.info("{} - {} - {}".format(partenerId, serie, nr))

        ret = self._stat.ExistaFacturaIntrare(partenerId, serie, nr)
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

        result = None

        # Format parameters to string
        data = data.strftime("%d.%m.%Y")
        serie = str(serie)
        nr = str(nr)
        partenerId = str(partenerId)

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
        intrari, rc = self._stat.GetIntrari()
        result = []
        if (rc == 0) and util.isArray(intrari):
            for intrare in intrari:
                val = self._colonListToDict(keys, intrare)
                isForFactura = (val["partenerId"] == partenerId) and \
                        (val["nrDoc"] == nr) and \
                        (val["data"] == data)
                if isForFactura:
                    result.append(self._colonListToDict(keys, intrare))
        else:
            self.logger.debug("rc = {}".format(rc))
            self.logger.error(repr(self.getListaErori()))

        self.logger.info("<<< {}() - duration = {}".format(inspect.stack()[0][3], dt.now() - start))
        return result


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

    def sendMissingProductCodesMail(self):
        if len(self.missingCodes) != 0:
            template = loader.get_template("mail/admin/productsWithoutCode.html")
            subject = "{} produse cu cod WinMentor incorect in Gesto".format(len(self.missingCodes))
            html_part = template.render({
                "subject": subject,
                "products": self.missingCodes
            })
            send_email(subject, html_part, toEmails=getCfgVal("notificationEmails"))


    def sendNewPartnersMail(self):
        if len(self._newPartners) != 0:
            txtMail = ""
            for partner in self._newPartners:
                for tag, val in partner.iteritems():
                    txtMail += "{}: {}\n".format(tag, val)
                txtMail += "-" * 20 + "\n"
            send_email(
                    subject = "Partener(i) noi in WinMentor",
                    msg = txtMail,
                    toEmails=getCfgVal("notificationEmails")
                    )


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

        matchStr = '^\s*([0-9]{1,4})\s*' #+"{}".format(tipGestiune)
        x = re.match(matchStr, name)
        if x:
            no = x.group(1)
            self.logger.debug(repr(no))

            # Find a "gestiune" that matches
            simbolGestiuneSearch = "Magazin {:d}P".format(int(no))
            self.logger.debug("simbolGestiuneSearch: {}".format(simbolGestiuneSearch))

            for gestiune in self.gestiuni:
                # regex = r"^\s*" + re.escape(no) + "\s*Magazin"
                # found = re.match(regex, gestiune["simbol"], re.IGNORECASE)
                # if found:
                #     result.append(gestiune)
                if simbolGestiuneSearch == gestiune["simbol"]:
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

        self.logger.debug("\n%s",
                        json.dumps(
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

        self.logger.info("CUI Panemar: {}".format(self.panemarCUI))

        # verify I have all gesto codes in WinMentor
        missingCodes = self.verifyWinMentorCodes(gestoData["items"])
        if missingCodes:
            self.logger.info("Factura are articole cu coduri nesetate, nu adaug")
            self.logger.info("<<< {}() - duration = {}".format(inspect.stack()[0][3], dt.now() - start))
            return

        # # Get gestiuni
        # gestiune = self.getGestiune(gestoData["simbolWinMentor"])

        # Get partener from gesto
        _, gestoPartener = util.fixupCUI(gestoData["source"]["code"])
        self.logger.info("gestoPartener = {}".format(gestoPartener))

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

        wmPartenerID = gestoPartener

        # Cod partener exact ca in Winmentor
        if not self.partenerExists(wmPartenerID):
            self.addPartener(
                    codFiscal = wmPartenerID,
                    denumirePartener = gestoData["source"]["name"]
                    )

        if not self.partenerExists(wmPartenerID):
            self.logger.error("Failed to add new partener correcly.")
            self.logger.info("<<< {}() - duration = {}".format(inspect.stack()[0][3], dt.now() - start))
            return

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
                subject = "Factura {} importata incomplet in Winmentor".format(gestoData["documentNo"])

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
                    wmCode = wmCode[len("G_"):] if wmCode.startswith("G_") else wmCode

                    # Search for article from winmentor in gesto array
                    artGesto = None
                    for a in gestoData["items"]:
                        if wmCode == a["code"]:
                            artGesto = a["code"]
                            break

                    if artGesto is None:
                        self.logger.error("Product [%s] from winmentor not found gesto", wmCode)
                        alreadyAdded = False
                        break

        if alreadyAdded:
            self.logger.info("Factura e deja adaugata")
            self.logger.info("<<< {}() - duration = {}".format(inspect.stack()[0][3], dt.now() - start))
            return

        # Get lista articole from gesto, create array of articole pentru factura
        articoleFactura = []
        for item in gestoData["items"]:
            # if not haveArticol:
            #     # Adauga produs in winmentor, cu prefixul G_
            #     self.logger.info("Need to add product to winmentor")
            #     rc = self.addProduct(
            #             idArticol = gestoId,
            #             denumire = articol["name"],
            #             codIntern = "G_{}".format(articol["id"]),
            #             um = articol["um"],
            #             pret = articol["listPrice"],
            #             cotaTVA = articol["vat"]
            #             )
            #     if not rc:
            #         self.logger.error(repr(self.getListaErori()))
            #         self.logger.info("<<< {}() - duration = {}".format(inspect.stack()[0][3], dt.now() - start))
            #         return

            #     if self.getProducts().get(gestoId) is None:
            #         self.logger.error("Failed to add articol to Winmentor")
            #         self.logger.info("<<< {}() - duration = {}".format(inspect.stack()[0][3], dt.now() - start))
            #         return

            wmArticol = self.getProduct(item["winMentorCode"])
            self.logger.info("wmArticol: {}".format(wmArticol))

            # Adauga produs la lista produse factura
            articoleFactura.append(
                    {
                        "codExternArticol": item["winMentorCode"],
                        "um": wmArticol["DenUM"],
                        "cant": item["qty"],
                        "listPrice": item["listPrice"],
                        "opPrice": item["opPrice"],
                        "simbGest": gestoData["simbolWinMentor"]
                        }
                    )

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
                items = articoleFactura
                )
        if rc:
            self.logger.info("SUCCESS: Adaugare factura")
        else:
            self.logger.error(repr(self.getListaErori()))
            1/0

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
        txtTransfer = (
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
        txtTransfer += "[Transfer_{}]\n".format(1)
        txtTransfer += "SimbolCarnet={}\n".format("NT_G")
        txtTransfer += "NrDoc={}\n".format(kwargs.get("nrDoc", ""))
        txtTransfer += "Data={:%d.%m.%Y}\n".format(kwargs.get("data"))
        txtTransfer += "GestDest={}\n".format(kwargs.get("gestiune")["simbol"])
        txtTransfer += "Operatie={}\n".format("A")
        txtTransfer += "Operat={}\n".format("T")
        txtTransfer += "TotalArticole={}\n".format(len(items))
        txtTransfer += "Observatii={}\n\n".format("Gesto")

        # Adauga items in factura
        txtTransfer += "\n[Items_{}]\n".format(1)
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
            txtTransfer += "Item_{}={}\n".format(idx + 1, txtProd) # articolele incep de la 1

        self.logger.debug("txtTransfer: \n{}".format(txtTransfer))

        fact = txtTransfer.split("\n")

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
        productsWithoutCode = []

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

        # # Cauta daca exista deja o factura in Winmentor cu intrarea din gesto
        # alreadyAdded = False
        # lstArt = self._stat.GetTransferuri()

        # self.logger.info(lstArt)
        # 1/0

        # if lstArt and (len(lstArt) != 0):
        #     self.logger.info("Gasit intrare in winmentor.")
        #     if len(lstArt) != len(gestoData["items"]):
        #         self.logger.error("Product list from gesto is different than product list from winmentor")
        #     else:
        #         # Verifica toate produsele din factura daca corespund cu cele din gesto
        #         alreadyAdded = True

        #         for artWm in lstArt:
        #             wmCode = artWm["idArticol"]
        #             # Remove "G_" prefix, if any
        #             wmCode = wmCode[len("G_"):] if wmCode.startswith("G_") else wmCode

        #             # Search for article from winmentor in gesto array
        #             artGesto = None
        #             for a in gestoData["items"]:
        #                 if wmCode == a["code"]:
        #                     artGesto = a["code"]
        #                     break

        #             if artGesto is None:
        #                 self.logger.error("Product [%s] from winmentor not found gesto", wmCode)
        #                 alreadyAdded = False
        #                 break

        # if alreadyAdded:
        #     self.logger.info("Factura e deja adaugata")
        #     self.logger.info("<<< {}() - duration = {}".format(inspect.stack()[0][3], dt.now() - start))
        #     return

        # Get lista articole from gesto, create array of articole pentru factura
        articoleTransfer = []
        for articol in gestoData["items"]:
            # Remove "." from all articol strings
            articol = { key: val.replace(".", "") if isinstance(val, basestring) else val for key, val in articol.iteritems() }
            gestoId = articol["code"]
            # Check if articol is in WinMentor
            haveArticol = self.getProducts().get(gestoId)
            if not haveArticol:
                if not gestoId.startswith("G_"):
                    gestoId = "G_" + gestoId
                    haveArticol = self.getProducts().get(gestoId)
            if not haveArticol:
                # Adauga produs in winmentor, cu prefixul G_
                self.logger.info("Need to add product {} to winmentor".format(articol["name"]))
                rc = self.addProduct(
                        idArticol = gestoId,
                        denumire = articol["name"],
                        codIntern = "G_{}".format(articol["id"]),
                        um = articol["um"],
                        pret = articol["listVal"]/articol["qty"],
                        cotaTVA = articol["vat"]
                        )
                if not rc:
                    self.logger.error(repr(self.getListaErori()))
                    self.logger.info("<<< {}() - duration = {}".format(inspect.stack()[0][3], dt.now() - start))
                    return

                if self.getProducts().get(gestoId) is None:
                    self.logger.error("Failed to add articol to Winmentor")
                    self.logger.info("<<< {}() - duration = {}".format(inspect.stack()[0][3], dt.now() - start))
                    return

            # Adauga produs la lista produse factura
            if self.isDrink(int(articol["code"])):
                simbGest = "PF-Bauturi"
            elif self.isSdwSalad(int(articol["code"])):
                simbGest = "PF Sandwich"
            else:
                # I need to have a gestiune for these articles too
                continue

            articoleTransfer.append({
                        "codExternArticol": gestoId,
                        "um": articol["um"],
                        "cant": articol["qty"],
                        "pret": articol["listVal"]/articol["qty"],
                        "simbGest": simbGest
                    })

        # Creaza transferul
        rc = self.importaTransfer(
                logOn = "Master", # TODO what's this?
                # nrDoc = gestoData["documentNo"],
                nrDoc = util.getNextDocumentNumber("NT"),
                data = opDate,
                gestiune = wmGestiune,
                items = articoleTransfer
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
