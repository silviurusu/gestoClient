'''
Facade (wrapper) for WinMentor OLE wrapper

@date 20/09/2017
@author Radu Cucu
'''

import pythoncom, win32com.client
from datetime import datetime as dt
from numbers import Number
import collections
import logging
from util import isArray


class WinMentor(object):
    ''' classdocs
    '''
    
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

        return parteneri 


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
            return None

        produse = []
        for idx, prodStr in enumerate(lista):
            produse.append(self._colonListToDict(keys, prodStr))

        return produse 


    def _dictToColonList(self, keys, args, separator = ";"):
        pd = []
        for key in keys:
            val = args.get(key, "") if isinstance(args, dict) else args[key]
            if isArray(val):
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
        txtFactura += "NrDoc={}\n".format(kwargs.get("nrDoc", ""))
        if kwargs.get("nrNir"):
            txtFactura += "NrNIR={}\n".format(kwargs.get("nrNir"))
        txtFactura += "Data={:%d.%m.%Y}\n".format(kwargs.get("data", dt.now()))
        txtFactura += "DataNir={:%d.%m.%Y}\n".format(kwargs.get("dataNir", dt.now()))
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
                "pret",
                "simbGest",
                "discount",
                "simbServ",
                "pretInreg",
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

        return (rc == 1)

    def adaugaPartener(self, **kwargs):
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
            # Add to new products array:
            self._newPartners.append(
                    { key: kwargs.get(key, "-") for key in keys if key != "_" }
                    )

        return (rc)

    def existaFacturaIntrare(self, partenerId, serie, nr):
        self.logger.debug("> existaFacturaIntrare")
        return (self._stat.ExistaFacturaIntrare(partenerId, serie, nr) == 1)

    def getFactura(self, partenerId, serie, nr, data):
        """ @return array de articole from Winmentor care corespund facturii

        """
        if not self.existaFacturaIntrare(partenerId, serie, nr):
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
        if (rc == 0) and isArray(intrari):
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

        return result


    def getListaGestiuni(self):
        keys = (
                "simbol",
                "denumire"
                )

        gestiuni, rc = self._stat.GetListaGestiuni()
        result = []
        if (rc == 0) and isArray(gestiuni):
            for gestiune in gestiuni:
                result.append(self._colonListToDict(keys, gestiune))
        else:
            self.logger.debug("rc = {}".format(rc))
            self.logger.error(repr(self.getListaErori()))

        return result

    def getNewProducts(self):
        return self._newProducts

    def getNewPartners(self):
        return self._newPartners

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

    # rc = winmentor.adaugaPartener(
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

    # winmentor.adaugaPartener(
    #         idPartener = "TM12323",
    #         denumirePartener = "Adrian Lalaul",
    #         numeBanca = ("BCR", "BRD", "Raiffeisen")
    #         )
    #
