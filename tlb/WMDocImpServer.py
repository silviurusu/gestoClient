# -*- coding: mbcs -*-
# Created by makepy.py version 0.5.01
# By python version 2.7.16 (v2.7.16:413a49145e, Mar  4 2019, 01:37:19) [MSC v.1500 64 bit (AMD64)]
# From type library 'WMDocImpServer.tlb'
# On Thu May 23 20:34:58 2019
'WMDocImpServer Library'
makepy_version = '0.5.01'
python_version = 0x20710f0

import win32com.client.CLSIDToClass, pythoncom, pywintypes
import win32com.client.util
from pywintypes import IID
from win32com.client import Dispatch

# The following 3 lines may need tweaking for the particular server
# Candidates are pythoncom.Missing, .Empty and .ArgNotFound
defaultNamedOptArg=pythoncom.Empty
defaultNamedNotOptArg=pythoncom.Empty
defaultUnnamedArg=pythoncom.Empty

CLSID = IID('{19FEBEEA-A1EE-4548-A5D0-C1A141F0F577}')
MajorVersion = 1
MinorVersion = 0
LibraryFlags = 8
LCID = 0x0

from win32com.client import DispatchBaseClass
class IWMDocImpObject(DispatchBaseClass):
	'Dispatch interface for WMDocImpObject Object'
	CLSID = IID('{FDF13A22-BD23-46D5-995D-94C3F7F83F64}')
	coclass_clsid = IID('{A4286FD3-EB00-40FC-AE02-AC9611532A43}')

	def AccesWMSGranted(self, Error=pythoncom.Missing):
		return self._ApplyTypes_(129, 1, (3, 0), ((16387, 2),), u'AccesWMSGranted', None,Error
			)

	def AdaugaArticol(self, InfoArticol=defaultNamedNotOptArg):
		return self._oleobj_.InvokeTypes(92, LCID, 1, (3, 0), ((8, 1),),InfoArticol
			)

	def AdaugaGestiune(self, InfoGest=defaultNamedNotOptArg):
		return self._oleobj_.InvokeTypes(135, LCID, 1, (3, 0), ((8, 1),),InfoGest
			)

	def AdaugaLinieContract(self, CodContract=defaultNamedNotOptArg, InfoLinie=defaultNamedNotOptArg):
		return self._oleobj_.InvokeTypes(232, LCID, 1, (3, 0), ((3, 1), (8, 1)),CodContract
			, InfoLinie)

	def AdaugaPartener(self, InfoPart=defaultNamedNotOptArg):
		return self._oleobj_.InvokeTypes(40, LCID, 1, (3, 0), ((8, 1),),InfoPart
			)

	def AddDataReferinta(self, DataRef=defaultNamedNotOptArg):
		return self._oleobj_.InvokeTypes(96, LCID, 1, (3, 0), ((8, 1),),DataRef
			)

	def BonAchizitieValid(self):
		return self._oleobj_.InvokeTypes(214, LCID, 1, (3, 0), (),)

	def BonuriConsumValide(self):
		return self._oleobj_.InvokeTypes(85, LCID, 1, (3, 0), (),)

	def ComenziFurnValide(self):
		return self._oleobj_.InvokeTypes(210, LCID, 1, (3, 0), (),)

	def ComenziGestValide(self):
		return self._oleobj_.InvokeTypes(105, LCID, 1, (3, 0), (),)

	def ComenziSubunitValide(self):
		return self._oleobj_.InvokeTypes(227, LCID, 1, (3, 0), (),)

	def ComenziValide(self):
		return self._oleobj_.InvokeTypes(30, LCID, 1, (3, 0), (),)

	def CompensariValide(self):
		return self._oleobj_.InvokeTypes(180, LCID, 1, (3, 0), (),)

	def ConectatlaServer(self):
		return self._oleobj_.InvokeTypes(233, LCID, 1, (3, 0), (),)

	def ContracteValide(self):
		return self._oleobj_.InvokeTypes(239, LCID, 1, (3, 0), (),)

	def DateValide(self):
		return self._oleobj_.InvokeTypes(32, LCID, 1, (3, 0), (),)

	def ExistaFactura(self, PartID=defaultNamedNotOptArg, NrFact=defaultNamedNotOptArg, SerieFact=defaultNamedNotOptArg):
		return self._oleobj_.InvokeTypes(37, LCID, 1, (3, 0), ((8, 1), (3, 1), (8, 1)),PartID
			, NrFact, SerieFact)

	def ExistaFacturaExt(self, PartID=defaultNamedNotOptArg, NrFact=defaultNamedNotOptArg, SerieFact=defaultNamedNotOptArg):
		return self._oleobj_.InvokeTypes(110, LCID, 1, (3, 0), ((8, 1), (8, 1), (8, 1)),PartID
			, NrFact, SerieFact)

	def ExistaFacturaIntrare(self, PartID=defaultNamedNotOptArg, NrFact=defaultNamedNotOptArg, SerieFact=defaultNamedNotOptArg):
		return self._oleobj_.InvokeTypes(235, LCID, 1, (3, 0), ((8, 1), (3, 1), (8, 1)),PartID
			, NrFact, SerieFact)

	def FactIntrareValida(self):
		return self._oleobj_.InvokeTypes(62, LCID, 1, (3, 0), (),)

	def GeListaLocatiiMobile(self, SimbolGest=defaultNamedNotOptArg, DenLocatieFixa=defaultNamedNotOptArg, Error=pythoncom.Missing):
		return self._ApplyTypes_(170, 1, (12, 0), ((8, 1), (8, 1), (16387, 2)), u'GeListaLocatiiMobile', None,SimbolGest
			, DenLocatieFixa, Error)

	def GenCodArticole(self):
		return self._oleobj_.InvokeTypes(56, LCID, 1, (3, 0), (),)

	def GenCodParteneri(self):
		return self._oleobj_.InvokeTypes(55, LCID, 1, (3, 0), (),)

	def GetAllIntrFurnNeoperate(self, Error=pythoncom.Missing):
		return self._ApplyTypes_(224, 1, (12, 0), ((16387, 2),), u'GetAllIntrFurnNeoperate', None,Error
			)

	def GetArtPeSedii(self, Error=pythoncom.Missing):
		return self._ApplyTypes_(220, 1, (12, 0), ((16387, 2),), u'GetArtPeSedii', None,Error
			)

	def GetArticoleDiscount(self, CodCriteriu=defaultNamedNotOptArg, DataAnaliza=defaultNamedNotOptArg, Error=pythoncom.Missing):
		return self._ApplyTypes_(120, 1, (12, 0), ((3, 1), (8, 1), (16387, 2)), u'GetArticoleDiscount', None,CodCriteriu
			, DataAnaliza, Error)

	def GetArticoleImpliciteLocatie(self, CodLocatie=defaultNamedNotOptArg, Error=pythoncom.Missing):
		return self._ApplyTypes_(176, 1, (12, 0), ((3, 1), (16387, 2)), u'GetArticoleImpliciteLocatie', None,CodLocatie
			, Error)

	def GetArticoleOptionale(self, Error=pythoncom.Missing):
		return self._ApplyTypes_(164, 1, (12, 0), ((16387, 2),), u'GetArticoleOptionale', None,Error
			)

	def GetAvizeNefacturate(self, Error=pythoncom.Missing):
		return self._ApplyTypes_(247, 1, (12, 0), ((16387, 2),), u'GetAvizeNefacturate', None,Error
			)

	def GetCarneteDedicate(self, Tipcarnet=defaultNamedNotOptArg, Error=pythoncom.Missing):
		return self._ApplyTypes_(191, 1, (12, 0), ((3, 1), (16387, 2)), u'GetCarneteDedicate', None,Tipcarnet
			, Error)

	def GetClaseArticole(self, Error=pythoncom.Missing):
		return self._ApplyTypes_(22, 1, (12, 0), ((16387, 2),), u'GetClaseArticole', None,Error
			)

	def GetClaseParteneri(self, Error=pythoncom.Missing):
		return self._ApplyTypes_(23, 1, (12, 0), ((16387, 2),), u'GetClaseParteneri', None,Error
			)

	def GetClaseStatistice(self, Error=pythoncom.Missing):
		return self._ApplyTypes_(179, 1, (12, 0), ((16387, 2),), u'GetClaseStatistice', None,Error
			)

	def GetCmdFurnNefacturate(self, Error=pythoncom.Missing):
		return self._ApplyTypes_(222, 1, (12, 0), ((16387, 2),), u'GetCmdFurnNefacturate', None,Error
			)

	def GetComenziInterne(self, DeLaData=defaultNamedNotOptArg, Error=pythoncom.Missing):
		return self._ApplyTypes_(87, 1, (12, 0), ((8, 1), (16387, 2)), u'GetComenziInterne', None,DeLaData
			, Error)

	def GetComenziNefacturate(self, Error=pythoncom.Missing):
		return self._ApplyTypes_(147, 1, (12, 0), ((16387, 2),), u'GetComenziNefacturate', None,Error
			)

	def GetComenziNeinchise(self, DL=defaultNamedNotOptArg, Error=pythoncom.Missing):
		return self._ApplyTypes_(202, 1, (12, 0), ((3, 1), (16387, 2)), u'GetComenziNeinchise', None,DL
			, Error)

	def GetComenziProdLansate(self, Error=pythoncom.Missing):
		return self._ApplyTypes_(161, 1, (12, 0), ((16387, 2),), u'GetComenziProdLansate', None,Error
			)

	def GetComenziSubunitNefact(self, Error=pythoncom.Missing):
		return self._ApplyTypes_(226, 1, (12, 0), ((16387, 2),), u'GetComenziSubunitNefact', None,Error
			)

	def GetContracteAbonament(self, DataReferinta=defaultNamedNotOptArg, Error=pythoncom.Missing):
		return self._ApplyTypes_(230, 1, (12, 0), ((8, 1), (16387, 2)), u'GetContracteAbonament', None,DataReferinta
			, Error)

	def GetCritDiscPart(self, Error=pythoncom.Missing):
		return self._ApplyTypes_(42, 1, (12, 0), ((16387, 2),), u'GetCritDiscPart', None,Error
			)

	def GetCritDiscPeArticole(self, Error=pythoncom.Missing):
		return self._ApplyTypes_(39, 1, (12, 0), ((16387, 2),), u'GetCritDiscPeArticole', None,Error
			)

	def GetCritDiscPeClase(self, Error=pythoncom.Missing):
		return self._ApplyTypes_(41, 1, (12, 0), ((16387, 2),), u'GetCritDiscPeClase', None,Error
			)

	def GetCriteriiDiscount(self, Error=pythoncom.Missing):
		return self._ApplyTypes_(234, 1, (12, 0), ((16387, 2),), u'GetCriteriiDiscount', None,Error
			)

	def GetDiminuari(self, DeLaData=defaultNamedNotOptArg, Error=pythoncom.Missing):
		return self._ApplyTypes_(94, 1, (12, 0), ((8, 1), (16387, 2)), u'GetDiminuari', None,DeLaData
			, Error)

	def GetDispLivrareNeoperate(self, SimbolGest=defaultNamedNotOptArg, Error=pythoncom.Missing):
		return self._ApplyTypes_(185, 1, (12, 0), ((8, 1), (16387, 2)), u'GetDispLivrareNeoperate', None,SimbolGest
			, Error)

	def GetDocFromFile(self, FileName=defaultNamedNotOptArg):
		return self._oleobj_.InvokeTypes(11, LCID, 1, (3, 0), ((8, 1),),FileName
			)

	def GetIesSubunitNeoperate(self, Error=pythoncom.Missing):
		return self._ApplyTypes_(204, 1, (12, 0), ((16387, 2),), u'GetIesSubunitNeoperate', None,Error
			)

	def GetIesiri(self, DataStart=defaultNamedNotOptArg, DataEnd=defaultNamedNotOptArg, Error=pythoncom.Missing):
		return self._ApplyTypes_(109, 1, (12, 0), ((8, 1), (8, 1), (16387, 2)), u'GetIesiri', None,DataStart
			, DataEnd, Error)

	def GetIncasariFactura(self, PartID=defaultNamedNotOptArg, NrFact=defaultNamedNotOptArg, SerieFact=defaultNamedNotOptArg):
		return self._ApplyTypes_(236, 1, (12, 0), ((8, 1), (3, 1), (8, 1)), u'GetIncasariFactura', None,PartID
			, NrFact, SerieFact)

	def GetIncasariLuna(self, Error=pythoncom.Missing):
		return self._ApplyTypes_(100, 1, (12, 0), ((16387, 2),), u'GetIncasariLuna', None,Error
			)

	def GetInfoArtClienti(self, Error=pythoncom.Missing):
		return self._ApplyTypes_(67, 1, (12, 0), ((16387, 2),), u'GetInfoArtClienti', None,Error
			)

	def GetInfoArticol(self, ArtID=defaultNamedNotOptArg, Error=pythoncom.Missing):
		return self._ApplyTypes_(88, 1, (12, 0), ((8, 1), (16387, 2)), u'GetInfoArticol', None,ArtID
			, Error)

	def GetInfoBonConsum(self, Numar=defaultNamedNotOptArg, Serie=defaultNamedNotOptArg, Error=pythoncom.Missing):
		return self._ApplyTypes_(221, 1, (12, 0), ((3, 1), (8, 1), (16387, 2)), u'GetInfoBonConsum', None,Numar
			, Serie, Error)

	def GetInfoCmdAgent(self, MarcaAgent=defaultNamedNotOptArg, TipComanda=defaultNamedNotOptArg, Error=pythoncom.Missing):
		return self._ApplyTypes_(89, 1, (12, 0), ((3, 1), (3, 1), (16387, 2)), u'GetInfoCmdAgent', None,MarcaAgent
			, TipComanda, Error)

	def GetInfoComenzi(self, Error=pythoncom.Missing):
		return self._ApplyTypes_(76, 1, (12, 0), ((16387, 2),), u'GetInfoComenzi', None,Error
			)

	def GetInfoComenziFurn(self, Error=pythoncom.Missing):
		return self._ApplyTypes_(184, 1, (12, 0), ((16387, 2),), u'GetInfoComenziFurn', None,Error
			)

	def GetInfoComenziGest(self, Error=pythoncom.Missing):
		return self._ApplyTypes_(107, 1, (12, 0), ((16387, 2),), u'GetInfoComenziGest', None,Error
			)

	def GetInfoLocatieMobila(self, CodExternLocatie=defaultNamedNotOptArg, SimbolGest=defaultNamedNotOptArg, Error=pythoncom.Missing):
		return self._ApplyTypes_(177, 1, (8, 0), ((8, 1), (8, 1), (16387, 2)), u'GetInfoLocatieMobila', None,CodExternLocatie
			, SimbolGest, Error)

	def GetInfoLocatieMobila2(self, CodLocatie=defaultNamedNotOptArg, SimbolGest=defaultNamedNotOptArg, Error=pythoncom.Missing):
		return self._ApplyTypes_(192, 1, (8, 0), ((3, 1), (8, 1), (16387, 2)), u'GetInfoLocatieMobila2', None,CodLocatie
			, SimbolGest, Error)

	def GetInfoPart(self, PartID=defaultNamedNotOptArg, Error=pythoncom.Missing):
		return self._ApplyTypes_(237, 1, (12, 0), ((8, 1), (16387, 2)), u'GetInfoPart', None,PartID
			, Error)

	def GetInfoSuplimCMD1(self, CodComanda1=defaultNamedNotOptArg, Error=pythoncom.Missing):
		return self._ApplyTypes_(113, 1, (12, 0), ((3, 1), (16387, 2)), u'GetInfoSuplimCMD1', None,CodComanda1
			, Error)

	def GetInfoUtilaje(self, ClasePart=defaultNamedNotOptArg, Error=pythoncom.Missing):
		return self._ApplyTypes_(108, 1, (12, 0), ((8, 1), (16387, 2)), u'GetInfoUtilaje', None,ClasePart
			, Error)

	def GetIntrSubunitNeoperate(self, Error=pythoncom.Missing):
		return self._ApplyTypes_(225, 1, (12, 0), ((16387, 2),), u'GetIntrSubunitNeoperate', None,Error
			)

	def GetIntrari(self, Error=pythoncom.Missing):
		return self._ApplyTypes_(50, 1, (12, 0), ((16387, 2),), u'GetIntrari', None,Error
			)

	def GetIntrariNeoperate(self, SimbolGest=defaultNamedNotOptArg, Error=pythoncom.Missing):
		return self._ApplyTypes_(131, 1, (12, 0), ((8, 1), (16387, 2)), u'GetIntrariNeoperate', None,SimbolGest
			, Error)

	def GetInventareNeoperate(self, SimbolGest=defaultNamedNotOptArg, Error=pythoncom.Missing):
		return self._ApplyTypes_(140, 1, (12, 0), ((8, 1), (16387, 2)), u'GetInventareNeoperate', None,SimbolGest
			, Error)

	def GetLastPretAchiz(self, IDArticol=defaultNamedNotOptArg, Error=pythoncom.Missing):
		return self._ApplyTypes_(168, 1, (8, 0), ((8, 1), (16387, 2)), u'GetLastPretAchiz', None,IDArticol
			, Error)

	def GetLastPreturiAchiz(self, Error=pythoncom.Missing):
		return self._ApplyTypes_(173, 1, (12, 0), ((16387, 2),), u'GetLastPreturiAchiz', None,Error
			)

	def GetLiniiAvizNefacturat(self, CodAviz=defaultNamedNotOptArg, Error=pythoncom.Missing):
		return self._ApplyTypes_(248, 1, (12, 0), ((3, 1), (16387, 2)), u'GetLiniiAvizNefacturat', None,CodAviz
			, Error)

	def GetLiniiComandaNefacturata(self, CodComanda=defaultNamedNotOptArg, Error=pythoncom.Missing):
		return self._ApplyTypes_(148, 1, (12, 0), ((3, 1), (16387, 2)), u'GetLiniiComandaNefacturata', None,CodComanda
			, Error)

	def GetLiniiComandaNeinchisa(self, CodComanda=defaultNamedNotOptArg, Error=pythoncom.Missing):
		return self._ApplyTypes_(203, 1, (12, 0), ((3, 1), (16387, 2)), u'GetLiniiComandaNeinchisa', None,CodComanda
			, Error)

	def GetLiniiComandaProd(self, CodComanda=defaultNamedNotOptArg, Error=pythoncom.Missing):
		return self._ApplyTypes_(162, 1, (12, 0), ((3, 1), (16387, 2)), u'GetLiniiComandaProd', None,CodComanda
			, Error)

	def GetLiniiContract(self, CodContract=defaultNamedNotOptArg, Error=pythoncom.Missing):
		return self._ApplyTypes_(231, 1, (12, 0), ((3, 1), (16387, 2)), u'GetLiniiContract', None,CodContract
			, Error)

	def GetLiniiDispLivrare(self, CodDispLivrare=defaultNamedNotOptArg, SimbolGest=defaultNamedNotOptArg, Error=pythoncom.Missing):
		return self._ApplyTypes_(186, 1, (12, 0), ((3, 1), (8, 1), (16387, 2)), u'GetLiniiDispLivrare', None,CodDispLivrare
			, SimbolGest, Error)

	def GetLiniiIntrariNeoperate(self, CodIntr=defaultNamedNotOptArg, Error=pythoncom.Missing):
		return self._ApplyTypes_(133, 1, (12, 0), ((3, 1), (16387, 2)), u'GetLiniiIntrariNeoperate', None,CodIntr
			, Error)

	def GetLiniiInventarNeoperat(self, CodInventar=defaultNamedNotOptArg, Error=pythoncom.Missing):
		return self._ApplyTypes_(142, 1, (12, 0), ((3, 1), (16387, 2)), u'GetLiniiInventarNeoperat', None,CodInventar
			, Error)

	def GetLiniiLivrariNeoperate(self, CodIes=defaultNamedNotOptArg, Error=pythoncom.Missing):
		return self._ApplyTypes_(138, 1, (12, 0), ((3, 1), (16387, 2)), u'GetLiniiLivrariNeoperate', None,CodIes
			, Error)

	def GetLiniiPromotiiPret(self, DataStart=defaultNamedNotOptArg, Error=pythoncom.Missing):
		return self._ApplyTypes_(152, 1, (12, 0), ((8, 1), (16387, 2)), u'GetLiniiPromotiiPret', None,DataStart
			, Error)

	def GetLiniiReceptiiNeop(self, CodIntr=defaultNamedNotOptArg, SimbolGest=defaultNamedNotOptArg, Error=pythoncom.Missing):
		return self._ApplyTypes_(199, 1, (12, 0), ((3, 1), (8, 1), (16387, 2)), u'GetLiniiReceptiiNeop', None,CodIntr
			, SimbolGest, Error)

	def GetLiniiTransfNeoperate(self, CodTransfer=defaultNamedNotOptArg, Error=pythoncom.Missing):
		return self._ApplyTypes_(127, 1, (12, 0), ((3, 1), (16387, 2)), u'GetLiniiTransfNeoperate', None,CodTransfer
			, Error)

	def GetListaArtCatPret(self, Error=pythoncom.Missing):
		return self._ApplyTypes_(25, 1, (12, 0), ((16387, 2),), u'GetListaArtCatPret', None,Error
			)

	def GetListaArtCatPret2(self, ArtID=defaultNamedNotOptArg, Error=pythoncom.Missing):
		return self._ApplyTypes_(77, 1, (12, 0), ((8, 1), (16387, 2)), u'GetListaArtCatPret2', None,ArtID
			, Error)

	def GetListaCarnete(self, Error=pythoncom.Missing):
		return self._ApplyTypes_(1, 1, (12, 0), ((16387, 2),), u'GetListaCarnete', None,Error
			)

	def GetListaCarneteExt(self, Error=pythoncom.Missing):
		return self._ApplyTypes_(78, 1, (12, 0), ((16387, 2),), u'GetListaCarneteExt', None,Error
			)

	def GetListaCatPret(self, Error=pythoncom.Missing):
		return self._ApplyTypes_(24, 1, (12, 0), ((16387, 2),), u'GetListaCatPret', None,Error
			)

	def GetListaDelegati(self, Error=pythoncom.Missing):
		return self._ApplyTypes_(54, 1, (12, 0), ((16387, 2),), u'GetListaDelegati', None,Error
			)

	def GetListaErori(self):
		return self._ApplyTypes_(4, 1, (12, 0), (), u'GetListaErori', None,)

	def GetListaFirme(self):
		return self._ApplyTypes_(7, 1, (12, 0), (), u'GetListaFirme', None,)

	def GetListaGestiuni(self, Error=pythoncom.Missing):
		return self._ApplyTypes_(6, 1, (12, 0), ((16387, 2),), u'GetListaGestiuni', None,Error
			)

	def GetListaLocalitati(self, Error=pythoncom.Missing):
		return self._ApplyTypes_(46, 1, (12, 0), ((16387, 2),), u'GetListaLocalitati', None,Error
			)

	def GetListaLuni(self, NumeSkema=defaultNamedNotOptArg):
		return self._ApplyTypes_(8, 1, (12, 0), ((8, 1),), u'GetListaLuni', None,NumeSkema
			)

	def GetListaPartFiltrata(self, Filtru=defaultNamedNotOptArg, Error=pythoncom.Missing):
		return self._ApplyTypes_(195, 1, (12, 0), ((8, 1), (16387, 2)), u'GetListaPartFiltrata', None,Filtru
			, Error)

	def GetListaParteneri(self, Error=pythoncom.Missing):
		return self._ApplyTypes_(12, 1, (12, 0), ((16387, 2),), u'GetListaParteneri', None,Error
			)

	def GetListaPersonal(self, Error=pythoncom.Missing):
		return self._ApplyTypes_(13, 1, (12, 0), ((16387, 2),), u'GetListaPersonal', None,Error
			)

	def GetListaSubunit(self, Error=pythoncom.Missing):
		return self._ApplyTypes_(45, 1, (12, 0), ((16387, 2),), u'GetListaSubunit', None,Error
			)

	def GetListaUtilizatori(self):
		return self._ApplyTypes_(144, 1, (12, 0), (), u'GetListaUtilizatori', None,)

	def GetListabanci(self, Error=pythoncom.Missing):
		return self._ApplyTypes_(21, 1, (12, 0), ((16387, 2),), u'GetListabanci', None,Error
			)

	def GetLivrariNeoperate(self, SimbolGest=defaultNamedNotOptArg, Error=pythoncom.Missing):
		return self._ApplyTypes_(136, 1, (12, 0), ((8, 1), (16387, 2)), u'GetLivrariNeoperate', None,SimbolGest
			, Error)

	def GetLocatieImplicitaArt(self, ArtID=defaultNamedNotOptArg, Error=pythoncom.Missing):
		return self._ApplyTypes_(174, 1, (8, 0), ((8, 1), (16387, 2)), u'GetLocatieImplicitaArt', None,ArtID
			, Error)

	def GetManoperaReteta(self, IDProdus=defaultNamedNotOptArg, Error=pythoncom.Missing):
		return self._ApplyTypes_(209, 1, (12, 0), ((8, 1), (16387, 2)), u'GetManoperaReteta', None,IDProdus
			, Error)

	def GetMaririStoc(self, DeLaData=defaultNamedNotOptArg, Error=pythoncom.Missing):
		return self._ApplyTypes_(95, 1, (12, 0), ((8, 1), (16387, 2)), u'GetMaririStoc', None,DeLaData
			, Error)

	def GetMaterialeReteta(self, IDProdus=defaultNamedNotOptArg, Error=pythoncom.Missing):
		return self._ApplyTypes_(208, 1, (12, 0), ((8, 1), (16387, 2)), u'GetMaterialeReteta', None,IDProdus
			, Error)

	def GetMonede(self, Error=pythoncom.Missing):
		return self._ApplyTypes_(61, 1, (12, 0), ((16387, 2),), u'GetMonede', None,Error
			)

	def GetNartObjVarStru(self, IDArticol=defaultNamedNotOptArg, Error=pythoncom.Missing):
		return self._ApplyTypes_(115, 1, (12, 0), ((8, 1), (16387, 2)), u'GetNartObjVarStru', None,IDArticol
			, Error)

	def GetNesositePromise(self, Error=pythoncom.Missing):
		return self._ApplyTypes_(156, 1, (12, 0), ((16387, 2),), u'GetNesositePromise', None,Error
			)

	def GetNextNumarDoc(self, SimbolCarnet=defaultNamedNotOptArg, TipDoc=defaultNamedNotOptArg, Error=pythoncom.Missing):
		return self._ApplyTypes_(64, 1, (8, 0), ((8, 1), (3, 1), (16387, 2)), u'GetNextNumarDoc', None,SimbolCarnet
			, TipDoc, Error)

	def GetNextPartID(self, Error=pythoncom.Missing):
		return self._ApplyTypes_(53, 1, (8, 0), ((16387, 2),), u'GetNextPartID', None,Error
			)

	def GetNomAtribute(self, Error=pythoncom.Missing):
		return self._ApplyTypes_(154, 1, (12, 0), ((16387, 2),), u'GetNomAtribute', None,Error
			)

	def GetNomCertificate(self, Error=pythoncom.Missing):
		return self._ApplyTypes_(66, 1, (12, 0), ((16387, 2),), u'GetNomCertificate', None,Error
			)

	def GetNomValAtribute(self, Error=pythoncom.Missing):
		return self._ApplyTypes_(155, 1, (12, 0), ((16387, 2),), u'GetNomValAtribute', None,Error
			)

	def GetNomenclatorArticole(self, Error=pythoncom.Missing):
		return self._ApplyTypes_(28, 1, (12, 0), ((16387, 2),), u'GetNomenclatorArticole', None,Error
			)

	def GetNomenclatorLocalitati(self, Error=pythoncom.Missing):
		return self._ApplyTypes_(60, 1, (12, 0), ((16387, 2),), u'GetNomenclatorLocalitati', None,Error
			)

	def GetNomenclatorLocatii(self, Error=pythoncom.Missing):
		return self._ApplyTypes_(90, 1, (12, 0), ((16387, 2),), u'GetNomenclatorLocatii', None,Error
			)

	def GetNotePredare(self, DeLaData=defaultNamedNotOptArg, Error=pythoncom.Missing):
		return self._ApplyTypes_(93, 1, (12, 0), ((8, 1), (16387, 2)), u'GetNotePredare', None,DeLaData
			, Error)

	def GetNumarFactura(self, SimbolCarnet=defaultNamedNotOptArg, Error=pythoncom.Missing):
		return self._ApplyTypes_(38, 1, (3, 0), ((8, 1), (16387, 2)), u'GetNumarFactura', None,SimbolCarnet
			, Error)

	def GetOferte(self, Error=pythoncom.Missing):
		return self._ApplyTypes_(44, 1, (12, 0), ((16387, 2),), u'GetOferte', None,Error
			)

	def GetPartPromotiiPret(self, Data=defaultNamedNotOptArg, Error=pythoncom.Missing):
		return self._ApplyTypes_(153, 1, (12, 0), ((8, 1), (16387, 2)), u'GetPartPromotiiPret', None,Data
			, Error)

	def GetProcenteDiscount(self, CodCriteriu=defaultNamedNotOptArg, DataAnaliza=defaultNamedNotOptArg, Error=pythoncom.Missing):
		return self._ApplyTypes_(119, 1, (12, 0), ((3, 1), (8, 1), (16387, 2)), u'GetProcenteDiscount', None,CodCriteriu
			, DataAnaliza, Error)

	def GetPromoCadouCuPrag(self, CodPromo=defaultNamedNotOptArg, Error=pythoncom.Missing):
		return self._ApplyTypes_(98, 1, (12, 0), ((3, 1), (16387, 2)), u'GetPromoCadouCuPrag', None,CodPromo
			, Error)

	def GetPromoCadouManuale(self, Data=defaultNamedNotOptArg, Error=pythoncom.Missing):
		return self._ApplyTypes_(79, 1, (12, 0), ((8, 1), (16387, 2)), u'GetPromoCadouManuale', None,Data
			, Error)

	def GetPromoPaketCuCadouPePrag(self, Data=defaultNamedNotOptArg, Error=pythoncom.Missing):
		return self._ApplyTypes_(97, 1, (12, 0), ((8, 1), (16387, 2)), u'GetPromoPaketCuCadouPePrag', None,Data
			, Error)

	def GetPromotiiCadou(self, Data=defaultNamedNotOptArg, Error=pythoncom.Missing):
		return self._ApplyTypes_(70, 1, (12, 0), ((8, 1), (16387, 2)), u'GetPromotiiCadou', None,Data
			, Error)

	def GetPromotiiPret(self, Data=defaultNamedNotOptArg, Error=pythoncom.Missing):
		return self._ApplyTypes_(151, 1, (12, 0), ((8, 1), (16387, 2)), u'GetPromotiiPret', None,Data
			, Error)

	def GetPromptPayment(self, Data=defaultNamedNotOptArg, Error=pythoncom.Missing):
		return self._ApplyTypes_(69, 1, (8, 0), ((8, 1), (16387, 2)), u'GetPromptPayment', None,Data
			, Error)

	def GetReceptiiNeoperate(self, SimbolGest=defaultNamedNotOptArg, Error=pythoncom.Missing):
		return self._ApplyTypes_(198, 1, (12, 0), ((8, 1), (16387, 2)), u'GetReceptiiNeoperate', None,SimbolGest
			, Error)

	def GetSeriiCadou(self, CodCadou=defaultNamedNotOptArg, Error=pythoncom.Missing):
		return self._ApplyTypes_(75, 1, (12, 0), ((3, 1), (16387, 2)), u'GetSeriiCadou', None,CodCadou
			, Error)

	def GetSeriiPromo1(self, CodPromo1=defaultNamedNotOptArg, Error=pythoncom.Missing):
		return self._ApplyTypes_(74, 1, (12, 0), ((3, 1), (16387, 2)), u'GetSeriiPromo1', None,CodPromo1
			, Error)

	def GetSintezaStoc(self, Error=pythoncom.Missing):
		return self._ApplyTypes_(91, 1, (12, 0), ((16387, 2),), u'GetSintezaStoc', None,Error
			)

	def GetSoldDetaliat(self, PartID=defaultNamedNotOptArg, Error=pythoncom.Missing):
		return self._ApplyTypes_(16, 1, (12, 0), ((8, 1), (16387, 2)), u'GetSoldDetaliat', None,PartID
			, Error)

	def GetSoldPart(self, PartID=defaultNamedNotOptArg, Error=pythoncom.Missing):
		return self._ApplyTypes_(26, 1, (12, 0), ((8, 1), (16387, 2)), u'GetSoldPart', None,PartID
			, Error)

	def GetSolduri(self, Error=pythoncom.Missing):
		return self._ApplyTypes_(29, 1, (12, 0), ((16387, 2),), u'GetSolduri', None,Error
			)

	def GetSolduriExt(self, Error=pythoncom.Missing):
		return self._ApplyTypes_(47, 1, (12, 0), ((16387, 2),), u'GetSolduriExt', None,Error
			)

	def GetSolduriFurn(self, Error=pythoncom.Missing):
		return self._ApplyTypes_(229, 1, (12, 0), ((16387, 2),), u'GetSolduriFurn', None,Error
			)

	def GetStocArtDetaliat(self, ArtID=defaultNamedNotOptArg, GestID=defaultNamedNotOptArg, Error=pythoncom.Missing):
		return self._ApplyTypes_(43, 1, (12, 0), ((8, 1), (8, 1), (16387, 2)), u'GetStocArtDetaliat', None,ArtID
			, GestID, Error)

	def GetStocArtExt2(self, GestID=defaultNamedNotOptArg, Error=pythoncom.Missing):
		return self._ApplyTypes_(65, 1, (12, 0), ((8, 1), (16387, 2)), u'GetStocArtExt2', None,GestID
			, Error)

	def GetStocArtFiltrat(self, Filtru=defaultNamedNotOptArg, GestID=defaultNamedNotOptArg, Error=pythoncom.Missing):
		return self._ApplyTypes_(194, 1, (12, 0), ((8, 1), (8, 1), (16387, 2)), u'GetStocArtFiltrat', None,Filtru
			, GestID, Error)

	def GetStocArtWMS(self, GestID=defaultNamedNotOptArg, ArtID=defaultNamedNotOptArg, Serie=defaultNamedNotOptArg, Error=pythoncom.Missing):
		return self._ApplyTypes_(171, 1, (12, 0), ((8, 1), (8, 1), (8, 1), (16387, 2)), u'GetStocArtWMS', None,GestID
			, ArtID, Serie, Error)

	def GetStocArticol(self, ArticolID=defaultNamedNotOptArg, GestID=defaultNamedNotOptArg, Error=pythoncom.Missing):
		return self._ApplyTypes_(48, 1, (12, 0), ((8, 1), (8, 1), (16387, 2)), u'GetStocArticol', None,ArticolID
			, GestID, Error)

	def GetStocArticole(self, Error=pythoncom.Missing):
		return self._ApplyTypes_(15, 1, (12, 0), ((16387, 2),), u'GetStocArticole', None,Error
			)

	def GetStocArticoleExt(self, Error=pythoncom.Missing):
		return self._ApplyTypes_(27, 1, (12, 0), ((16387, 2),), u'GetStocArticoleExt', None,Error
			)

	def GetStocLocatie(self, CodLocatie=defaultNamedNotOptArg, Error=pythoncom.Missing):
		return self._ApplyTypes_(172, 1, (12, 0), ((3, 1), (16387, 2)), u'GetStocLocatie', None,CodLocatie
			, Error)

	def GetStocuriPeGestiuni(self, Error=pythoncom.Missing):
		return self._ApplyTypes_(59, 1, (12, 0), ((16387, 2),), u'GetStocuriPeGestiuni', None,Error
			)

	def GetSubunitatiUser(self, Error=pythoncom.Missing):
		return self._ApplyTypes_(19, 1, (12, 0), ((16387, 2),), u'GetSubunitatiUser', None,Error
			)

	def GetTargetAgenti(self, MarcaAgent=defaultNamedNotOptArg, Data=defaultNamedNotOptArg, Error=pythoncom.Missing):
		return self._ApplyTypes_(158, 1, (12, 0), ((3, 1), (8, 1), (16387, 2)), u'GetTargetAgenti', None,MarcaAgent
			, Data, Error)

	def GetTargetPart(self, IDPartener=defaultNamedNotOptArg, Data=defaultNamedNotOptArg, Error=pythoncom.Missing):
		return self._ApplyTypes_(217, 1, (12, 0), ((8, 1), (8, 1), (16387, 2)), u'GetTargetPart', None,IDPartener
			, Data, Error)

	def GetTaskuri(self, Error=pythoncom.Missing):
		return self._ApplyTypes_(167, 1, (12, 0), ((16387, 2),), u'GetTaskuri', None,Error
			)

	def GetTransfNeoperate(self, SimbolGest=defaultNamedNotOptArg, Error=pythoncom.Missing):
		return self._ApplyTypes_(125, 1, (12, 0), ((8, 1), (16387, 2)), u'GetTransfNeoperate', None,SimbolGest
			, Error)

	def GetTransferuri(self, DataStart=defaultNamedNotOptArg, DataEnd=defaultNamedNotOptArg, Error=pythoncom.Missing):
		return self._ApplyTypes_(104, 1, (12, 0), ((8, 1), (8, 1), (16387, 2)), u'GetTransferuri', None,DataStart
			, DataEnd, Error)

	def GetTranzactiiInCurs(self, Error=pythoncom.Missing):
		return self._ApplyTypes_(49, 1, (12, 0), ((16387, 2),), u'GetTranzactiiInCurs', None,Error
			)

	def GetTraseeAgent(self, DataStart=defaultNamedNotOptArg, DataEnd=defaultNamedNotOptArg, Marca=defaultNamedNotOptArg, Error=pythoncom.Missing):
		return self._ApplyTypes_(68, 1, (12, 0), ((8, 1), (8, 1), (3, 1), (16387, 2)), u'GetTraseeAgent', None,DataStart
			, DataEnd, Marca, Error)

	def GetUltimulTransferInGestiunea(self, GestID=defaultNamedNotOptArg, Error=pythoncom.Missing):
		return self._ApplyTypes_(82, 1, (12, 0), ((8, 1), (16387, 2)), u'GetUltimulTransferInGestiunea', None,GestID
			, Error)

	def GetVanzariExt(self, Error=pythoncom.Missing):
		return self._ApplyTypes_(52, 1, (12, 0), ((16387, 2),), u'GetVanzariExt', None,Error
			)

	def GetVanzariLuna(self, Error=pythoncom.Missing):
		return self._ApplyTypes_(51, 1, (12, 0), ((16387, 2),), u'GetVanzariLuna', None,Error
			)

	def GetVersiuni(self, VerMentor=pythoncom.Missing, VerServer=pythoncom.Missing):
		return self._ApplyTypes_(17, 1, (3, 0), ((16389, 2), (16389, 2)), u'GetVersiuni', None,VerMentor
			, VerServer)

	def GetnextCodEAN(self, TipEAN=defaultNamedNotOptArg, ColoanaArt=defaultNamedNotOptArg, Error=pythoncom.Missing):
		return self._ApplyTypes_(182, 1, (8, 0), ((8, 1), (8, 1), (16387, 2)), u'GetnextCodEAN', None,TipEAN
			, ColoanaArt, Error)

	def IesiriSubunitValid(self):
		return self._oleobj_.InvokeTypes(80, LCID, 1, (3, 0), (),)

	def ImportaBonuriAchizitie(self):
		return self._oleobj_.InvokeTypes(215, LCID, 1, (3, 0), (),)

	def ImportaBonuriConsum(self):
		return self._oleobj_.InvokeTypes(86, LCID, 1, (3, 0), (),)

	def ImportaComenzi(self):
		return self._oleobj_.InvokeTypes(31, LCID, 1, (3, 0), (),)

	def ImportaComenziFurn(self):
		return self._oleobj_.InvokeTypes(211, LCID, 1, (3, 0), (),)

	def ImportaComenziGest(self):
		return self._oleobj_.InvokeTypes(106, LCID, 1, (3, 0), (),)

	def ImportaComenziSubunit(self):
		return self._oleobj_.InvokeTypes(228, LCID, 1, (3, 0), (),)

	def ImportaCompensari(self):
		return self._oleobj_.InvokeTypes(181, LCID, 1, (3, 0), (),)

	def ImportaContracte(self):
		return self._oleobj_.InvokeTypes(240, LCID, 1, (3, 0), (),)

	def ImportaFactIntrare(self):
		return self._oleobj_.InvokeTypes(63, LCID, 1, (3, 0), (),)

	def ImportaFacturi(self):
		return self._oleobj_.InvokeTypes(33, LCID, 1, (3, 0), (),)

	def ImportaIesiriSubunit(self):
		return self._oleobj_.InvokeTypes(81, LCID, 1, (3, 0), (),)

	def ImportaIncasariExt(self):
		return self._oleobj_.InvokeTypes(36, LCID, 1, (3, 0), (),)

	def ImportaInvoice(self):
		return self._oleobj_.InvokeTypes(73, LCID, 1, (3, 0), (),)

	def ImportaMonetare(self):
		return self._oleobj_.InvokeTypes(84, LCID, 1, (3, 0), (),)

	def ImportaNoteContabile(self):
		return self._oleobj_.InvokeTypes(213, LCID, 1, (3, 0), (),)

	def ImportaNotePredare(self):
		return self._oleobj_.InvokeTypes(103, LCID, 1, (3, 0), (),)

	def ImportaOferte(self):
		return self._oleobj_.InvokeTypes(166, LCID, 1, (3, 0), (),)

	def ImportaPlati(self):
		return self._oleobj_.InvokeTypes(197, LCID, 1, (3, 0), (),)

	def ImportaReglareInventar(self, TipReglare=defaultNamedNotOptArg):
		return self._oleobj_.InvokeTypes(123, LCID, 1, (3, 0), ((3, 1),),TipReglare
			)

	def ImportaRetete(self):
		return self._oleobj_.InvokeTypes(207, LCID, 1, (3, 0), (),)

	def ImportaTransferuri(self):
		return self._oleobj_.InvokeTypes(58, LCID, 1, (3, 0), (),)

	def IncasariValideExt(self):
		return self._oleobj_.InvokeTypes(35, LCID, 1, (3, 0), (),)

	def InchideComanda(self, CodComanda=defaultNamedNotOptArg):
		return self._oleobj_.InvokeTypes(238, LCID, 1, (3, 0), ((3, 1),),CodComanda
			)

	def InvoiceValid(self):
		return self._oleobj_.InvokeTypes(72, LCID, 1, (3, 0), (),)

	def IsAdministratorWMS(self, Error=pythoncom.Missing):
		return self._ApplyTypes_(130, 1, (3, 0), ((16387, 2),), u'IsAdministratorWMS', None,Error
			)

	def LocatiaAreStoc(self, CodLocatie=defaultNamedNotOptArg, Error=pythoncom.Missing):
		return self._ApplyTypes_(190, 1, (3, 0), ((3, 1), (16387, 2)), u'LocatiaAreStoc', None,CodLocatie
			, Error)

	def LogOff(self):
		return self._oleobj_.InvokeTypes(218, LCID, 1, (24, 0), (),)

	def LogOn(self, UserName=defaultNamedNotOptArg, PassWord=defaultNamedNotOptArg):
		return self._oleobj_.InvokeTypes(3, LCID, 1, (3, 0), ((8, 1), (8, 1)),UserName
			, PassWord)

	def ModificaHeaderContract(self, CodContract=defaultNamedNotOptArg, InfoHeader=defaultNamedNotOptArg):
		return self._oleobj_.InvokeTypes(245, LCID, 1, (3, 0), ((3, 1), (8, 1)),CodContract
			, InfoHeader)

	def ModificaLinieContract(self, CodLinieContract=defaultNamedNotOptArg, InfoLinie=defaultNamedNotOptArg):
		return self._oleobj_.InvokeTypes(246, LCID, 1, (3, 0), ((3, 1), (8, 1)),CodLinieContract
			, InfoLinie)

	def ModificaPartener(self, InfoPart=defaultNamedNotOptArg):
		return self._oleobj_.InvokeTypes(216, LCID, 1, (3, 0), ((8, 1),),InfoPart
			)

	def MonetareValide(self):
		return self._oleobj_.InvokeTypes(83, LCID, 1, (3, 0), (),)

	def NCValide(self):
		return self._oleobj_.InvokeTypes(212, LCID, 1, (3, 0), (),)

	def NotePredareValide(self):
		return self._oleobj_.InvokeTypes(102, LCID, 1, (3, 0), (),)

	def OferteValide(self):
		return self._oleobj_.InvokeTypes(165, LCID, 1, (3, 0), (),)

	def PlatiValide(self):
		return self._oleobj_.InvokeTypes(196, LCID, 1, (3, 0), (),)

	def ReglareInventarValida(self, TipReglare=defaultNamedNotOptArg):
		return self._oleobj_.InvokeTypes(122, LCID, 1, (3, 0), ((3, 1),),TipReglare
			)

	def ReteteValide(self):
		return self._oleobj_.InvokeTypes(206, LCID, 1, (3, 0), (),)

	def SchimbaRezervare(self, CodLinieComanda=defaultNamedNotOptArg, GestiuneVeche=defaultNamedNotOptArg, SerieVeche=defaultNamedNotOptArg, CodLocatieVeche=defaultNamedNotOptArg
			, GestiuneNoua=defaultNamedNotOptArg, SerieNoua=defaultNamedNotOptArg, CodLocatieNoua=defaultNamedNotOptArg, Cant=defaultNamedNotOptArg):
		return self._oleobj_.InvokeTypes(201, LCID, 1, (3, 0), ((3, 1), (8, 1), (8, 1), (3, 1), (8, 1), (8, 1), (3, 1), (5, 1)),CodLinieComanda
			, GestiuneVeche, SerieVeche, CodLocatieVeche, GestiuneNoua, SerieNoua
			, CodLocatieNoua, Cant)

	def SendMesajWME(self, Mesaj=defaultNamedNotOptArg):
		return self._oleobj_.InvokeTypes(145, LCID, 1, (3, 0), ((8, 1),),Mesaj
			)

	def SerializareDispLivrare(self, CodComanda=defaultNamedNotOptArg, Serializare=defaultNamedNotOptArg):
		return self._oleobj_.InvokeTypes(241, LCID, 1, (3, 0), ((3, 1), (12, 1)),CodComanda
			, Serializare)

	def SerializareIntrari(self, CodIntr=defaultNamedNotOptArg, Serializare=defaultNamedNotOptArg):
		return self._oleobj_.InvokeTypes(242, LCID, 1, (3, 0), ((3, 1), (12, 1)),CodIntr
			, Serializare)

	def SetAllSubunitFlag(self, Flag=defaultNamedNotOptArg):
		return self._oleobj_.InvokeTypes(223, LCID, 1, (24, 0), ((3, 1),),Flag
			)

	def SetCMDFacturabile(self, Comenzi=defaultNamedNotOptArg):
		return self._oleobj_.InvokeTypes(112, LCID, 1, (3, 0), ((12, 1),),Comenzi
			)

	def SetCantitatiLiniiComanda(self, ListaLinii=defaultNamedNotOptArg):
		return self._oleobj_.InvokeTypes(149, LCID, 1, (3, 0), ((12, 1),),ListaLinii
			)

	def SetCarnetTransfer(self, SimbolCarnet=defaultNamedNotOptArg):
		return self._oleobj_.InvokeTypes(188, LCID, 1, (3, 0), ((8, 1),),SimbolCarnet
			)

	def SetCatPretImplicita(self, IDCatPret=defaultNamedNotOptArg):
		return self._oleobj_.InvokeTypes(243, LCID, 1, (3, 0), ((8, 1),),IDCatPret
			)

	def SetCmdImplicitAcceptat(self, ImplicitAcceptat=defaultNamedNotOptArg):
		return self._oleobj_.InvokeTypes(18, LCID, 1, (24, 0), ((3, 1),),ImplicitAcceptat
			)

	def SetComenziFaraLansare(self, FaraLansare=defaultNamedNotOptArg):
		return self._oleobj_.InvokeTypes(124, LCID, 1, (24, 0), ((3, 1),),FaraLansare
			)

	def SetContImplicitArt(self, SimbolCont=defaultNamedNotOptArg):
		return self._oleobj_.InvokeTypes(101, LCID, 1, (3, 0), ((8, 1),),SimbolCont
			)

	def SetDenSubunit(self, DenSubunit=defaultNamedNotOptArg):
		return self._oleobj_.InvokeTypes(34, LCID, 1, (3, 0), ((8, 1),),DenSubunit
			)

	def SetDescriereLocatie(self, CodLocatie=defaultNamedNotOptArg, Descriere=defaultNamedNotOptArg):
		return self._oleobj_.InvokeTypes(189, LCID, 1, (3, 0), ((3, 1), (8, 1)),CodLocatie
			, Descriere)

	def SetDocsData(self, DataDoc=defaultNamedNotOptArg):
		return self._oleobj_.InvokeTypes(14, LCID, 1, (24, 0), ((12, 1),),DataDoc
			)

	def SetFapticInventarOperat(self, ListaFaptic=defaultNamedNotOptArg, CodInventar=defaultNamedNotOptArg):
		return self._oleobj_.InvokeTypes(143, LCID, 1, (3, 0), ((12, 1), (3, 1)),ListaFaptic
			, CodInventar)

	def SetFilterNartExt(self, Filter=defaultNamedNotOptArg):
		return self._oleobj_.InvokeTypes(150, LCID, 1, (24, 0), ((8, 1),),Filter
			)

	def SetFlagCMDOnline(self, CMDOnline=defaultNamedNotOptArg):
		return self._oleobj_.InvokeTypes(99, LCID, 1, (24, 0), ((3, 1),),CMDOnline
			)

	def SetIDArtAnalizat(self, ArtID=defaultNamedNotOptArg):
		return self._oleobj_.InvokeTypes(116, LCID, 1, (24, 0), ((8, 1),),ArtID
			)

	def SetIDArtField(self, FieldName=defaultNamedNotOptArg):
		return self._oleobj_.InvokeTypes(10, LCID, 1, (24, 0), ((8, 1),),FieldName
			)

	def SetIDPartAnalizat(self, PartID=defaultNamedNotOptArg):
		return self._oleobj_.InvokeTypes(117, LCID, 1, (24, 0), ((8, 1),),PartID
			)

	def SetIDPartField(self, FieldName=defaultNamedNotOptArg):
		return self._oleobj_.InvokeTypes(9, LCID, 1, (24, 0), ((8, 1),),FieldName
			)

	def SetInclusivStoc0(self, Flag=defaultNamedNotOptArg):
		return self._oleobj_.InvokeTypes(219, LCID, 1, (24, 0), ((3, 1),),Flag
			)

	def SetLiniiDispLivrareOperate(self, ListaLinii=defaultNamedNotOptArg):
		return self._oleobj_.InvokeTypes(187, LCID, 1, (3, 0), ((12, 1),),ListaLinii
			)

	def SetLivrariOperate(self, ListaLivrari=defaultNamedNotOptArg):
		return self._oleobj_.InvokeTypes(139, LCID, 1, (3, 0), ((12, 1),),ListaLivrari
			)

	def SetLocatieImplicita(self, ArtID=defaultNamedNotOptArg, CodLocatie=defaultNamedNotOptArg):
		return self._oleobj_.InvokeTypes(178, LCID, 1, (3, 0), ((8, 1), (3, 1)),ArtID
			, CodLocatie)

	def SetLunaLucru(self, An=defaultNamedNotOptArg, Luna=defaultNamedNotOptArg):
		return self._oleobj_.InvokeTypes(2, LCID, 1, (3, 0), ((3, 1), (3, 1)),An
			, Luna)

	def SetNumeFirma(self, NumeFirma=defaultNamedNotOptArg):
		return self._oleobj_.InvokeTypes(5, LCID, 1, (3, 0), ((8, 1),),NumeFirma
			)

	def SetObservatiiComanda(self, Observatii=defaultNamedNotOptArg):
		return self._oleobj_.InvokeTypes(159, LCID, 1, (3, 0), ((12, 1),),Observatii
			)

	def SetObservatiiLiniiComanda(self, Observatii=defaultNamedNotOptArg):
		return self._oleobj_.InvokeTypes(163, LCID, 1, (3, 0), ((12, 1),),Observatii
			)

	def SetReceptiiIntrariOperate(self, ListaReceptii=defaultNamedNotOptArg):
		return self._oleobj_.InvokeTypes(134, LCID, 1, (3, 0), ((12, 1),),ListaReceptii
			)

	def SetReceptiiPartialeIntr(self, ListaReceptii=defaultNamedNotOptArg):
		return self._oleobj_.InvokeTypes(200, LCID, 1, (3, 0), ((12, 1),),ListaReceptii
			)

	def SetReceptiiTransfOperate(self, ListaReceptii=defaultNamedNotOptArg):
		return self._oleobj_.InvokeTypes(128, LCID, 1, (3, 0), ((12, 1),),ListaReceptii
			)

	def SetRezervareAutomata(self, Flag=defaultNamedNotOptArg):
		return self._oleobj_.InvokeTypes(111, LCID, 1, (24, 0), ((3, 1),),Flag
			)

	def SetSimbolClasaFiltrare(self, SimbolClasa=defaultNamedNotOptArg):
		return self._oleobj_.InvokeTypes(244, LCID, 1, (3, 0), ((8, 1),),SimbolClasa
			)

	def SetStadiuWMSComanda(self, CodComanda=defaultNamedNotOptArg, Stadiu=defaultNamedNotOptArg):
		return self._oleobj_.InvokeTypes(146, LCID, 1, (3, 0), ((3, 1), (3, 1)),CodComanda
			, Stadiu)

	def SetStadiuWMSIntrari(self, CodIntr=defaultNamedNotOptArg, Stadiu=defaultNamedNotOptArg):
		return self._oleobj_.InvokeTypes(132, LCID, 1, (3, 0), ((3, 1), (3, 1)),CodIntr
			, Stadiu)

	def SetStadiuWMSInventar(self, CodInventar=defaultNamedNotOptArg, Stadiu=defaultNamedNotOptArg):
		return self._oleobj_.InvokeTypes(141, LCID, 1, (3, 0), ((3, 1), (3, 1)),CodInventar
			, Stadiu)

	def SetStadiuWMSLivrari(self, CodIes=defaultNamedNotOptArg, Stadiu=defaultNamedNotOptArg):
		return self._oleobj_.InvokeTypes(137, LCID, 1, (3, 0), ((3, 1), (3, 1)),CodIes
			, Stadiu)

	def SetStadiuWMSTransf(self, CodTransf=defaultNamedNotOptArg, Stadiu=defaultNamedNotOptArg):
		return self._oleobj_.InvokeTypes(126, LCID, 1, (3, 0), ((3, 1), (3, 1)),CodTransf
			, Stadiu)

	def SetStocEgalCantDeScos(self, Flag=defaultNamedNotOptArg):
		return self._oleobj_.InvokeTypes(157, LCID, 1, (24, 0), ((3, 1),),Flag
			)

	def SetStocFaraFurn(self, Flag=defaultNamedNotOptArg):
		return self._oleobj_.InvokeTypes(205, LCID, 1, (24, 0), ((3, 1),),Flag
			)

	def SetSubunitate(self, Subunitate=defaultNamedNotOptArg):
		return self._oleobj_.InvokeTypes(20, LCID, 1, (3, 0), ((3, 1),),Subunitate
			)

	def SetTipFiltruTransferuri(self, Tip=defaultNamedNotOptArg):
		return self._oleobj_.InvokeTypes(121, LCID, 1, (24, 0), ((3, 1),),Tip
			)

	def SetValExtensiiComanda(self, Valori=defaultNamedNotOptArg):
		return self._oleobj_.InvokeTypes(175, LCID, 1, (3, 0), ((12, 1),),Valori
			)

	def SetValExtensiiLiniiComanda(self, Valori=defaultNamedNotOptArg):
		return self._oleobj_.InvokeTypes(160, LCID, 1, (3, 0), ((12, 1),),Valori
			)

	def TransferuriValide(self):
		return self._oleobj_.InvokeTypes(57, LCID, 1, (3, 0), (),)

	def UpdateArtIDField(self, IDCol=defaultNamedNotOptArg, Valoare=defaultNamedNotOptArg, CodObiect=defaultNamedNotOptArg):
		return self._oleobj_.InvokeTypes(183, LCID, 1, (3, 0), ((8, 1), (8, 1), (3, 1)),IDCol
			, Valoare, CodObiect)

	def UpdateArticol(self, InfoArticol=defaultNamedNotOptArg):
		return self._oleobj_.InvokeTypes(118, LCID, 1, (3, 0), ((8, 1),),InfoArticol
			)

	def UpdateInfoSediu(self, IDPart=defaultNamedNotOptArg, Sediu=defaultNamedNotOptArg, InfoSediu=defaultNamedNotOptArg):
		return self._oleobj_.InvokeTypes(193, LCID, 1, (3, 0), ((8, 1), (8, 1), (8, 1)),IDPart
			, Sediu, InfoSediu)

	def UpdatePart(self, InfoPart=defaultNamedNotOptArg):
		return self._oleobj_.InvokeTypes(114, LCID, 1, (3, 0), ((12, 1),),InfoPart
			)

	def UpdateStareUtilaje(self, InfoUtilaje=defaultNamedNotOptArg):
		return self._oleobj_.InvokeTypes(71, LCID, 1, (3, 0), ((12, 1),),InfoUtilaje
			)

	def UpdateTask(self, Infotask=defaultNamedNotOptArg):
		return self._oleobj_.InvokeTypes(169, LCID, 1, (3, 0), ((8, 1),),Infotask
			)

	_prop_map_get_ = {
	}
	_prop_map_put_ = {
	}
	def __iter__(self):
		"Return a Python iterator for this object"
		try:
			ob = self._oleobj_.InvokeTypes(-4,LCID,3,(13, 10),())
		except pythoncom.error:
			raise TypeError("This object does not support enumeration")
		return win32com.client.util.Iterator(ob, None)

from win32com.client import CoClassBaseClass
# This CoClass is known by the name 'WMDocImpServer.WMDocImpObject'
class WMDocImpObject(CoClassBaseClass): # A CoClass
	# WMDocImpObject Object
	CLSID = IID('{A4286FD3-EB00-40FC-AE02-AC9611532A43}')
	coclass_sources = [
	]
	coclass_interfaces = [
		IWMDocImpObject,
	]
	default_interface = IWMDocImpObject

IWMDocImpObject_vtables_dispatch_ = 1
IWMDocImpObject_vtables_ = [
	(( u'LogOn' , u'UserName' , u'PassWord' , u'Param3' , ), 3, (3, (), [ 
			(8, 1, None, None) , (8, 1, None, None) , (16387, 10, None, None) , ], 1 , 1 , 4 , 0 , 56 , (3, 0, None, None) , 0 , )),
	(( u'GetListaErori' , u'Value' , ), 4, (4, (), [ (16396, 10, None, None) , ], 1 , 1 , 4 , 0 , 64 , (3, 0, None, None) , 0 , )),
	(( u'SetNumeFirma' , u'NumeFirma' , u'Value' , ), 5, (5, (), [ (8, 1, None, None) , 
			(16387, 10, None, None) , ], 1 , 1 , 4 , 0 , 72 , (3, 0, None, None) , 0 , )),
	(( u'GetListaCarnete' , u'Error' , u'Value' , ), 1, (1, (), [ (16387, 2, None, None) , 
			(16396, 10, None, None) , ], 1 , 1 , 4 , 0 , 80 , (3, 0, None, None) , 0 , )),
	(( u'SetLunaLucru' , u'An' , u'Luna' , u'Value' , ), 2, (2, (), [ 
			(3, 1, None, None) , (3, 1, None, None) , (16387, 10, None, None) , ], 1 , 1 , 4 , 0 , 88 , (3, 0, None, None) , 0 , )),
	(( u'GetListaGestiuni' , u'Error' , u'Value' , ), 6, (6, (), [ (16387, 2, None, None) , 
			(16396, 10, None, None) , ], 1 , 1 , 4 , 0 , 96 , (3, 0, None, None) , 0 , )),
	(( u'GetListaFirme' , u'Value' , ), 7, (7, (), [ (16396, 10, None, None) , ], 1 , 1 , 4 , 0 , 104 , (3, 0, None, None) , 0 , )),
	(( u'GetListaLuni' , u'NumeSkema' , u'Value' , ), 8, (8, (), [ (8, 1, None, None) , 
			(16396, 10, None, None) , ], 1 , 1 , 4 , 0 , 112 , (3, 0, None, None) , 0 , )),
	(( u'SetIDPartField' , u'FieldName' , ), 9, (9, (), [ (8, 1, None, None) , ], 1 , 1 , 4 , 0 , 120 , (3, 0, None, None) , 0 , )),
	(( u'SetIDArtField' , u'FieldName' , ), 10, (10, (), [ (8, 1, None, None) , ], 1 , 1 , 4 , 0 , 128 , (3, 0, None, None) , 0 , )),
	(( u'GetDocFromFile' , u'FileName' , u'Value' , ), 11, (11, (), [ (8, 1, None, None) , 
			(16387, 10, None, None) , ], 1 , 1 , 4 , 0 , 136 , (3, 0, None, None) , 0 , )),
	(( u'GetListaPersonal' , u'Error' , u'Value' , ), 13, (13, (), [ (16387, 2, None, None) , 
			(16396, 10, None, None) , ], 1 , 1 , 4 , 0 , 144 , (3, 0, None, None) , 0 , )),
	(( u'GetListaParteneri' , u'Error' , u'Value' , ), 12, (12, (), [ (16387, 2, None, None) , 
			(16396, 10, None, None) , ], 1 , 1 , 4 , 0 , 152 , (3, 0, None, None) , 0 , )),
	(( u'SetDocsData' , u'DataDoc' , ), 14, (14, (), [ (12, 1, None, None) , ], 1 , 1 , 4 , 0 , 160 , (3, 0, None, None) , 0 , )),
	(( u'GetStocArticole' , u'Error' , u'Value' , ), 15, (15, (), [ (16387, 2, None, None) , 
			(16396, 10, None, None) , ], 1 , 1 , 4 , 0 , 168 , (3, 0, None, None) , 0 , )),
	(( u'GetSoldDetaliat' , u'PartID' , u'Error' , u'Value' , ), 16, (16, (), [ 
			(8, 1, None, None) , (16387, 2, None, None) , (16396, 10, None, None) , ], 1 , 1 , 4 , 0 , 176 , (3, 0, None, None) , 0 , )),
	(( u'GetVersiuni' , u'VerMentor' , u'VerServer' , u'Value' , ), 17, (17, (), [ 
			(16389, 2, None, None) , (16389, 2, None, None) , (16387, 10, None, None) , ], 1 , 1 , 4 , 0 , 184 , (3, 0, None, None) , 0 , )),
	(( u'SetCmdImplicitAcceptat' , u'ImplicitAcceptat' , ), 18, (18, (), [ (3, 1, None, None) , ], 1 , 1 , 4 , 0 , 192 , (3, 0, None, None) , 0 , )),
	(( u'GetSubunitatiUser' , u'Error' , u'Value' , ), 19, (19, (), [ (16387, 2, None, None) , 
			(16396, 10, None, None) , ], 1 , 1 , 4 , 0 , 200 , (3, 0, None, None) , 0 , )),
	(( u'SetSubunitate' , u'Subunitate' , u'Value' , ), 20, (20, (), [ (3, 1, None, None) , 
			(16387, 10, None, None) , ], 1 , 1 , 4 , 0 , 208 , (3, 0, None, None) , 0 , )),
	(( u'GetListabanci' , u'Error' , u'Value' , ), 21, (21, (), [ (16387, 2, None, None) , 
			(16396, 10, None, None) , ], 1 , 1 , 4 , 0 , 216 , (3, 0, None, None) , 0 , )),
	(( u'GetClaseArticole' , u'Error' , u'Value' , ), 22, (22, (), [ (16387, 2, None, None) , 
			(16396, 10, None, None) , ], 1 , 1 , 4 , 0 , 224 , (3, 0, None, None) , 0 , )),
	(( u'GetClaseParteneri' , u'Error' , u'Value' , ), 23, (23, (), [ (16387, 2, None, None) , 
			(16396, 10, None, None) , ], 1 , 1 , 4 , 0 , 232 , (3, 0, None, None) , 0 , )),
	(( u'GetListaCatPret' , u'Error' , u'Value' , ), 24, (24, (), [ (16387, 2, None, None) , 
			(16396, 10, None, None) , ], 1 , 1 , 4 , 0 , 240 , (3, 0, None, None) , 0 , )),
	(( u'GetListaArtCatPret' , u'Error' , u'Value' , ), 25, (25, (), [ (16387, 2, None, None) , 
			(16396, 10, None, None) , ], 1 , 1 , 4 , 0 , 248 , (3, 0, None, None) , 0 , )),
	(( u'GetSoldPart' , u'PartID' , u'Error' , u'Value' , ), 26, (26, (), [ 
			(8, 1, None, None) , (16387, 2, None, None) , (16396, 10, None, None) , ], 1 , 1 , 4 , 0 , 256 , (3, 0, None, None) , 0 , )),
	(( u'GetStocArticoleExt' , u'Error' , u'Value' , ), 27, (27, (), [ (16387, 2, None, None) , 
			(16396, 10, None, None) , ], 1 , 1 , 4 , 0 , 264 , (3, 0, None, None) , 0 , )),
	(( u'GetNomenclatorArticole' , u'Error' , u'Value' , ), 28, (28, (), [ (16387, 2, None, None) , 
			(16396, 10, None, None) , ], 1 , 1 , 4 , 0 , 272 , (3, 0, None, None) , 0 , )),
	(( u'GetSolduri' , u'Error' , u'Value' , ), 29, (29, (), [ (16387, 2, None, None) , 
			(16396, 10, None, None) , ], 1 , 1 , 4 , 0 , 280 , (3, 0, None, None) , 0 , )),
	(( u'ComenziValide' , u'Value' , ), 30, (30, (), [ (16387, 10, None, None) , ], 1 , 1 , 4 , 0 , 288 , (3, 0, None, None) , 0 , )),
	(( u'ImportaComenzi' , u'Value' , ), 31, (31, (), [ (16387, 10, None, None) , ], 1 , 1 , 4 , 0 , 296 , (3, 0, None, None) , 0 , )),
	(( u'DateValide' , u'Value' , ), 32, (32, (), [ (16387, 10, None, None) , ], 1 , 1 , 4 , 0 , 304 , (3, 0, None, None) , 0 , )),
	(( u'ImportaFacturi' , u'Value' , ), 33, (33, (), [ (16387, 10, None, None) , ], 1 , 1 , 4 , 0 , 312 , (3, 0, None, None) , 0 , )),
	(( u'SetDenSubunit' , u'DenSubunit' , u'Value' , ), 34, (34, (), [ (8, 1, None, None) , 
			(16387, 10, None, None) , ], 1 , 1 , 4 , 0 , 320 , (3, 0, None, None) , 0 , )),
	(( u'IncasariValideExt' , u'Value' , ), 35, (35, (), [ (16387, 10, None, None) , ], 1 , 1 , 4 , 0 , 328 , (3, 0, None, None) , 0 , )),
	(( u'ImportaIncasariExt' , u'Value' , ), 36, (36, (), [ (16387, 10, None, None) , ], 1 , 1 , 4 , 0 , 336 , (3, 0, None, None) , 0 , )),
	(( u'ExistaFactura' , u'PartID' , u'NrFact' , u'SerieFact' , u'Value' , 
			), 37, (37, (), [ (8, 1, None, None) , (3, 1, None, None) , (8, 1, None, None) , (16387, 10, None, None) , ], 1 , 1 , 4 , 0 , 344 , (3, 0, None, None) , 0 , )),
	(( u'GetNumarFactura' , u'SimbolCarnet' , u'Error' , u'Value' , ), 38, (38, (), [ 
			(8, 1, None, None) , (16387, 2, None, None) , (16387, 10, None, None) , ], 1 , 1 , 4 , 0 , 352 , (3, 0, None, None) , 0 , )),
	(( u'GetCritDiscPeArticole' , u'Error' , u'Value' , ), 39, (39, (), [ (16387, 2, None, None) , 
			(16396, 10, None, None) , ], 1 , 1 , 4 , 0 , 360 , (3, 0, None, None) , 0 , )),
	(( u'AdaugaPartener' , u'InfoPart' , u'Value' , ), 40, (40, (), [ (8, 1, None, None) , 
			(16387, 10, None, None) , ], 1 , 1 , 4 , 0 , 368 , (3, 0, None, None) , 0 , )),
	(( u'GetCritDiscPeClase' , u'Error' , u'Value' , ), 41, (41, (), [ (16387, 2, None, None) , 
			(16396, 10, None, None) , ], 1 , 1 , 4 , 0 , 376 , (3, 0, None, None) , 0 , )),
	(( u'GetCritDiscPart' , u'Error' , u'Value' , ), 42, (42, (), [ (16387, 2, None, None) , 
			(16396, 10, None, None) , ], 1 , 1 , 4 , 0 , 384 , (3, 0, None, None) , 0 , )),
	(( u'GetStocArtDetaliat' , u'ArtID' , u'GestID' , u'Error' , u'Value' , 
			), 43, (43, (), [ (8, 1, None, None) , (8, 1, None, None) , (16387, 2, None, None) , (16396, 10, None, None) , ], 1 , 1 , 4 , 0 , 392 , (3, 0, None, None) , 0 , )),
	(( u'GetOferte' , u'Error' , u'Value' , ), 44, (44, (), [ (16387, 2, None, None) , 
			(16396, 10, None, None) , ], 1 , 1 , 4 , 0 , 400 , (3, 0, None, None) , 0 , )),
	(( u'GetListaSubunit' , u'Error' , u'Value' , ), 45, (45, (), [ (16387, 2, None, None) , 
			(16396, 10, None, None) , ], 1 , 1 , 4 , 0 , 408 , (3, 0, None, None) , 0 , )),
	(( u'GetListaLocalitati' , u'Error' , u'Value' , ), 46, (46, (), [ (16387, 2, None, None) , 
			(16396, 10, None, None) , ], 1 , 1 , 4 , 0 , 416 , (3, 0, None, None) , 0 , )),
	(( u'GetSolduriExt' , u'Error' , u'Value' , ), 47, (47, (), [ (16387, 2, None, None) , 
			(16396, 10, None, None) , ], 1 , 1 , 4 , 0 , 424 , (3, 0, None, None) , 0 , )),
	(( u'GetStocArticol' , u'ArticolID' , u'GestID' , u'Error' , u'Value' , 
			), 48, (48, (), [ (8, 1, None, None) , (8, 1, None, None) , (16387, 2, None, None) , (16396, 10, None, None) , ], 1 , 1 , 4 , 0 , 432 , (3, 0, None, None) , 0 , )),
	(( u'GetTranzactiiInCurs' , u'Error' , u'Value' , ), 49, (49, (), [ (16387, 2, None, None) , 
			(16396, 10, None, None) , ], 1 , 1 , 4 , 0 , 440 , (3, 0, None, None) , 0 , )),
	(( u'GetIntrari' , u'Error' , u'Value' , ), 50, (50, (), [ (16387, 2, None, None) , 
			(16396, 10, None, None) , ], 1 , 1 , 4 , 0 , 448 , (3, 0, None, None) , 0 , )),
	(( u'GetVanzariLuna' , u'Error' , u'Value' , ), 51, (51, (), [ (16387, 2, None, None) , 
			(16396, 10, None, None) , ], 1 , 1 , 4 , 0 , 456 , (3, 0, None, None) , 0 , )),
	(( u'GetVanzariExt' , u'Error' , u'Value' , ), 52, (52, (), [ (16387, 2, None, None) , 
			(16396, 10, None, None) , ], 1 , 1 , 4 , 0 , 464 , (3, 0, None, None) , 0 , )),
	(( u'GetNextPartID' , u'Error' , u'Value' , ), 53, (53, (), [ (16387, 2, None, None) , 
			(16392, 10, None, None) , ], 1 , 1 , 4 , 0 , 472 , (3, 0, None, None) , 0 , )),
	(( u'GetListaDelegati' , u'Error' , u'Value' , ), 54, (54, (), [ (16387, 2, None, None) , 
			(16396, 10, None, None) , ], 1 , 1 , 4 , 0 , 480 , (3, 0, None, None) , 0 , )),
	(( u'GenCodParteneri' , u'Value' , ), 55, (55, (), [ (16387, 10, None, None) , ], 1 , 1 , 4 , 0 , 488 , (3, 0, None, None) , 0 , )),
	(( u'GenCodArticole' , u'Value' , ), 56, (56, (), [ (16387, 10, None, None) , ], 1 , 1 , 4 , 0 , 496 , (3, 0, None, None) , 0 , )),
	(( u'TransferuriValide' , u'Value' , ), 57, (57, (), [ (16387, 10, None, None) , ], 1 , 1 , 4 , 0 , 504 , (3, 0, None, None) , 0 , )),
	(( u'ImportaTransferuri' , u'Value' , ), 58, (58, (), [ (16387, 10, None, None) , ], 1 , 1 , 4 , 0 , 512 , (3, 0, None, None) , 0 , )),
	(( u'GetStocuriPeGestiuni' , u'Error' , u'Value' , ), 59, (59, (), [ (16387, 2, None, None) , 
			(16396, 10, None, None) , ], 1 , 1 , 4 , 0 , 520 , (3, 0, None, None) , 0 , )),
	(( u'GetNomenclatorLocalitati' , u'Error' , u'Param2' , ), 60, (60, (), [ (16387, 2, None, None) , 
			(16396, 10, None, None) , ], 1 , 1 , 4 , 0 , 528 , (3, 0, None, None) , 0 , )),
	(( u'GetMonede' , u'Error' , u'Value' , ), 61, (61, (), [ (16387, 2, None, None) , 
			(16396, 10, None, None) , ], 1 , 1 , 4 , 0 , 536 , (3, 0, None, None) , 0 , )),
	(( u'FactIntrareValida' , u'Value' , ), 62, (62, (), [ (16387, 10, None, None) , ], 1 , 1 , 4 , 0 , 544 , (3, 0, None, None) , 0 , )),
	(( u'ImportaFactIntrare' , u'Value' , ), 63, (63, (), [ (16387, 10, None, None) , ], 1 , 1 , 4 , 0 , 552 , (3, 0, None, None) , 0 , )),
	(( u'GetNextNumarDoc' , u'SimbolCarnet' , u'TipDoc' , u'Error' , u'Value' , 
			), 64, (64, (), [ (8, 1, None, None) , (3, 1, None, None) , (16387, 2, None, None) , (16392, 10, None, None) , ], 1 , 1 , 4 , 0 , 560 , (3, 0, None, None) , 0 , )),
	(( u'GetStocArtExt2' , u'GestID' , u'Error' , u'Value' , ), 65, (65, (), [ 
			(8, 1, None, None) , (16387, 2, None, None) , (16396, 10, None, None) , ], 1 , 1 , 4 , 0 , 568 , (3, 0, None, None) , 0 , )),
	(( u'GetNomCertificate' , u'Error' , u'Value' , ), 66, (66, (), [ (16387, 2, None, None) , 
			(16396, 10, None, None) , ], 1 , 1 , 4 , 0 , 576 , (3, 0, None, None) , 0 , )),
	(( u'GetInfoArtClienti' , u'Error' , u'Value' , ), 67, (67, (), [ (16387, 2, None, None) , 
			(16396, 10, None, None) , ], 1 , 1 , 4 , 0 , 584 , (3, 0, None, None) , 0 , )),
	(( u'GetTraseeAgent' , u'DataStart' , u'DataEnd' , u'Marca' , u'Error' , 
			u'Value' , ), 68, (68, (), [ (8, 1, None, None) , (8, 1, None, None) , (3, 1, None, None) , 
			(16387, 2, None, None) , (16396, 10, None, None) , ], 1 , 1 , 4 , 0 , 592 , (3, 0, None, None) , 0 , )),
	(( u'GetPromptPayment' , u'Data' , u'Error' , u'Value' , ), 69, (69, (), [ 
			(8, 1, None, None) , (16387, 2, None, None) , (16392, 10, None, None) , ], 1 , 1 , 4 , 0 , 600 , (3, 0, None, None) , 0 , )),
	(( u'GetPromotiiCadou' , u'Data' , u'Error' , u'Value' , ), 70, (70, (), [ 
			(8, 1, None, None) , (16387, 2, None, None) , (16396, 10, None, None) , ], 1 , 1 , 4 , 0 , 608 , (3, 0, None, None) , 0 , )),
	(( u'UpdateStareUtilaje' , u'InfoUtilaje' , u'Value' , ), 71, (71, (), [ (12, 1, None, None) , 
			(16387, 10, None, None) , ], 1 , 1 , 4 , 0 , 616 , (3, 0, None, None) , 0 , )),
	(( u'InvoiceValid' , u'Value' , ), 72, (72, (), [ (16387, 10, None, None) , ], 1 , 1 , 4 , 0 , 624 , (3, 0, None, None) , 0 , )),
	(( u'ImportaInvoice' , u'Value' , ), 73, (73, (), [ (16387, 10, None, None) , ], 1 , 1 , 4 , 0 , 632 , (3, 0, None, None) , 0 , )),
	(( u'GetSeriiPromo1' , u'CodPromo1' , u'Error' , u'Value' , ), 74, (74, (), [ 
			(3, 1, None, None) , (16387, 2, None, None) , (16396, 10, None, None) , ], 1 , 1 , 4 , 0 , 640 , (3, 0, None, None) , 0 , )),
	(( u'GetSeriiCadou' , u'CodCadou' , u'Error' , u'Value' , ), 75, (75, (), [ 
			(3, 1, None, None) , (16387, 2, None, None) , (16396, 10, None, None) , ], 1 , 1 , 4 , 0 , 648 , (3, 0, None, None) , 0 , )),
	(( u'GetInfoComenzi' , u'Error' , u'Value' , ), 76, (76, (), [ (16387, 2, None, None) , 
			(16396, 10, None, None) , ], 1 , 1 , 4 , 0 , 656 , (3, 0, None, None) , 0 , )),
	(( u'GetListaArtCatPret2' , u'ArtID' , u'Error' , u'Value' , ), 77, (77, (), [ 
			(8, 1, None, None) , (16387, 2, None, None) , (16396, 10, None, None) , ], 1 , 1 , 4 , 0 , 664 , (3, 0, None, None) , 0 , )),
	(( u'GetListaCarneteExt' , u'Error' , u'Value' , ), 78, (78, (), [ (16387, 2, None, None) , 
			(16396, 10, None, None) , ], 1 , 1 , 4 , 0 , 672 , (3, 0, None, None) , 0 , )),
	(( u'GetPromoCadouManuale' , u'Data' , u'Error' , u'Value' , ), 79, (79, (), [ 
			(8, 1, None, None) , (16387, 2, None, None) , (16396, 10, None, None) , ], 1 , 1 , 4 , 0 , 680 , (3, 0, None, None) , 0 , )),
	(( u'IesiriSubunitValid' , u'Value' , ), 80, (80, (), [ (16387, 10, None, None) , ], 1 , 1 , 4 , 0 , 688 , (3, 0, None, None) , 0 , )),
	(( u'ImportaIesiriSubunit' , u'Value' , ), 81, (81, (), [ (16387, 10, None, None) , ], 1 , 1 , 4 , 0 , 696 , (3, 0, None, None) , 0 , )),
	(( u'GetUltimulTransferInGestiunea' , u'GestID' , u'Error' , u'Value' , ), 82, (82, (), [ 
			(8, 1, None, None) , (16387, 2, None, None) , (16396, 10, None, None) , ], 1 , 1 , 4 , 0 , 704 , (3, 0, None, None) , 0 , )),
	(( u'MonetareValide' , u'Value' , ), 83, (83, (), [ (16387, 10, None, None) , ], 1 , 1 , 4 , 0 , 712 , (3, 0, None, None) , 0 , )),
	(( u'ImportaMonetare' , u'Value' , ), 84, (84, (), [ (16387, 10, None, None) , ], 1 , 1 , 4 , 0 , 720 , (3, 0, None, None) , 0 , )),
	(( u'BonuriConsumValide' , u'Value' , ), 85, (85, (), [ (16387, 10, None, None) , ], 1 , 1 , 4 , 0 , 728 , (3, 0, None, None) , 0 , )),
	(( u'ImportaBonuriConsum' , u'Value' , ), 86, (86, (), [ (16387, 10, None, None) , ], 1 , 1 , 4 , 0 , 736 , (3, 0, None, None) , 0 , )),
	(( u'GetComenziInterne' , u'DeLaData' , u'Error' , u'Value' , ), 87, (87, (), [ 
			(8, 1, None, None) , (16387, 2, None, None) , (16396, 10, None, None) , ], 1 , 1 , 4 , 0 , 744 , (3, 0, None, None) , 0 , )),
	(( u'GetInfoArticol' , u'ArtID' , u'Error' , u'Value' , ), 88, (88, (), [ 
			(8, 1, None, None) , (16387, 2, None, None) , (16396, 10, None, None) , ], 1 , 1 , 4 , 0 , 752 , (3, 0, None, None) , 0 , )),
	(( u'GetInfoCmdAgent' , u'MarcaAgent' , u'TipComanda' , u'Error' , u'Value' , 
			), 89, (89, (), [ (3, 1, None, None) , (3, 1, None, None) , (16387, 2, None, None) , (16396, 10, None, None) , ], 1 , 1 , 4 , 0 , 760 , (3, 0, None, None) , 0 , )),
	(( u'GetNomenclatorLocatii' , u'Error' , u'Value' , ), 90, (90, (), [ (16387, 2, None, None) , 
			(16396, 10, None, None) , ], 1 , 1 , 4 , 0 , 768 , (3, 0, None, None) , 0 , )),
	(( u'GetSintezaStoc' , u'Error' , u'Value' , ), 91, (91, (), [ (16387, 2, None, None) , 
			(16396, 10, None, None) , ], 1 , 1 , 4 , 0 , 776 , (3, 0, None, None) , 0 , )),
	(( u'AdaugaArticol' , u'InfoArticol' , u'Value' , ), 92, (92, (), [ (8, 1, None, None) , 
			(16387, 10, None, None) , ], 1 , 1 , 4 , 0 , 784 , (3, 0, None, None) , 0 , )),
	(( u'GetNotePredare' , u'DeLaData' , u'Error' , u'Value' , ), 93, (93, (), [ 
			(8, 1, None, None) , (16387, 2, None, None) , (16396, 10, None, None) , ], 1 , 1 , 4 , 0 , 792 , (3, 0, None, None) , 0 , )),
	(( u'GetDiminuari' , u'DeLaData' , u'Error' , u'Value' , ), 94, (94, (), [ 
			(8, 1, None, None) , (16387, 2, None, None) , (16396, 10, None, None) , ], 1 , 1 , 4 , 0 , 800 , (3, 0, None, None) , 0 , )),
	(( u'GetMaririStoc' , u'DeLaData' , u'Error' , u'Value' , ), 95, (95, (), [ 
			(8, 1, None, None) , (16387, 2, None, None) , (16396, 10, None, None) , ], 1 , 1 , 4 , 0 , 808 , (3, 0, None, None) , 0 , )),
	(( u'AddDataReferinta' , u'DataRef' , u'Value' , ), 96, (96, (), [ (8, 1, None, None) , 
			(16387, 10, None, None) , ], 1 , 1 , 4 , 0 , 816 , (3, 0, None, None) , 0 , )),
	(( u'GetPromoPaketCuCadouPePrag' , u'Data' , u'Error' , u'Value' , ), 97, (97, (), [ 
			(8, 1, None, None) , (16387, 2, None, None) , (16396, 10, None, None) , ], 1 , 1 , 4 , 0 , 824 , (3, 0, None, None) , 0 , )),
	(( u'GetPromoCadouCuPrag' , u'CodPromo' , u'Error' , u'Value' , ), 98, (98, (), [ 
			(3, 1, None, None) , (16387, 2, None, None) , (16396, 10, None, None) , ], 1 , 1 , 4 , 0 , 832 , (3, 0, None, None) , 0 , )),
	(( u'SetFlagCMDOnline' , u'CMDOnline' , ), 99, (99, (), [ (3, 1, None, None) , ], 1 , 1 , 4 , 0 , 840 , (3, 0, None, None) , 0 , )),
	(( u'GetIncasariLuna' , u'Error' , u'Value' , ), 100, (100, (), [ (16387, 2, None, None) , 
			(16396, 10, None, None) , ], 1 , 1 , 4 , 0 , 848 , (3, 0, None, None) , 0 , )),
	(( u'SetContImplicitArt' , u'SimbolCont' , u'Value' , ), 101, (101, (), [ (8, 1, None, None) , 
			(16387, 10, None, None) , ], 1 , 1 , 4 , 0 , 856 , (3, 0, None, None) , 0 , )),
	(( u'NotePredareValide' , u'Value' , ), 102, (102, (), [ (16387, 10, None, None) , ], 1 , 1 , 4 , 0 , 864 , (3, 0, None, None) , 0 , )),
	(( u'ImportaNotePredare' , u'Value' , ), 103, (103, (), [ (16387, 10, None, None) , ], 1 , 1 , 4 , 0 , 872 , (3, 0, None, None) , 0 , )),
	(( u'GetTransferuri' , u'DataStart' , u'DataEnd' , u'Error' , u'Value' , 
			), 104, (104, (), [ (8, 1, None, None) , (8, 1, None, None) , (16387, 2, None, None) , (16396, 10, None, None) , ], 1 , 1 , 4 , 0 , 880 , (3, 0, None, None) , 0 , )),
	(( u'ComenziGestValide' , u'Value' , ), 105, (105, (), [ (16387, 10, None, None) , ], 1 , 1 , 4 , 0 , 888 , (3, 0, None, None) , 0 , )),
	(( u'ImportaComenziGest' , u'Value' , ), 106, (106, (), [ (16387, 10, None, None) , ], 1 , 1 , 4 , 0 , 896 , (3, 0, None, None) , 0 , )),
	(( u'GetInfoComenziGest' , u'Error' , u'Value' , ), 107, (107, (), [ (16387, 2, None, None) , 
			(16396, 10, None, None) , ], 1 , 1 , 4 , 0 , 904 , (3, 0, None, None) , 0 , )),
	(( u'GetInfoUtilaje' , u'ClasePart' , u'Error' , u'Value' , ), 108, (108, (), [ 
			(8, 1, None, None) , (16387, 2, None, None) , (16396, 10, None, None) , ], 1 , 1 , 4 , 0 , 912 , (3, 0, None, None) , 0 , )),
	(( u'GetIesiri' , u'DataStart' , u'DataEnd' , u'Error' , u'Value' , 
			), 109, (109, (), [ (8, 1, None, None) , (8, 1, None, None) , (16387, 2, None, None) , (16396, 10, None, None) , ], 1 , 1 , 4 , 0 , 920 , (3, 0, None, None) , 0 , )),
	(( u'ExistaFacturaExt' , u'PartID' , u'NrFact' , u'SerieFact' , u'Value' , 
			), 110, (110, (), [ (8, 1, None, None) , (8, 1, None, None) , (8, 1, None, None) , (16387, 10, None, None) , ], 1 , 1 , 4 , 0 , 928 , (3, 0, None, None) , 0 , )),
	(( u'SetRezervareAutomata' , u'Flag' , ), 111, (111, (), [ (3, 1, None, None) , ], 1 , 1 , 4 , 0 , 936 , (3, 0, None, None) , 0 , )),
	(( u'SetCMDFacturabile' , u'Comenzi' , u'Value' , ), 112, (112, (), [ (12, 1, None, None) , 
			(16387, 10, None, None) , ], 1 , 1 , 4 , 0 , 944 , (3, 0, None, None) , 0 , )),
	(( u'GetInfoSuplimCMD1' , u'CodComanda1' , u'Error' , u'Value' , ), 113, (113, (), [ 
			(3, 1, None, None) , (16387, 2, None, None) , (16396, 10, None, None) , ], 1 , 1 , 4 , 0 , 952 , (3, 0, None, None) , 0 , )),
	(( u'UpdatePart' , u'InfoPart' , u'Value' , ), 114, (114, (), [ (12, 1, None, None) , 
			(16387, 10, None, None) , ], 1 , 1 , 4 , 0 , 960 , (3, 0, None, None) , 0 , )),
	(( u'GetNartObjVarStru' , u'IDArticol' , u'Error' , u'Param3' , ), 115, (115, (), [ 
			(8, 1, None, None) , (16387, 2, None, None) , (16396, 10, None, None) , ], 1 , 1 , 4 , 0 , 968 , (3, 0, None, None) , 0 , )),
	(( u'SetIDArtAnalizat' , u'ArtID' , ), 116, (116, (), [ (8, 1, None, None) , ], 1 , 1 , 4 , 0 , 976 , (3, 0, None, None) , 0 , )),
	(( u'SetIDPartAnalizat' , u'PartID' , ), 117, (117, (), [ (8, 1, None, None) , ], 1 , 1 , 4 , 0 , 984 , (3, 0, None, None) , 0 , )),
	(( u'UpdateArticol' , u'InfoArticol' , u'Value' , ), 118, (118, (), [ (8, 1, None, None) , 
			(16387, 10, None, None) , ], 1 , 1 , 4 , 0 , 992 , (3, 0, None, None) , 0 , )),
	(( u'GetProcenteDiscount' , u'CodCriteriu' , u'DataAnaliza' , u'Error' , u'Value' , 
			), 119, (119, (), [ (3, 1, None, None) , (8, 1, None, None) , (16387, 2, None, None) , (16396, 10, None, None) , ], 1 , 1 , 4 , 0 , 1000 , (3, 0, None, None) , 0 , )),
	(( u'GetArticoleDiscount' , u'CodCriteriu' , u'DataAnaliza' , u'Error' , u'Value' , 
			), 120, (120, (), [ (3, 1, None, None) , (8, 1, None, None) , (16387, 2, None, None) , (16396, 10, None, None) , ], 1 , 1 , 4 , 0 , 1008 , (3, 0, None, None) , 0 , )),
	(( u'SetTipFiltruTransferuri' , u'Tip' , ), 121, (121, (), [ (3, 1, None, None) , ], 1 , 1 , 4 , 0 , 1016 , (3, 0, None, None) , 0 , )),
	(( u'ReglareInventarValida' , u'TipReglare' , u'Value' , ), 122, (122, (), [ (3, 1, None, None) , 
			(16387, 10, None, None) , ], 1 , 1 , 4 , 0 , 1024 , (3, 0, None, None) , 0 , )),
	(( u'ImportaReglareInventar' , u'TipReglare' , u'Value' , ), 123, (123, (), [ (3, 1, None, None) , 
			(16387, 10, None, None) , ], 1 , 1 , 4 , 0 , 1032 , (3, 0, None, None) , 0 , )),
	(( u'SetComenziFaraLansare' , u'FaraLansare' , ), 124, (124, (), [ (3, 1, None, None) , ], 1 , 1 , 4 , 0 , 1040 , (3, 0, None, None) , 0 , )),
	(( u'GetTransfNeoperate' , u'SimbolGest' , u'Error' , u'Value' , ), 125, (125, (), [ 
			(8, 1, None, None) , (16387, 2, None, None) , (16396, 10, None, None) , ], 1 , 1 , 4 , 0 , 1048 , (3, 0, None, None) , 0 , )),
	(( u'SetStadiuWMSTransf' , u'CodTransf' , u'Stadiu' , u'Value' , ), 126, (126, (), [ 
			(3, 1, None, None) , (3, 1, None, None) , (16387, 10, None, None) , ], 1 , 1 , 4 , 0 , 1056 , (3, 0, None, None) , 0 , )),
	(( u'GetLiniiTransfNeoperate' , u'CodTransfer' , u'Error' , u'Value' , ), 127, (127, (), [ 
			(3, 1, None, None) , (16387, 2, None, None) , (16396, 10, None, None) , ], 1 , 1 , 4 , 0 , 1064 , (3, 0, None, None) , 0 , )),
	(( u'SetReceptiiTransfOperate' , u'ListaReceptii' , u'Value' , ), 128, (128, (), [ (12, 1, None, None) , 
			(16387, 10, None, None) , ], 1 , 1 , 4 , 0 , 1072 , (3, 0, None, None) , 0 , )),
	(( u'AccesWMSGranted' , u'Error' , u'Value' , ), 129, (129, (), [ (16387, 2, None, None) , 
			(16387, 10, None, None) , ], 1 , 1 , 4 , 0 , 1080 , (3, 0, None, None) , 0 , )),
	(( u'IsAdministratorWMS' , u'Error' , u'Value' , ), 130, (130, (), [ (16387, 2, None, None) , 
			(16387, 10, None, None) , ], 1 , 1 , 4 , 0 , 1088 , (3, 0, None, None) , 0 , )),
	(( u'GetIntrariNeoperate' , u'SimbolGest' , u'Error' , u'Value' , ), 131, (131, (), [ 
			(8, 1, None, None) , (16387, 2, None, None) , (16396, 10, None, None) , ], 1 , 1 , 4 , 0 , 1096 , (3, 0, None, None) , 0 , )),
	(( u'SetStadiuWMSIntrari' , u'CodIntr' , u'Stadiu' , u'Value' , ), 132, (132, (), [ 
			(3, 1, None, None) , (3, 1, None, None) , (16387, 10, None, None) , ], 1 , 1 , 4 , 0 , 1104 , (3, 0, None, None) , 0 , )),
	(( u'GetLiniiIntrariNeoperate' , u'CodIntr' , u'Error' , u'Value' , ), 133, (133, (), [ 
			(3, 1, None, None) , (16387, 2, None, None) , (16396, 10, None, None) , ], 1 , 1 , 4 , 0 , 1112 , (3, 0, None, None) , 0 , )),
	(( u'SetReceptiiIntrariOperate' , u'ListaReceptii' , u'Value' , ), 134, (134, (), [ (12, 1, None, None) , 
			(16387, 10, None, None) , ], 1 , 1 , 4 , 0 , 1120 , (3, 0, None, None) , 0 , )),
	(( u'AdaugaGestiune' , u'InfoGest' , u'Value' , ), 135, (135, (), [ (8, 1, None, None) , 
			(16387, 10, None, None) , ], 1 , 1 , 4 , 0 , 1128 , (3, 0, None, None) , 0 , )),
	(( u'GetLivrariNeoperate' , u'SimbolGest' , u'Error' , u'Value' , ), 136, (136, (), [ 
			(8, 1, None, None) , (16387, 2, None, None) , (16396, 10, None, None) , ], 1 , 1 , 4 , 0 , 1136 , (3, 0, None, None) , 0 , )),
	(( u'SetStadiuWMSLivrari' , u'CodIes' , u'Stadiu' , u'Value' , ), 137, (137, (), [ 
			(3, 1, None, None) , (3, 1, None, None) , (16387, 10, None, None) , ], 1 , 1 , 4 , 0 , 1144 , (3, 0, None, None) , 0 , )),
	(( u'GetLiniiLivrariNeoperate' , u'CodIes' , u'Error' , u'Value' , ), 138, (138, (), [ 
			(3, 1, None, None) , (16387, 2, None, None) , (16396, 10, None, None) , ], 1 , 1 , 4 , 0 , 1152 , (3, 0, None, None) , 0 , )),
	(( u'SetLivrariOperate' , u'ListaLivrari' , u'Value' , ), 139, (139, (), [ (12, 1, None, None) , 
			(16387, 10, None, None) , ], 1 , 1 , 4 , 0 , 1160 , (3, 0, None, None) , 0 , )),
	(( u'GetInventareNeoperate' , u'SimbolGest' , u'Error' , u'Value' , ), 140, (140, (), [ 
			(8, 1, None, None) , (16387, 2, None, None) , (16396, 10, None, None) , ], 1 , 1 , 4 , 0 , 1168 , (3, 0, None, None) , 0 , )),
	(( u'SetStadiuWMSInventar' , u'CodInventar' , u'Stadiu' , u'Value' , ), 141, (141, (), [ 
			(3, 1, None, None) , (3, 1, None, None) , (16387, 10, None, None) , ], 1 , 1 , 4 , 0 , 1176 , (3, 0, None, None) , 0 , )),
	(( u'GetLiniiInventarNeoperat' , u'CodInventar' , u'Error' , u'Value' , ), 142, (142, (), [ 
			(3, 1, None, None) , (16387, 2, None, None) , (16396, 10, None, None) , ], 1 , 1 , 4 , 0 , 1184 , (3, 0, None, None) , 0 , )),
	(( u'SetFapticInventarOperat' , u'ListaFaptic' , u'CodInventar' , u'Value' , ), 143, (143, (), [ 
			(12, 1, None, None) , (3, 1, None, None) , (16387, 10, None, None) , ], 1 , 1 , 4 , 0 , 1192 , (3, 0, None, None) , 0 , )),
	(( u'GetListaUtilizatori' , u'Value' , ), 144, (144, (), [ (16396, 10, None, None) , ], 1 , 1 , 4 , 0 , 1200 , (3, 0, None, None) , 0 , )),
	(( u'SendMesajWME' , u'Mesaj' , u'Value' , ), 145, (145, (), [ (8, 1, None, None) , 
			(16387, 10, None, None) , ], 1 , 1 , 4 , 0 , 1208 , (3, 0, None, None) , 0 , )),
	(( u'GetComenziNefacturate' , u'Error' , u'Value' , ), 147, (147, (), [ (16387, 2, None, None) , 
			(16396, 10, None, None) , ], 1 , 1 , 4 , 0 , 1216 , (3, 0, None, None) , 0 , )),
	(( u'SetStadiuWMSComanda' , u'CodComanda' , u'Stadiu' , u'Value' , ), 146, (146, (), [ 
			(3, 1, None, None) , (3, 1, None, None) , (16387, 10, None, None) , ], 1 , 1 , 4 , 0 , 1224 , (3, 0, None, None) , 0 , )),
	(( u'GetLiniiComandaNefacturata' , u'CodComanda' , u'Error' , u'Value' , ), 148, (148, (), [ 
			(3, 1, None, None) , (16387, 2, None, None) , (16396, 10, None, None) , ], 1 , 1 , 4 , 0 , 1232 , (3, 0, None, None) , 0 , )),
	(( u'SetCantitatiLiniiComanda' , u'ListaLinii' , u'Value' , ), 149, (149, (), [ (12, 1, None, None) , 
			(16387, 10, None, None) , ], 1 , 1 , 4 , 0 , 1240 , (3, 0, None, None) , 0 , )),
	(( u'SetFilterNartExt' , u'Filter' , ), 150, (150, (), [ (8, 1, None, None) , ], 1 , 1 , 4 , 0 , 1248 , (3, 0, None, None) , 0 , )),
	(( u'GetPromotiiPret' , u'Data' , u'Error' , u'Value' , ), 151, (151, (), [ 
			(8, 1, None, None) , (16387, 2, None, None) , (16396, 10, None, None) , ], 1 , 1 , 4 , 0 , 1256 , (3, 0, None, None) , 0 , )),
	(( u'GetLiniiPromotiiPret' , u'DataStart' , u'Error' , u'Value' , ), 152, (152, (), [ 
			(8, 1, None, None) , (16387, 2, None, None) , (16396, 10, None, None) , ], 1 , 1 , 4 , 0 , 1264 , (3, 0, None, None) , 0 , )),
	(( u'GetPartPromotiiPret' , u'Data' , u'Error' , u'Value' , ), 153, (153, (), [ 
			(8, 1, None, None) , (16387, 2, None, None) , (16396, 10, None, None) , ], 1 , 1 , 4 , 0 , 1272 , (3, 0, None, None) , 0 , )),
	(( u'GetNomAtribute' , u'Error' , u'Value' , ), 154, (154, (), [ (16387, 2, None, None) , 
			(16396, 10, None, None) , ], 1 , 1 , 4 , 0 , 1280 , (3, 0, None, None) , 0 , )),
	(( u'GetNomValAtribute' , u'Error' , u'Value' , ), 155, (155, (), [ (16387, 2, None, None) , 
			(16396, 10, None, None) , ], 1 , 1 , 4 , 0 , 1288 , (3, 0, None, None) , 0 , )),
	(( u'GetNesositePromise' , u'Error' , u'Value' , ), 156, (156, (), [ (16387, 2, None, None) , 
			(16396, 10, None, None) , ], 1 , 1 , 4 , 0 , 1296 , (3, 0, None, None) , 0 , )),
	(( u'SetStocEgalCantDeScos' , u'Flag' , ), 157, (157, (), [ (3, 1, None, None) , ], 1 , 1 , 4 , 0 , 1304 , (3, 0, None, None) , 0 , )),
	(( u'GetTargetAgenti' , u'MarcaAgent' , u'Data' , u'Error' , u'Value' , 
			), 158, (158, (), [ (3, 1, None, None) , (8, 1, None, None) , (16387, 2, None, None) , (16396, 10, None, None) , ], 1 , 1 , 4 , 0 , 1312 , (3, 0, None, None) , 0 , )),
	(( u'SetObservatiiComanda' , u'Observatii' , u'Value' , ), 159, (159, (), [ (12, 1, None, None) , 
			(16387, 10, None, None) , ], 1 , 1 , 4 , 0 , 1320 , (3, 0, None, None) , 0 , )),
	(( u'SetValExtensiiLiniiComanda' , u'Valori' , u'Value' , ), 160, (160, (), [ (12, 1, None, None) , 
			(16387, 10, None, None) , ], 1 , 1 , 4 , 0 , 1328 , (3, 0, None, None) , 0 , )),
	(( u'GetComenziProdLansate' , u'Error' , u'Value' , ), 161, (161, (), [ (16387, 2, None, None) , 
			(16396, 10, None, None) , ], 1 , 1 , 4 , 0 , 1336 , (3, 0, None, None) , 0 , )),
	(( u'GetLiniiComandaProd' , u'CodComanda' , u'Error' , u'Value' , ), 162, (162, (), [ 
			(3, 1, None, None) , (16387, 2, None, None) , (16396, 10, None, None) , ], 1 , 1 , 4 , 0 , 1344 , (3, 0, None, None) , 0 , )),
	(( u'SetObservatiiLiniiComanda' , u'Observatii' , u'Value' , ), 163, (163, (), [ (12, 1, None, None) , 
			(16387, 10, None, None) , ], 1 , 1 , 4 , 0 , 1352 , (3, 0, None, None) , 0 , )),
	(( u'GetArticoleOptionale' , u'Error' , u'Value' , ), 164, (164, (), [ (16387, 2, None, None) , 
			(16396, 10, None, None) , ], 1 , 1 , 4 , 0 , 1360 , (3, 0, None, None) , 0 , )),
	(( u'OferteValide' , u'Value' , ), 165, (165, (), [ (16387, 10, None, None) , ], 1 , 1 , 4 , 0 , 1368 , (3, 0, None, None) , 0 , )),
	(( u'ImportaOferte' , u'Value' , ), 166, (166, (), [ (16387, 10, None, None) , ], 1 , 1 , 4 , 0 , 1376 , (3, 0, None, None) , 0 , )),
	(( u'GetTaskuri' , u'Error' , u'Value' , ), 167, (167, (), [ (16387, 2, None, None) , 
			(16396, 10, None, None) , ], 1 , 1 , 4 , 0 , 1384 , (3, 0, None, None) , 0 , )),
	(( u'GetLastPretAchiz' , u'IDArticol' , u'Error' , u'Value' , ), 168, (168, (), [ 
			(8, 1, None, None) , (16387, 2, None, None) , (16392, 10, None, None) , ], 1 , 1 , 4 , 0 , 1392 , (3, 0, None, None) , 0 , )),
	(( u'UpdateTask' , u'Infotask' , u'Value' , ), 169, (169, (), [ (8, 1, None, None) , 
			(16387, 10, None, None) , ], 1 , 1 , 4 , 0 , 1400 , (3, 0, None, None) , 0 , )),
	(( u'GeListaLocatiiMobile' , u'SimbolGest' , u'DenLocatieFixa' , u'Error' , u'Value' , 
			), 170, (170, (), [ (8, 1, None, None) , (8, 1, None, None) , (16387, 2, None, None) , (16396, 10, None, None) , ], 1 , 1 , 4 , 0 , 1408 , (3, 0, None, None) , 0 , )),
	(( u'GetStocArtWMS' , u'GestID' , u'ArtID' , u'Serie' , u'Error' , 
			u'Value' , ), 171, (171, (), [ (8, 1, None, None) , (8, 1, None, None) , (8, 1, None, None) , 
			(16387, 2, None, None) , (16396, 10, None, None) , ], 1 , 1 , 4 , 0 , 1416 , (3, 0, None, None) , 0 , )),
	(( u'GetStocLocatie' , u'CodLocatie' , u'Error' , u'Value' , ), 172, (172, (), [ 
			(3, 1, None, None) , (16387, 2, None, None) , (16396, 10, None, None) , ], 1 , 1 , 4 , 0 , 1424 , (3, 0, None, None) , 0 , )),
	(( u'GetLocatieImplicitaArt' , u'ArtID' , u'Error' , u'Value' , ), 174, (174, (), [ 
			(8, 1, None, None) , (16387, 2, None, None) , (16392, 10, None, None) , ], 1 , 1 , 4 , 0 , 1432 , (3, 0, None, None) , 0 , )),
	(( u'GetLastPreturiAchiz' , u'Error' , u'Value' , ), 173, (173, (), [ (16387, 2, None, None) , 
			(16396, 10, None, None) , ], 1 , 1 , 4 , 0 , 1440 , (3, 0, None, None) , 0 , )),
	(( u'SetValExtensiiComanda' , u'Valori' , u'Value' , ), 175, (175, (), [ (12, 1, None, None) , 
			(16387, 10, None, None) , ], 1 , 1 , 4 , 0 , 1448 , (3, 0, None, None) , 0 , )),
	(( u'GetArticoleImpliciteLocatie' , u'CodLocatie' , u'Error' , u'Value' , ), 176, (176, (), [ 
			(3, 1, None, None) , (16387, 2, None, None) , (16396, 10, None, None) , ], 1 , 1 , 4 , 0 , 1456 , (3, 0, None, None) , 0 , )),
	(( u'GetInfoLocatieMobila' , u'CodExternLocatie' , u'SimbolGest' , u'Error' , u'Value' , 
			), 177, (177, (), [ (8, 1, None, None) , (8, 1, None, None) , (16387, 2, None, None) , (16392, 10, None, None) , ], 1 , 1 , 4 , 0 , 1464 , (3, 0, None, None) , 0 , )),
	(( u'SetLocatieImplicita' , u'ArtID' , u'CodLocatie' , u'Value' , ), 178, (178, (), [ 
			(8, 1, None, None) , (3, 1, None, None) , (16387, 10, None, None) , ], 1 , 1 , 4 , 0 , 1472 , (3, 0, None, None) , 0 , )),
	(( u'GetClaseStatistice' , u'Error' , u'Value' , ), 179, (179, (), [ (16387, 2, None, None) , 
			(16396, 10, None, None) , ], 1 , 1 , 4 , 0 , 1480 , (3, 0, None, None) , 0 , )),
	(( u'CompensariValide' , u'Value' , ), 180, (180, (), [ (16387, 10, None, None) , ], 1 , 1 , 4 , 0 , 1488 , (3, 0, None, None) , 0 , )),
	(( u'ImportaCompensari' , u'Value' , ), 181, (181, (), [ (16387, 10, None, None) , ], 1 , 1 , 4 , 0 , 1496 , (3, 0, None, None) , 0 , )),
	(( u'GetnextCodEAN' , u'TipEAN' , u'ColoanaArt' , u'Error' , u'Value' , 
			), 182, (182, (), [ (8, 1, None, None) , (8, 1, None, None) , (16387, 2, None, None) , (16392, 10, None, None) , ], 1 , 1 , 4 , 0 , 1504 , (3, 0, None, None) , 0 , )),
	(( u'UpdateArtIDField' , u'IDCol' , u'Valoare' , u'CodObiect' , u'Value' , 
			), 183, (183, (), [ (8, 1, None, None) , (8, 1, None, None) , (3, 1, None, None) , (16387, 10, None, None) , ], 1 , 1 , 4 , 0 , 1512 , (3, 0, None, None) , 0 , )),
	(( u'GetInfoComenziFurn' , u'Error' , u'Value' , ), 184, (184, (), [ (16387, 2, None, None) , 
			(16396, 10, None, None) , ], 1 , 1 , 4 , 0 , 1520 , (3, 0, None, None) , 0 , )),
	(( u'GetDispLivrareNeoperate' , u'SimbolGest' , u'Error' , u'Value' , ), 185, (185, (), [ 
			(8, 1, None, None) , (16387, 2, None, None) , (16396, 10, None, None) , ], 1 , 1 , 4 , 0 , 1528 , (3, 0, None, None) , 0 , )),
	(( u'GetLiniiDispLivrare' , u'CodDispLivrare' , u'SimbolGest' , u'Error' , u'Value' , 
			), 186, (186, (), [ (3, 1, None, None) , (8, 1, None, None) , (16387, 2, None, None) , (16396, 10, None, None) , ], 1 , 1 , 4 , 0 , 1536 , (3, 0, None, None) , 0 , )),
	(( u'SetLiniiDispLivrareOperate' , u'ListaLinii' , u'Value' , ), 187, (187, (), [ (12, 1, None, None) , 
			(16387, 10, None, None) , ], 1 , 1 , 4 , 0 , 1544 , (3, 0, None, None) , 0 , )),
	(( u'SetCarnetTransfer' , u'SimbolCarnet' , u'Value' , ), 188, (188, (), [ (8, 1, None, None) , 
			(16387, 10, None, None) , ], 1 , 1 , 4 , 0 , 1552 , (3, 0, None, None) , 0 , )),
	(( u'SetDescriereLocatie' , u'CodLocatie' , u'Descriere' , u'Value' , ), 189, (189, (), [ 
			(3, 1, None, None) , (8, 1, None, None) , (16387, 10, None, None) , ], 1 , 1 , 4 , 0 , 1560 , (3, 0, None, None) , 0 , )),
	(( u'LocatiaAreStoc' , u'CodLocatie' , u'Error' , u'Value' , ), 190, (190, (), [ 
			(3, 1, None, None) , (16387, 2, None, None) , (16387, 10, None, None) , ], 1 , 1 , 4 , 0 , 1568 , (3, 0, None, None) , 0 , )),
	(( u'GetCarneteDedicate' , u'Tipcarnet' , u'Error' , u'Value' , ), 191, (191, (), [ 
			(3, 1, None, None) , (16387, 2, None, None) , (16396, 10, None, None) , ], 1 , 1 , 4 , 0 , 1576 , (3, 0, None, None) , 0 , )),
	(( u'GetInfoLocatieMobila2' , u'CodLocatie' , u'SimbolGest' , u'Error' , u'Value' , 
			), 192, (192, (), [ (3, 1, None, None) , (8, 1, None, None) , (16387, 2, None, None) , (16392, 10, None, None) , ], 1 , 1 , 4 , 0 , 1584 , (3, 0, None, None) , 0 , )),
	(( u'UpdateInfoSediu' , u'IDPart' , u'Sediu' , u'InfoSediu' , u'Value' , 
			), 193, (193, (), [ (8, 1, None, None) , (8, 1, None, None) , (8, 1, None, None) , (16387, 10, None, None) , ], 1 , 1 , 4 , 0 , 1592 , (3, 0, None, None) , 0 , )),
	(( u'GetStocArtFiltrat' , u'Filtru' , u'GestID' , u'Error' , u'Value' , 
			), 194, (194, (), [ (8, 1, None, None) , (8, 1, None, None) , (16387, 2, None, None) , (16396, 10, None, None) , ], 1 , 1 , 4 , 0 , 1600 , (3, 0, None, None) , 0 , )),
	(( u'GetListaPartFiltrata' , u'Filtru' , u'Error' , u'Value' , ), 195, (195, (), [ 
			(8, 1, None, None) , (16387, 2, None, None) , (16396, 10, None, None) , ], 1 , 1 , 4 , 0 , 1608 , (3, 0, None, None) , 0 , )),
	(( u'PlatiValide' , u'Value' , ), 196, (196, (), [ (16387, 10, None, None) , ], 1 , 1 , 4 , 0 , 1616 , (3, 0, None, None) , 0 , )),
	(( u'ImportaPlati' , u'Value' , ), 197, (197, (), [ (16387, 10, None, None) , ], 1 , 1 , 4 , 0 , 1624 , (3, 0, None, None) , 0 , )),
	(( u'GetReceptiiNeoperate' , u'SimbolGest' , u'Error' , u'Value' , ), 198, (198, (), [ 
			(8, 1, None, None) , (16387, 2, None, None) , (16396, 10, None, None) , ], 1 , 1 , 4 , 0 , 1632 , (3, 0, None, None) , 0 , )),
	(( u'GetLiniiReceptiiNeop' , u'CodIntr' , u'SimbolGest' , u'Error' , u'Value' , 
			), 199, (199, (), [ (3, 1, None, None) , (8, 1, None, None) , (16387, 2, None, None) , (16396, 10, None, None) , ], 1 , 1 , 4 , 0 , 1640 , (3, 0, None, None) , 0 , )),
	(( u'SetReceptiiPartialeIntr' , u'ListaReceptii' , u'Value' , ), 200, (200, (), [ (12, 1, None, None) , 
			(16387, 10, None, None) , ], 1 , 1 , 4 , 0 , 1648 , (3, 0, None, None) , 0 , )),
	(( u'SchimbaRezervare' , u'CodLinieComanda' , u'GestiuneVeche' , u'SerieVeche' , u'CodLocatieVeche' , 
			u'GestiuneNoua' , u'SerieNoua' , u'CodLocatieNoua' , u'Cant' , u'Value' , 
			), 201, (201, (), [ (3, 1, None, None) , (8, 1, None, None) , (8, 1, None, None) , (3, 1, None, None) , 
			(8, 1, None, None) , (8, 1, None, None) , (3, 1, None, None) , (5, 1, None, None) , (16387, 10, None, None) , ], 1 , 1 , 4 , 0 , 1656 , (3, 0, None, None) , 0 , )),
	(( u'GetComenziNeinchise' , u'DL' , u'Error' , u'Value' , ), 202, (202, (), [ 
			(3, 1, None, None) , (16387, 2, None, None) , (16396, 10, None, None) , ], 1 , 1 , 4 , 0 , 1664 , (3, 0, None, None) , 0 , )),
	(( u'GetLiniiComandaNeinchisa' , u'CodComanda' , u'Error' , u'Value' , ), 203, (203, (), [ 
			(3, 1, None, None) , (16387, 2, None, None) , (16396, 10, None, None) , ], 1 , 1 , 4 , 0 , 1672 , (3, 0, None, None) , 0 , )),
	(( u'GetIesSubunitNeoperate' , u'Error' , u'Value' , ), 204, (204, (), [ (16387, 2, None, None) , 
			(16396, 10, None, None) , ], 1 , 1 , 4 , 0 , 1680 , (3, 0, None, None) , 0 , )),
	(( u'SetStocFaraFurn' , u'Flag' , ), 205, (205, (), [ (3, 1, None, None) , ], 1 , 1 , 4 , 0 , 1688 , (3, 0, None, None) , 0 , )),
	(( u'ReteteValide' , u'Value' , ), 206, (206, (), [ (16387, 10, None, None) , ], 1 , 1 , 4 , 0 , 1696 , (3, 0, None, None) , 0 , )),
	(( u'ImportaRetete' , u'Value' , ), 207, (207, (), [ (16387, 10, None, None) , ], 1 , 1 , 4 , 0 , 1704 , (3, 0, None, None) , 0 , )),
	(( u'GetMaterialeReteta' , u'IDProdus' , u'Error' , u'Value' , ), 208, (208, (), [ 
			(8, 1, None, None) , (16387, 2, None, None) , (16396, 10, None, None) , ], 1 , 1 , 4 , 0 , 1712 , (3, 0, None, None) , 0 , )),
	(( u'GetManoperaReteta' , u'IDProdus' , u'Error' , u'Value' , ), 209, (209, (), [ 
			(8, 1, None, None) , (16387, 2, None, None) , (16396, 10, None, None) , ], 1 , 1 , 4 , 0 , 1720 , (3, 0, None, None) , 0 , )),
	(( u'ComenziFurnValide' , u'Value' , ), 210, (210, (), [ (16387, 10, None, None) , ], 1 , 1 , 4 , 0 , 1728 , (3, 0, None, None) , 0 , )),
	(( u'ImportaComenziFurn' , u'Value' , ), 211, (211, (), [ (16387, 10, None, None) , ], 1 , 1 , 4 , 0 , 1736 , (3, 0, None, None) , 0 , )),
	(( u'NCValide' , u'Value' , ), 212, (212, (), [ (16387, 10, None, None) , ], 1 , 1 , 4 , 0 , 1744 , (3, 0, None, None) , 0 , )),
	(( u'ImportaNoteContabile' , u'Value' , ), 213, (213, (), [ (16387, 10, None, None) , ], 1 , 1 , 4 , 0 , 1752 , (3, 0, None, None) , 0 , )),
	(( u'BonAchizitieValid' , u'Value' , ), 214, (214, (), [ (16387, 10, None, None) , ], 1 , 1 , 4 , 0 , 1760 , (3, 0, None, None) , 0 , )),
	(( u'ImportaBonuriAchizitie' , u'Value' , ), 215, (215, (), [ (16387, 10, None, None) , ], 1 , 1 , 4 , 0 , 1768 , (3, 0, None, None) , 0 , )),
	(( u'ModificaPartener' , u'InfoPart' , u'Value' , ), 216, (216, (), [ (8, 1, None, None) , 
			(16387, 10, None, None) , ], 1 , 1 , 4 , 0 , 1776 , (3, 0, None, None) , 0 , )),
	(( u'GetTargetPart' , u'IDPartener' , u'Data' , u'Error' , u'Value' , 
			), 217, (217, (), [ (8, 1, None, None) , (8, 1, None, None) , (16387, 2, None, None) , (16396, 10, None, None) , ], 1 , 1 , 4 , 0 , 1784 , (3, 0, None, None) , 0 , )),
	(( u'LogOff' , ), 218, (218, (), [ ], 1 , 1 , 4 , 0 , 1792 , (3, 0, None, None) , 0 , )),
	(( u'SetInclusivStoc0' , u'Flag' , ), 219, (219, (), [ (3, 1, None, None) , ], 1 , 1 , 4 , 0 , 1800 , (3, 0, None, None) , 0 , )),
	(( u'GetArtPeSedii' , u'Error' , u'Value' , ), 220, (220, (), [ (16387, 2, None, None) , 
			(16396, 10, None, None) , ], 1 , 1 , 4 , 0 , 1808 , (3, 0, None, None) , 0 , )),
	(( u'GetInfoBonConsum' , u'Numar' , u'Serie' , u'Error' , u'Value' , 
			), 221, (221, (), [ (3, 1, None, None) , (8, 1, None, None) , (16387, 2, None, None) , (16396, 10, None, None) , ], 1 , 1 , 4 , 0 , 1816 , (3, 0, None, None) , 0 , )),
	(( u'GetCmdFurnNefacturate' , u'Error' , u'Value' , ), 222, (222, (), [ (16387, 2, None, None) , 
			(16396, 10, None, None) , ], 1 , 1 , 4 , 0 , 1824 , (3, 0, None, None) , 0 , )),
	(( u'SetAllSubunitFlag' , u'Flag' , ), 223, (223, (), [ (3, 1, None, None) , ], 1 , 1 , 4 , 0 , 1832 , (3, 0, None, None) , 0 , )),
	(( u'GetAllIntrFurnNeoperate' , u'Error' , u'Value' , ), 224, (224, (), [ (16387, 2, None, None) , 
			(16396, 10, None, None) , ], 1 , 1 , 4 , 0 , 1840 , (3, 0, None, None) , 0 , )),
	(( u'GetIntrSubunitNeoperate' , u'Error' , u'Value' , ), 225, (225, (), [ (16387, 2, None, None) , 
			(16396, 10, None, None) , ], 1 , 1 , 4 , 0 , 1848 , (3, 0, None, None) , 0 , )),
	(( u'GetComenziSubunitNefact' , u'Error' , u'Value' , ), 226, (226, (), [ (16387, 2, None, None) , 
			(16396, 10, None, None) , ], 1 , 1 , 4 , 0 , 1856 , (3, 0, None, None) , 0 , )),
	(( u'ComenziSubunitValide' , u'Value' , ), 227, (227, (), [ (16387, 10, None, None) , ], 1 , 1 , 4 , 0 , 1864 , (3, 0, None, None) , 0 , )),
	(( u'ImportaComenziSubunit' , u'Value' , ), 228, (228, (), [ (16387, 10, None, None) , ], 1 , 1 , 4 , 0 , 1872 , (3, 0, None, None) , 0 , )),
	(( u'GetSolduriFurn' , u'Error' , u'Value' , ), 229, (229, (), [ (16387, 2, None, None) , 
			(16396, 10, None, None) , ], 1 , 1 , 4 , 0 , 1880 , (3, 0, None, None) , 0 , )),
	(( u'GetContracteAbonament' , u'DataReferinta' , u'Error' , u'Value' , ), 230, (230, (), [ 
			(8, 1, None, None) , (16387, 2, None, None) , (16396, 10, None, None) , ], 1 , 1 , 4 , 0 , 1888 , (3, 0, None, None) , 0 , )),
	(( u'GetLiniiContract' , u'CodContract' , u'Error' , u'Value' , ), 231, (231, (), [ 
			(3, 1, None, None) , (16387, 2, None, None) , (16396, 10, None, None) , ], 1 , 1 , 4 , 0 , 1896 , (3, 0, None, None) , 0 , )),
	(( u'AdaugaLinieContract' , u'CodContract' , u'InfoLinie' , u'Value' , ), 232, (232, (), [ 
			(3, 1, None, None) , (8, 1, None, None) , (16387, 10, None, None) , ], 1 , 1 , 4 , 0 , 1904 , (3, 0, None, None) , 0 , )),
	(( u'ConectatlaServer' , u'Value' , ), 233, (233, (), [ (16387, 10, None, None) , ], 1 , 1 , 4 , 0 , 1912 , (3, 0, None, None) , 0 , )),
	(( u'GetCriteriiDiscount' , u'Error' , u'Value' , ), 234, (234, (), [ (16387, 2, None, None) , 
			(16396, 10, None, None) , ], 1 , 1 , 4 , 0 , 1920 , (3, 0, None, None) , 0 , )),
	(( u'ExistaFacturaIntrare' , u'PartID' , u'NrFact' , u'SerieFact' , u'Value' , 
			), 235, (235, (), [ (8, 1, None, None) , (3, 1, None, None) , (8, 1, None, None) , (16387, 10, None, None) , ], 1 , 1 , 4 , 0 , 1928 , (3, 0, None, None) , 0 , )),
	(( u'GetIncasariFactura' , u'PartID' , u'NrFact' , u'SerieFact' , u'Value' , 
			), 236, (236, (), [ (8, 1, None, None) , (3, 1, None, None) , (8, 1, None, None) , (16396, 10, None, None) , ], 1 , 1 , 4 , 0 , 1936 , (3, 0, None, None) , 0 , )),
	(( u'GetInfoPart' , u'PartID' , u'Error' , u'Value' , ), 237, (237, (), [ 
			(8, 1, None, None) , (16387, 2, None, None) , (16396, 10, None, None) , ], 1 , 1 , 4 , 0 , 1944 , (3, 0, None, None) , 0 , )),
	(( u'InchideComanda' , u'CodComanda' , u'Value' , ), 238, (238, (), [ (3, 1, None, None) , 
			(16387, 10, None, None) , ], 1 , 1 , 4 , 0 , 1952 , (3, 0, None, None) , 0 , )),
	(( u'ContracteValide' , u'Value' , ), 239, (239, (), [ (16387, 10, None, None) , ], 1 , 1 , 4 , 0 , 1960 , (3, 0, None, None) , 0 , )),
	(( u'ImportaContracte' , u'Value' , ), 240, (240, (), [ (16387, 10, None, None) , ], 1 , 1 , 4 , 0 , 1968 , (3, 0, None, None) , 0 , )),
	(( u'SerializareDispLivrare' , u'CodComanda' , u'Serializare' , u'Value' , ), 241, (241, (), [ 
			(3, 1, None, None) , (12, 1, None, None) , (16387, 10, None, None) , ], 1 , 1 , 4 , 0 , 1976 , (3, 0, None, None) , 0 , )),
	(( u'SerializareIntrari' , u'CodIntr' , u'Serializare' , u'Value' , ), 242, (242, (), [ 
			(3, 1, None, None) , (12, 1, None, None) , (16387, 10, None, None) , ], 1 , 1 , 4 , 0 , 1984 , (3, 0, None, None) , 0 , )),
	(( u'SetCatPretImplicita' , u'IDCatPret' , u'Value' , ), 243, (243, (), [ (8, 1, None, None) , 
			(16387, 10, None, None) , ], 1 , 1 , 4 , 0 , 1992 , (3, 0, None, None) , 0 , )),
	(( u'SetSimbolClasaFiltrare' , u'SimbolClasa' , u'Value' , ), 244, (244, (), [ (8, 1, None, None) , 
			(16387, 10, None, None) , ], 1 , 1 , 4 , 0 , 2000 , (3, 0, None, None) , 0 , )),
	(( u'ModificaHeaderContract' , u'CodContract' , u'InfoHeader' , u'Value' , ), 245, (245, (), [ 
			(3, 1, None, None) , (8, 1, None, None) , (16387, 10, None, None) , ], 1 , 1 , 4 , 0 , 2008 , (3, 0, None, None) , 0 , )),
	(( u'ModificaLinieContract' , u'CodLinieContract' , u'InfoLinie' , u'Value' , ), 246, (246, (), [ 
			(3, 1, None, None) , (8, 1, None, None) , (16387, 10, None, None) , ], 1 , 1 , 4 , 0 , 2016 , (3, 0, None, None) , 0 , )),
	(( u'GetAvizeNefacturate' , u'Error' , u'Value' , ), 247, (247, (), [ (16387, 2, None, None) , 
			(16396, 10, None, None) , ], 1 , 1 , 4 , 0 , 2024 , (3, 0, None, None) , 0 , )),
	(( u'GetLiniiAvizNefacturat' , u'CodAviz' , u'Error' , u'Value' , ), 248, (248, (), [ 
			(3, 1, None, None) , (16387, 2, None, None) , (16396, 10, None, None) , ], 1 , 1 , 4 , 0 , 2032 , (3, 0, None, None) , 0 , )),
]

RecordMap = {
}

CLSIDToClassMap = {
	'{A4286FD3-EB00-40FC-AE02-AC9611532A43}' : WMDocImpObject,
	'{FDF13A22-BD23-46D5-995D-94C3F7F83F64}' : IWMDocImpObject,
}
CLSIDToPackageMap = {}
win32com.client.CLSIDToClass.RegisterCLSIDsFromDict( CLSIDToClassMap )
VTablesToPackageMap = {}
VTablesToClassMap = {
	'{FDF13A22-BD23-46D5-995D-94C3F7F83F64}' : 'IWMDocImpObject',
}


NamesToIIDMap = {
	'IWMDocImpObject' : '{FDF13A22-BD23-46D5-995D-94C3F7F83F64}',
}


