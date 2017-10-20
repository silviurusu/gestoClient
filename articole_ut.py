# TODO rename to articole.py, use __main__ for ut 
import pythoncom, win32com.client

if __name__ == '__main__':
    fdm = pythoncom.LoadTypeLib('DocImpServer.tlb')
    if fdm is None:
        exit()

    print(fdm)

    for index in xrange(0, fdm.GetTypeInfoCount()):
        fdoc = fdm.GetDocumentation(index)
        print("{:d} - {:s}".format(index, repr(fdoc)))

        if fdoc[0] == 'DocImpObject':
            type_iid = fdm.GetTypeInfo(index).GetTypeAttr().iid
            print type_iid
            downloads_stat = win32com.client.Dispatch(type_iid)

            # Seteaza firma de lucru 
            ret = downloads_stat.GetListaFirme()
            ret = downloads_stat.SetNumeFirma(ret[1])

            # Now you can start working 
            ret2 = None
            ret, ret2 = downloads_stat.GetNomenclatorArticole()
            print(downloads_stat.GetListaErori())

            if ret is not None:
                print("no products: {:d}".format(len(ret)))
                for i, prod in enumerate(ret):
                    print("product {:d} - {:s}".format(i, repr(prod)))
            if ret2 is not None:
                print("ret2: {:s}".format(repr(ret2))) 






