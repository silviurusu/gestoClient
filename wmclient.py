import datetime
import win32api
import pythoncom, win32com.client
import requests
import json
from django.core.mail import EmailMessage
import os
from unidecode import unidecode
from util import *
from settings import *

# from win32com.client import makepy
# makepy.main ()
# exit()


# GESTO_IP="http://www.gesto.ro"
# GESTO_IP="http://31.14.16.81:8000"
GESTO_IP="http://192.168.3.49"
fdm = pythoncom.LoadTypeLib('DocImpServer.tlb')

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settingsWM")

print(fdm)
downloads_stat = None

for index in xrange(0, fdm.GetTypeInfoCount()):
    type_name = fdm.GetDocumentation(index)[0]

    print type_name

    if type_name == 'DocImpObject':
        type_iid = fdm.GetTypeInfo(index).GetTypeAttr().iid
        print type_iid
        downloads_stat = win32com.client.Dispatch(type_iid)

        # ret = downloads_stat.LogOn('Mircea', '2')
        ret = downloads_stat.GetListaFirme()
        if ret != 0:
            print ret
            print  downloads_stat.GetListaErori()

        ret = downloads_stat.SetNumeFirma(u'PAN2016')
        if ret != 1:
            print ret
            print  downloads_stat.GetListaErori()

        ret = downloads_stat.GetListaLuni(u'PAN2016')
        if ret != 1:
            print ret
            print  downloads_stat.GetListaErori()

        ret = downloads_stat.SetLunaLucru(2017, 7)
        print ret
        if ret == 0:
            print  downloads_stat.GetListaErori()

        ret = downloads_stat.SetIDPartField('CodFiscal')

        # # ret = downloads_stat.GetReceptii()
        # # ret = downloads_stat.GetNomenclatorArticole()
        # # ret = downloads_stat.GetClaseArticole()
        # # ret = downloads_stat.GetStocuriPeGestiuni()

        # # ret = downloads_stat.GetIntrari()

        # # ret = downloads_stat.SetIDPartField('CODINTERN')
        # ret = downloads_stat.SetIDPartField('CodFiscal')
        # ret = downloads_stat.SetIDArtField('CODINTERN')
        # ret = downloads_stat.SetIDArtField('CodExtern')
        # ret = downloads_stat.GetListaParteneri()
        # # print ret
        # if ret != 1:
        #     print  downloads_stat.GetListaErori()

        # ret = downloads_stat.GetProducts('01.01.2017 00:00:00')
        # # print ret
        # if ret != 1:
        #     print  downloads_stat.GetListaErori()


        # # with open('fi.txt') as f:
        # #     lines = [line.rstrip('\n') for line in f]
        # # print lines

        # # downloads_stat.SetDocsData(lines)
        # # print ret
        # # if ret != 1:
        # #     print  downloads_stat.GetListaErori()

        # # downloads_stat.FactIntrareValida()
        # # print ret
        # # if ret != 1:
        # #     print  downloads_stat.GetListaErori()

        # # downloads_stat.ImportaFactIntrare()
        # # print ret
        # # print  downloads_stat.GetListaErori()

# # downloads_stat.BuildListOfDownloads(True, True)
# # print downloads_stat.Download(0).Url
# # print downloads_stat


# url = GESTO_IP+"/operations?type=type&dateBegin=dateBegin&dateEnd=dateEnd&idStart=idStart&idEnd=idEnd&idPOS=idPOS&listVal=listVal&page=page&pageSize=pageSize
# startDate = datetime.datetime.now()  - datetime.timedelta(days=1)



# ret = downloads_stat.GenCodArticole()
# if ret == -1:
#     print  downloads_stat.GetListaErori()

# ret = downloads_stat.GetProducts('01.01.2017 00:00:00')
# productsWM = ret[0]
# productsCnt = len(productsWM)

# thefile = open('products.txt', 'w')
# for ctr, product in enumerate(productsWM, start=1):
#     thefile.write("{} {} {}\n".format(ctr, productsCnt, product))

# exit()

# productDetails = [""] * 11
# productDetails[0] = "COD IN2"
# productDetails[1] = "NUME2"
# productDetails[9] = "SILVIU2"

# productStr = ';'.join([unicode(x) for x in productDetails])
# print productStr

# ret = downloads_stat.AddProduct(productStr)
# if ret == 1:
#     subject = "Produs nou in WinMentor: {}, {}".format(productDetails[0],productDetails[1])
#     msg = ""
#     msg += "\nProdusul {}, {} a fost adaugat".format(productDetails[0], productDetails[1])
#     send_email(subject, msg, toEmails=["silviu@vectron.ro", ])
# else:
#     print  downloads_stat.GetListaErori()


# productDetails = [""] * 11
# productDetails[0] = "COD IN2"
# # productDetails[1] = "NUME2"
# for i in range(2, 11):
#     productDetails[i] = "SILVIU{}".format(11-i)
# productDetails[2] = ""


# productStr = ';'.join([unicode(x) for x in productDetails])
# print productStr

# ret = downloads_stat.ModiProduct(productStr)
# if ret != 1:
#     print  downloads_stat.GetListaErori()

# ret = downloads_stat.GetProducts('01.01.2017 00:00:00')
# productsWM = ret[0]
# productsCnt = len(productsWM)

# thefile = open('products.txt', 'w')
# for ctr, product in enumerate(productsWM, start=1):
#     thefile.write("{} {} {}\n".format(ctr, productsCnt, product))

# exit()

startDate = datetime.datetime.strptime("2017-07-19", "%Y-%m-%d")
endDate = startDate + datetime.timedelta(days=1)
# startDate = None
# endDate = None

idStart=None
idEnd=None

type = "reception"

url = GESTO_IP+"/operations?"
url += "&type="+type
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
print (url)

r = requests.get(urlCount, headers={'GESTOTOKEN': settings.GESTOTOKEN})

if r.status_code != 200:
    print(r.text)
else:
    retJSON = r.json()
    # print(json.dumps(retJSON, sort_keys=True, indent=4, separators=(',', ': '), default=util.defaultJSON))

totalRecords = retJSON["range"]["totalRecords"]

pageSize = 10
pagesCount = int((totalRecords + pageSize - 1) / pageSize)
print "pagesCount: {}".format(pagesCount)

for ctr in range(1, pagesCount + 1):
    urlPage = url + "&pageSize="+str(pageSize)
    urlPage += "&page="+str(ctr)
    print ctr, pagesCount, urlPage

    r = requests.get(urlPage, headers={'GESTOTOKEN': settings.GESTOTOKEN})
    retJSON = r.json()

    tot = len(retJSON["data"])
    for ctr2, op in enumerate(retJSON["data"], start=1):

        ret = downloads_stat.ExistaFactura(op["documentNo"])
        if ret == -1:
            print  downloads_stat.GetListaErori()
        if ret != 0:
             # factura exista
             continue

        print ctr2, tot, op["id"]

        recFiscalCode = op["source"]["code"].lower().replace("ro", "")
        if recFiscalCode == "4844886":
            # {u'code': u'4844886', u'type': u'company', u'name': u'00 PANEMAR MORARIT SI PANIFICATIE'}
            continue

        print op["source"]
        op["documentDate"] = datetime.datetime.utcfromtimestamp(op["documentDate"])

        facturaLines = []
        facturaLines.append("[InfoPachet]")
        facturaLines.append("AnLucru={}".format(op["documentDate"].year))
        facturaLines.append("LunaLucru={}".format(op["documentDate"].month))
        facturaLines.append("TipDocument=FACTURA INTRARE")
        facturaLines.append("TotalFacturi=1")
        facturaLines.append("LogOn=Master")
        facturaLines.append("[Factura_1]")
        facturaLines.append("Operatie=A")
        facturaLines.append("SerieDoc=G")
        facturaLines.append("NrDoc={}".format(op["documentNo"]))
        facturaLines.append("NrNIR={}".format(op["relatedDocumentNo"] if op["relatedDocumentNo"] != "nil" else ""))
        facturaLines.append("Data={}".format(op["documentDate"].strftime("%d.%m.%Y")))
        facturaLines.append("SimbolCarnetNir=XL6")
        facturaLines.append("DataNir={}".format(op["documentDate"].strftime("%d.%m.%Y")))
        facturaLines.append("Scadenta=")
        facturaLines.append("TotalArticole={}".format(len(op["items"])))
        facturaLines.append("Observatii=")
        facturaLines.append("ObservatiiNIR=")


        # util.printArray(facturaLines)
        # 1/0

        # ret = downloads_stat.SetIDPartField('CODINTERN')
        # ret = downloads_stat.SetIDPartField('CodExtern')

        # look for a partner with same fiscal code

        ret = downloads_stat.GetListaParteneri()
        # print ret

        partRet = ret[0]
        partFound = None

        partCnt = len(partRet)

        print
        thefile = open('test.txt', 'w')
        for ctr, part in enumerate(partRet, start=1):
            partDetails = part.split(";")
            thefile.write("{} {} {}\n".format(ctr, partCnt, unidecode(partDetails[2])))

        for ctr, part in enumerate(partRet, start=1):
            # print part.encode('utf-8').strip()
            partDetails = part.split(";")
            # print partDetails
            # print "{} {} {}".format(ctr, partCnt, unidecode(partDetails[2]))

            if recFiscalCode in partDetails[2]:
                partFound = part
                break

            # break

        if partFound is None:
            # furnizor nou
            print partDetails
            partDetailsNew = [""] * 22
            partDetailsNew[0] = op["source"]["code"]
            partDetailsNew[1] = op["source"]["name"]
            partDetailsNew[2] = op["source"]["code"]

            partStr = ';'.join([unicode(x) for x in partDetailsNew])
            print partStr

            ret = downloads_stat.AdaugaPartener(partStr)
            if ret == 1:
                subject = "Furnizor nou in WinMentor: {}, {}".format(op["source"]["code"], op["source"]["name"])
                msg = ""
                msg += "\nFurnizorul {}, {} a fost adaugat".format(op["source"]["code"], op["source"]["name"])
                send_email(subject, msg, toEmails=["silviu@vectron.ro", ])
            else:
                print  downloads_stat.GetListaErori()

            # Structura unei linii InfoPart este:
            # ID Partener;
            # Denumire partener;
            # Cod Fiscal;
            # Sediul in localitatea;
            # Adresa sediu;
            # Telefon sediu;
            # Persoane de contact; // separate prin "~"
            # Simbol Clasa;
            # Simbol categorie de pret;
            # ID Agent implicit;
            # Nr. Registrul comertului;
            # Observatii;
            # Simbol banca; // separate prin "~" daca sunt mai multe;
            # Nume banca;// separate prin "~" daca sunt mai multe;
            # Localitate banca; // separate prin "~" daca sunt mai multe;
            # Cont banca; // separate prin "~" daca sunt mai multe;
            # Zi implicita plata;
            # Nume sediu secundar ;// separate prin "~" daca sunt mai multe;
            # Adresa sediului secundar; // separate prin "~" daca sunt mai multe;
            # Telefonul sediului secundar;// separate prin "~" daca sunt mai multe;
            # Localitatea sediului secundar;// separate prin "~" daca sunt mai multe;
            # ID Agent pentru sediului secundar; // separate prin "~" daca sunt mai multe;
        facturaLines.append("CodFurnizor=")

        facturaLines.append("")
        facturaLines.append("[Items_1]")
        ret = downloads_stat.GetProducts('01.01.2017 00:00:00')

        productsWM = ret[0]
        productsCnt = len(productsWM)

        thefile = open('products.txt', 'w')
        for ctr, product in enumerate(productsWM, start=1):
            thefile.write("{} {} {}\n".format(ctr, productsCnt, product))
        productsWM = ret[0]
        productFound = None

        productsCnt = len(productsWM)

        for item in op["items"]:
            print item
            # {
            #     "mgb": "nil",
            #     "mga": "nil",
            #     "mga_code": "nil",
            #     "mgb_code": "nil",
            #     "qty": 15,
            #     "code": "10156",
            #     "dep_code": 1,
            #     "id": 26429260,
            #     "name": "COVRIGI BREZEL 80 GR",
            #     "opPrice": 1.11,
            #     "dep": "Panificatie",
            #     "listPrice": 1.5,
            #     "department": "Panificatie",
            #     "vat": 9
            # }
            productFound = None
            productNameFound = None
            for ctr, product in enumerate(productsWM, start=1):
                # print part.encode('utf-8').strip()

                print product
                productDetails = product.split(";")
                print "{} {} {}".format(ctr, productsCnt, ';'.join([unicode(x) for x in productDetails]))

                if item["code"] == productDetails[1]:
                    productFound = product
                    productID = productDetails[0]
                    break
                elif productNameFound is None and item["name"] == productDetails[1]:
                    productNameFound = product

                # break

            if productFound is not None:
                pass

            elif productNameFound is not None:
                # found same name but not the codintern
                # most probably the same product, update

                productDetails = productNameFound.split(";")

                productDetailsUpdate = [""] * 11
                productDetailsUpdate[0] = productDetails[0]
                productDetailsUpdate[1] = item["code"]

                productStr = ';'.join([unicode(x) for x in productDetailsUpdate])
                print productStr
                ret = downloads_stat.ModiProduct(productStr)
                if ret != 1:
                    print  downloads_stat.GetListaErori()
            else:
                # create product
                #   IDArticol;
                #   Denumire;
                #   Den_UM;
                #   IDProducator;
                #   Denumire Producator;
                #   TipSerie;
                #   DataAdaugarii;
                #   DataUltimeiModificari;
                #   Tip unitate de masura;
                #   Cod Intern WinMentor;
                #   Simbol Clasa

                productDetails = [""] * 11
                productDetails[0] = item["code"]
                productDetails[1] = item["name"]

                productStr = ';'.join([unicode(x) for x in productDetails])
                print productStr

                ret = downloads_stat.AddProduct(productStr)
                if ret == 1:
                    subject = "Produs nou in WinMentor: {}, {}".format(item["code"], item["name"])
                    msg = ""
                    msg += "\nProdusul {}, {} a fost adaugat".format(item["code"], item["name"])
                    send_email(subject, msg, toEmails=["silviu@vectron.ro", ])
                else:
                    print  downloads_stat.GetListaErori()

            # IDArticol;DenUM;Cant;Pret;Simbol gestiune receptie;ProcentDiscount;SimbolCont(in caz ul cand articolul este un serviciu);Pret de inregistrare (in cazul cand se folosesc articole valorice)
            facturaLines.append("Item_1={};;{};{};;;;".format(productID, item["qty"], item["opPrice"]))

        util.printArray(facturaLines)
        downloads_stat.SetDocsData(facturaLines)
        if ret != 1:
            print  downloads_stat.GetListaErori()

        downloads_stat.FactIntrareValida()
        if ret != 1:
            print  downloads_stat.GetListaErori()

        # downloads_stat.ImportaFactIntrare()
        # if ret != 1:
        #     print  downloads_stat.GetListaErori()

        break

    break
