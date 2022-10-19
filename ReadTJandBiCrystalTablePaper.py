# %%
from locale import normalize
from tkinter import N
from turtle import color, colormode, pos
import numpy as np
import os
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.pyplot as plt
from matplotlib import transforms
from scipy import optimize
from scipy import stats
from sklearn.neighbors import NearestNeighbors
import GeometryFunctions as gf
import GeneralLattice as gl
import LAMMPSTool as LT
import LatticeDefinitions as ld
import re
import sys
import matplotlib.lines as mlines
from sklearn.ensemble import GradientBoostingRegressor
import MiscFunctions as mf
from pickle import FALSE
from scipy.optimize import curve_fit

# Assumes columns are 2: GBPE, 3: TJPE, 4: GB Lattice Atoms PE 5: TJLattice Atoms, 6: Number of GB atoms, 7 Number of TJ atoms,, 8 Number of PTM GB Atoms, 9 Number of PTM TJ Atoms, 10 is TJ Length

# %%
#plt.rc('text', usetex=True)
# plt.rcParams['text.latex.preamble']=[r"\usepackage{amsmath}"]
#plt.rcParams['text.latex.preamble'] = r"\usepackage{bm} \usepackagstrDeltaAxisstrDeltaAxise{amsmath}"
plt.rc('text', usetex=True)
plt.rc('text.latex', preamble=r'\usepackage{amsmath} \usepackage{bm}')
#plt.rc('text', usetex=True)
#plt.rcParams["text.latex.preamble"].join([r"\usepackage{bm},"r"\usepackage{amsmath}",])
plt.rcParams['figure.dpi'] = 300
#matplotlib.verbose.level = 'debug-annoying'
strDeltaAxis = r'$\bm{\delta_{i}}$'
strFAxis = r'$F_{L}$ in eV $\AA^{-2}$'
strCSLAxis = r'$\gamma_{\mathrm{CSL}}$ in eV $\AA^{-2}$'
strCurved = r'$\gamma_{\mathrm{curved}}$ in eV $\AA^{-2}$'
strSigmaAxis = 'CSL $\Sigma$ value'
strTJAxis = r'$\bar{\lambda}_{\mathrm{TJ}}$ in eV $\AA^{-1}$'
strMeanTJAxis = r'Mean of $\bar{\lambda}_{\mathrm{TJ}}$ in eV $\AA^{-1}$'
strNWGBAxis = r'$\gamma_{\mathrm{NW}}$ in eV $\AA^{-2}$'
strGBAxis = r'$\bar{\gamma}$ in eV $\AA^{-2}$'
strDMinAxis = r'$10d_{\mathrm{min}}/r_0$'

lstAxes = ['Axis001', 'Axis101', 'Axis111']
lstLegendAxes = ['Axis [001]', 'Axis [101]', 'Axis [111]']
lstAxis001 = [5, 13, 17, 29, 37]
#lstAxis001 = [5,29]
lstAxis101 = [3, 9, 11, 19, 27]
#lstAxis101 = [3,9,11,17]
lstAxis111 = [3, 7, 13, 21, 31]
#lstAxis111 = [3,7]
lstSigmas = [lstAxis001, lstAxis101, lstAxis111]
lstAllSigma = []


dctAllTJ = dict()
dctCSLGB = dict()
dctAllGB = dict()
dctCSLMeta = dict()
dctSGBExcess = dict()
dctLists = dict()
dctLists[lstAxes[0]] = lstAxis001
dctLists[lstAxes[1]] = lstAxis101
dctLists[lstAxes[2]] = lstAxis111
for i in lstAxes:
    lstAllSigma.extend(dctLists[i])
lstAllSigma = np.unique(lstAllSigma).tolist()
lstAllSigmaPositions = []


dctDMin = dict()

dctDMin['Axis001,5'] = [list(range(6, 9))]
dctDMin['Axis001,13'] = [[6, 7]]
dctDMin['Axis001,17'] = [list(range(0, 8))]
dctDMin['Axis001,29'] = [list(range(2, 8))]
dctDMin['Axis001,37'] = [list(range(5, 8))]

dctDMin['Axis101,3'] = [list(range(0, 9))]
dctDMin['Axis101,9'] = [list(range(5, 9))]  # GB periodic unit rearrangement
dctDMin['Axis101,11'] = [list(range(0, 8))]
#dctDMin['Axis101,17'] = [list(range(7,8))]
dctDMin['Axis101,19'] = [list(range(0, 8))]
# disconnections nucleated in GB simulation cell
dctDMin['Axis101,27'] = [list(range(6, 9))]

# disconnections nucleated in GB simulation cell
dctDMin['Axis111,3'] = [list(range(6, 9))]
# disconnections nucleated in GB simulation cell
dctDMin['Axis111,7'] = [list(range(7, 9))]
# disconnections nucleated in GB simulatin cell
dctDMin['Axis111,13'] = [list(range(0, 9))]
# dctDMin['Axis111,19'] = [list(range(6,9))] #discconections nucleated in GB simulation
# distorted grain boundary disconnections in TJ simulation cell cylindrical grain disrupted
dctDMin['Axis111,21'] = [list(range(6, 9))]
dctDMin['Axis111,31'] = [[0, 1, 2, 3, 5, 6, 7]]
lstColours = ['darkblue', 'purple', 'peru']


class CSLGBData(object):
    def __init__(self, arrAxis, intSigma, inValues):
        self.__Axis = arrAxis.astype('int')
        self.__Sigma = intSigma
        self.__OriginalValues = inValues
        self.__OriginalLength = len(inValues)
        lstRows = []
        intCheck = inValues[0, 3].astype('int')
        lstRows.append(inValues[0])
        for j in range(1, len(inValues)):
            if inValues[j, 3].astype('int') != intCheck:
                intCheck = inValues[j, 3]
                lstRows.append(inValues[j])
        self.__Values = np.vstack(lstRows)
        self.__Length = len(self.__Values)
        self.__DMinValues = np.unique(self.__Values[:, 0])*10

    def GetDMinValues(self, lstDMask=None):
        return self.__DMinValues

    def GetOriginalValues(self):
        return self.__OriginalValues

    def GetValues(self):
        return self.__Values

    def FindCSLExcess(self, fltPEDatum=-3.36):
        return self.__Values[:, 1] - (fltPEDatum*self.__Values[:, 3])

    def GetCSLExcessPerArea(self, fltPEDatum=-3.36, blnUnique=True):
        arrArea = self.__Values[:, -1]
        return self.FindCSLExcess(fltPEDatum)/(2*arrArea)

    def GetSigmaValue(self):
        return self.__Sigma

    def GetSigmaArrays(self, lstPossibleSigmas):
        intValue = lstPossibleSigmas.index(self.__Sigma)
        return (intValue*np.ones(self.__Length))

    def GetAxis(self):
        return self.__Axis

    def GetLength(self):
        return self.__Length

    def GetCSLExcessByDMin(self, arrDMin: np.array, fltPEDatum=-3.36):
        arrRows = arrRows = np.isin((10*self.__OriginalValues[:, 0]), arrDMin)
        arrCSL = self.__OriginalValues[arrRows]
        lstReturn = []
        intAtoms = arrCSL[0, 3]
        for a in arrCSL:
            if a[3] < intAtoms:
                lstReturn.append(a)
                intAtoms = a[3]
            elif len(lstReturn) == 0:
                lstReturn.append(a)
        arrCSL = np.vstack(lstReturn)
        arrExcess = (arrCSL[:, 1] - (fltPEDatum *
                                     arrCSL[:, 3]))/(2*arrCSL[:, -1])
        arrDMin = 10*arrCSL[:, 0]
        return arrDMin, arrExcess


class TJAndGBData(object):
    def __init__(self, arrAxis, intSigma, inValues, lstDMinValues, intNumberOfTripleLines):
        self.__Axis = arrAxis.astype('int')
        self.__Sigma = intSigma
        self.__OriginalValues = inValues
        arrRows = np.isin(inValues[:, 1], lstDMinValues)
        inValues = inValues[arrRows]
        intDelta = int(max(inValues[:, 0]))+1
        self.__Displacments = []
        intDMax = len(lstDMinValues)
        #lstRows = []
        lstPositions = []
        for i in range(0, intDelta):
            arrCheck = inValues[intDMax*i, [6, 7]].astype('int')
            # lstRows.append(inValues[intDMax*i])
            lstPositions.append(intDMax*i)
            for j in range(1, intDMax):
                arrCurrent = inValues[intDMax*i+j, [6, 7]].astype('int')
                if not(np.all(arrCurrent == arrCheck)):
                    arrCheck = arrCurrent
                    # lstRows.append(inValues[intDMax*i+j])
                    lstPositions.append(intDMax*i+j)
        #arrValues = np.vstack(lstRows)
        self.__DeltaRange = intDelta
        self.__DMinValues = lstDMinValues
        self.__ArrayPositions = np.array(lstPositions)
        self.__Values = inValues[self.__ArrayPositions]
        self.__Length = len(self.__Values)
        self.__NumberOfTripleLines = intNumberOfTripleLines

    def GetLength(self):
        return self.__Length

    def GetAxis(self):
        return self.__Axis

    def GetExcessEnergy(self, fltDatum=-3.36):
        return self.__Values[:, 3] - fltDatum*self.__Values[:, 7]

    def GetSigma(self):
        return self.__Sigma

    def GetOriginaValues(self):
        return self.__OriginalValues

    def GetValues(self):
        return self.__Values

    def GetDMinValues(self):
        return self.__DMinValues

    def FindCSLExcess(self, inCSLArray, fltPEDatum=-3.36):
        return inCSLArray[:, 1] - (fltPEDatum*inCSLArray[:, 3])

    def FindTotalGBArea(self):
        objSigma = gl.SigmaCell(self.__Axis, ld.FCCCell)
        objSigma.MakeCSLCell(self.__Sigma)
        arrSigmaBasis = objSigma.GetBasisVectors()
        s0 = np.linalg.norm(arrSigmaBasis, axis=1)[0]
        s1 = np.linalg.norm(arrSigmaBasis, axis=1)[1]
        s2 = np.linalg.norm(arrSigmaBasis, axis=1)[2]
        intHeight = 4
        intAtoms = 1.5*10**5
        intAtomsPerCell = 4
        a = 4.05  # lattice parameter
        h = a*np.round(intHeight/s2, 0)
        i = np.sqrt(intAtoms*a/(32*12*intAtomsPerCell *
                                h*np.linalg.det(arrSigmaBasis)))
        i = np.round(i, 0).astype('int')
        r = 2*a*s1*i
        w = 32*a*i*s0
        l = 12*a*i*s1
        # there are two planar grain boundaries and two cylindrical grain boundaries
        return 2*l*h*s2, 4*r*np.pi*h*s2

    # returns excess energy weighted by twice the curved grain boundaries to 1 planar oundary
    def GetMeanGB(self, inCSLGBData: CSLGBData):
        fltGBArea, fltCylinderArea = self.FindTotalGBArea()
        arrCSLArray = inCSLGBData.GetOriginalValues()
        intRatio = len(self.__OriginalValues)/len(arrCSLArray)
        arrCSLArray = np.tile(arrCSLArray, (10, 1))
        arrAtoms = arrCSLArray[:, -2] - self.__OriginalValues[:, 6]
        fltMu = self.__OriginalValues[0, 4]/self.__OriginalValues[0, 8]
        arrGB = self.__OriginalValues[:, 2] + (fltMu*arrAtoms)
        arrExcessCSL = self.FindCSLExcess(arrCSLArray)
        arrExcessCSL = arrExcessCSL[self.__ArrayPositions]
        arrGB = arrGB[self.__ArrayPositions]
        arrCSL = arrCSLArray[:, 1][self.__ArrayPositions]
        return (arrExcessCSL/fltGBArea + 2*(arrGB-arrCSL)/fltCylinderArea)/3

    def GetCylindricalExcessPerArea(self, inCSLGBData: CSLGBData):
        fltCylinderArea = self.FindTotalGBArea()[1]
        arrCSLArray = inCSLGBData.GetOriginalValues()
        arrCSLArray = np.tile(arrCSLArray, (10, 1))
        arrAtoms = arrCSLArray[:, -2] - self.__OriginalValues[:, 6]
        fltMu = self.__OriginalValues[0, 4]/self.__OriginalValues[0, 8]
        arrGB = self.__OriginalValues[:, 2] + (fltMu*arrAtoms)
        arrGB = arrGB[self.__ArrayPositions]
        arrCSL = arrCSLArray[:, 1][self.__ArrayPositions]
        return (arrGB-arrCSL)/fltCylinderArea

    def AdjustEnergyByMassBalance(self):
       # arrNMax = np.max(self.__Values[:, [6, 7]])*np.ones(len(self.__Values))
        arrMu = self.__Values[:, 4]/self.__Values[:, 8]
        arrTJAdjusted = self.__Values[:, 3] + \
            arrMu*(self.__Values[:, 6]-self.__Values[:, 7])
        arrGBAdjusted = self.__Values[:, 2]  # + \
        # arrMu*(arrNMax-self.__Values[:, 6])
        return arrTJAdjusted, arrGBAdjusted

    def GetExcessEnergies(self):
        arrMu = self.__Values[0, 4]/self.__Values[0, 8]
        arrTJAdjusted = self.__Values[:, 3] - arrMu*self.__Values[:, 7]
        arrGBAdjusted = self.__Values[:, 2] - arrMu*self.__Values[:, 6]
        return arrTJAdjusted, arrGBAdjusted

    def GetTJExcessPerLength(self):
        fltLength = self.__Values[0, -1]*self.__NumberOfTripleLines
        arrTJAdjusted, arrGBAdjusted = self.AdjustEnergyByMassBalance()
        arrTotalExcessEnergy = arrTJAdjusted-arrGBAdjusted
        return arrTotalExcessEnergy/fltLength

    def GetMinimumTJForEachDelta(self):
        lstValues = []
        arrTJExcess = self.GetTJExcessPerLength()
        for j in range(self.__DeltaRange):
            arrRows = np.where(self.__Values[:, 0] == j)[0]
            if len(arrRows) > 0:
                arrCurrentValues = arrTJExcess[arrRows]
                arrMin = np.argmin(arrCurrentValues)
                lstValues.append(arrRows[arrMin])
        return np.array(lstValues)

    # only looks at nearest triple line
    def GetTJEnergyGradient(self, fltLattice: float):
        lstValues = []
        objCSL = gl.SigmaCell(self.__Axis, ld.FCCCell)
        objCSL.MakeCSLCell(self.__Sigma)
        arrBasis = fltLattice*objCSL.GetBasisVectors()
        arrTJExcess = self.GetTJExcessPerLength()
        arrUniqueDMin = np.sort(np.unique(self.__Values[:, 1]))
        for j in arrUniqueDMin:
            arrRows = np.where(self.__Values[:, 1] == j)[0]
            arrDeltaRows = self._TJAndGBData__Values[arrRows, 0].astype('int')
            if len(arrRows) > 0:
                arrCurrentValues = arrTJExcess[arrRows]
                arrMin = np.argmin(arrCurrentValues)
                objPeriodicTree = gf.PeriodicWrapperKDTree(np.array([self.__Displacments[arrDeltaRows[arrMin]]]), fltLattice*objCSL.GetBasisVectors(
                ), gf.FindConstraintsFromBasisVectors(arrBasis), np.max(np.linalg.norm(arrBasis)))
                arrDistances, arrIndices = objPeriodicTree.Pquery(
                    self.__Displacments[arrDeltaRows], 1)
                arrFValues = arrCurrentValues - arrCurrentValues[arrMin]
                arrDistances = arrDistances
                arrFValues = np.delete(arrFValues, arrMin)
                arrDistances2 = np.delete(arrDistances, arrMin)
                arrCutOff = np.where(arrDistances2 < 4.05)[0]
                # if len(arrDistances2) > 0:
                #     intMin = np.argmin(arrDistances2)
                if len(arrFValues) > 0:
                    lstValues.append(
                        arrFValues[arrCutOff]/arrDistances2[arrCutOff])
        # return lstValues
        return np.concatenate(lstValues, axis=0)

    def GetTJDifferenceForEachDelta(self):
        lstValues = []
        arrTJExcess = self.GetTJExcessPerLength()
        for j in range(self.__DeltaRange):
            arrRows = np.where(self.__Values[:, 0].astype('int') == j)[0]
            arrCurrentValues = arrTJExcess[arrRows]
            intLength = len(arrCurrentValues)
            lstCurrentValues = []
            if intLength <= 1:
                lstCurrentValues.append(np.array([0]))
            else:
                for k in range(1, intLength):
                    lstCurrentValues.append(
                        arrCurrentValues[k] - arrCurrentValues[k-1])
            lstValues.append(np.array(lstCurrentValues))
        return lstValues

    def GetTJForEachDelta(self):
        lstValues = []
        lstDMinPosition = []
        arrTJExcess = self.GetTJExcessPerLength()
        for j in range(self.__DeltaRange):
            arrRows = np.where(self.__Values[:, 0].astype('int') == j)[0]
            arrCurrentValues = arrTJExcess[arrRows]
            lstValues.append(arrCurrentValues)
            lstDMinPosition.append(self.__Values[arrRows, 1])
        return lstValues

    def GetTJForEachDMin(self):
        lstValues = []
        arrTJExcess = self.GetTJExcessPerLength()
        for j in self.__DMinValues:
            arrRows = np.where(self.__Values[:, 1] == j)[0]
            if len(arrRows) > 0:
                arrCurrentValues = arrTJExcess[arrRows]
                lstValues.append(arrCurrentValues)
        return lstValues

    def GetMinimumTJForEachDMin(self):
        lstValues = []
        arrTJExcess = self.GetTJExcessPerLength()
        for j in self.__DMinValues:
            arrRows = np.where(self.__Values[:, 1] == j)[0]
            if len(arrRows) > 0:
                arrCurrentValues = arrTJExcess[arrRows]
                arrMin = np.argmin(arrCurrentValues)
                lstValues.append(arrRows[arrMin])
        return np.array(lstValues)

    def GetSigmaArrays(self, lstPossibleSigmas):
        intValue = lstPossibleSigmas.index(self.__Sigma)
        return (intValue*np.ones(self.__Length))

    def GetPositionsByDMin(self):
        lstPositions = []
        lstUsedDMins = []
        for i in self.__DMinValues:
            lstRows = []
            for j in range(10):
                arrRows = np.where((self.__Values[:, 1].astype('int') == i) & (
                    self.__Values[:, 0].astype('int') == j))[0]
                if len(arrRows) > 0:
                    lstRows.append(arrRows[0])
            if len(lstRows) > 0:
                lstPositions.append(np.array(lstRows))
                lstUsedDMins.append(i)
        return lstPositions, lstUsedDMins

    def GetPositionsByDelta(self):
        lstPositions = []
        lstDMinsPositions = []
        lstUniqueDMins = list(np.sort(np.unique(self.__Values[:, 1])))
        for i in range(self.__DeltaRange):
            arrRows = np.where((self.__Values[:, 0] == i))[0]
            if len(arrRows) > 0:
                lstPositions.append(arrRows)
            arrDMins = self.__Values[arrRows, 1]
            lstIndex = list(map(lambda x: lstUniqueDMins.index(x), arrDMins))
            lstDMinsPositions.append(lstIndex)
        return lstPositions, lstDMinsPositions

    def SetDisplacements(self, inArray):
        self.__Displacments = inArray[:-1]

    def GetDisplacements(self):
        return self.__Displacments

    def FindExcessStrainEnergy(self):
        return (self.__Values[:, 5]/self.__Values[:, 9]-self.__Values[:, 5]/self.__Values[:, 9])

    def GetAtomMergeDifferences(self):
        lstAllRows = []
        for j in range(1,len(self.__DMinValues)):
            lstTemp = []
            intRows2 = np.where(self.__OriginalValues[:,1] == self.__DMinValues[j])[0]
            intRows1 = np.where(self.__OriginalValues[:,1] == self.__DMinValues[j]-1)[0]
            arrDifference = self.__OriginalValues[intRows2] - self.__OriginalValues[intRows1]
            arrDelete = np.where(np.all(arrDifference[:,2:] == 0, axis=1))[0]
            intRows1 = np.delete(intRows1, arrDelete)
            intRows2 = np.delete(intRows2, arrDelete)
            if len(intRows1) > 0:
                lstTemp.append(intRows1)
                lstTemp.append(intRows2)
                lstAllRows.append(np.vstack(lstTemp)) 
        lstValueRows = [] #row numbers for self.__Values from self.__OriginalValues
        for l in lstAllRows:
            lstTemp = []
            lstRows1 = []
            for j in l[0]:
                arrRows1 = np.where(np.all(self.__Values[:,2:]==self.__OriginalValues[j,2:],axis=1))[0]
                if len(arrRows1) > 0:
                    lstRows1.append(arrRows1[0])
            lstRows2 = []
            for k in l[1]:
                arrRows2 = np.where(np.all(self.__Values[:,2:]==self.__OriginalValues[k,2:],axis=1))[0]
                if len(arrRows2) > 0 and len(arrRows1) > 0:
                    lstRows2.append(arrRows2[0])
            if len(lstRows1) > 0 and len(lstRows2) > 0:
                lstTemp.append(np.array(lstRows1))
                lstTemp.append(np.array(lstRows2))
                arrValues = np.vstack(lstTemp)
                lstValueRows.append(arrValues)
        return lstValueRows   
        # lstAllPositions = []
        # lstAllDMins = []
        # for j in range(self.__DeltaRange):
        #     arrDMins = np.unique(self.__Values[:, 1])    
        #     if len(arrDMins) > 1:  # need at least two values
        #         lstPos1 = []
        #         lstPos2 = []
        #         lstNGB = []
        #         lstNTJ = []
        #         for k in range(1, len(arrDMins)):
        #             intRow2 = np.where((self.__Values[:, 0] == j) & (
        #                 self.__Values[:, 1] == arrDMins[k]))[0][0]
        #             intRow1 = np.where((self.__Values[:, 0] == j) & (
        #                 self.__Values[:, 1] == arrDMins[k-1]))[0][0]
        #             lstPos2.append(intRow2)
        #             lstPos1.append(intRow1)
        # return lstNGB, lstNTJ, lstPos1, lstPos2

        
        
        # lstAllPositions = []
        # lstAllDMins = []
        # for j in range(self.__DeltaRange):
        #     arrDMins = np.unique(self.__Values[:, 1])    
        #     if len(arrDMins) > 1:  # need at least two values
        #         lstPos1 = []
        #         lstPos2 = []
        #         lstNGB = []
        #         lstNTJ = []
        #         for k in range(1, len(arrDMins)):
        #             intRow2 = np.where((self.__Values[:, 0] == j) & (
        #                 self.__Values[:, 1] == arrDMins[k]))[0][0]
        #             intRow1 = np.where((self.__Values[:, 0] == j) & (
        #                 self.__Values[:, 1] == arrDMins[k-1]))[0][0]
        #             lstPos2.append(intRow2)
        #             lstPos1.append(intRow1)
        # return lstNGB, lstNTJ, lstPos1, lstPos2

        # for i in arrDMins:
        #     arrRows = np.where(self.__Values[:,1] == i)[0]
        #     lstValues.append(arrDifferences[arrRows])
        #     lstDMins.append(i)
        # return lstValues, lstDMins


def FitLine(x, a, b):
    return a*x + b


for strAxis in lstAxes:
    strBiDir = '/home/p17992pt/csf4_scratch/BiCrystal/'
    strTJDir = '/home/p17992pt/csf4_scratch/TJCylinder/'
    arrAxis = np.zeros(3)
    for j in range(3):
        arrAxis[j] = int(strAxis[j-3])
    for intSigma in dctLists[strAxis]:
        strBiSigma = 'Sigma' + str(intSigma) + '/'
        strTJSigma = 'TJSigma' + str(intSigma) + '/'
        arrCSLValues = np.loadtxt(
            strBiDir + strAxis + '/' + strBiSigma + 'Values.txt')
        objCSL = CSLGBData(arrAxis, intSigma, arrCSLValues)
        arrTJValues = np.loadtxt(
            strTJDir + strAxis + '/' + strTJSigma + 'Values.txt')
        arrDisplacements = np.loadtxt(
            strTJDir + strAxis + '/' + strTJSigma + 'AllRandomPoints')
        strDMINKey = strAxis + ',' + str(intSigma)
        lstDMinValues = dctDMin[strDMINKey]
        objTJAndGBData = TJAndGBData(
            arrAxis, intSigma, arrTJValues, lstDMinValues[0], 4)
        objTJAndGBData.SetDisplacements(arrDisplacements)
        dctAllGB[strDMINKey] = objCSL
        dctAllTJ[strDMINKey] = objTJAndGBData
lstMarkers = ['o', 'v', 's']

arrAxes = np.array(
    [np.array([0, 0, 1]), np.array([1, 0, 1]), np.array([1, 1, 1])])
lstAxisNames = ['Axis [001]', 'Axis [101]', 'Axis [111]']
#%%

# %%
# TJ std (or change to mean) for against disorientation angle
lstAngles = []
lstStd = []
for a in dctAllTJ.keys():
    i = np.where(np.all(dctAllGB[a].GetAxis() == arrAxes, axis=1))[0][0]
    arrTJ = dctAllTJ[a].GetTJExcessPerLength()
    arrPositions = dctAllTJ[a].GetMinimumTJForEachDMin()
    #fltStd = np.mean(arrTJ[arrPositions])
    fltStd = np.std(arrTJ)
    objCSL = gl.SigmaCell(dctAllTJ[a].GetAxis(), ld.FCCCell)
    objCSL.MakeCSLCell(dctAllTJ[a].GetSigma())
    fltAngle = 180*objCSL.GetLatticeRotation()/np.pi
    if fltAngle < 40:
        lstAngles.append(fltAngle)
        lstStd.append(fltStd)
        plt.scatter(fltAngle, fltStd,
                    color=lstColours[i], marker=lstMarkers[i])
        plt.annotate(
            '$\Sigma$' + str(dctAllTJ[a].GetSigma()), (fltAngle, fltStd))
pop, popt = curve_fit(FitLine, lstAngles, lstStd)
plt.plot(lstAngles, FitLine(np.array(lstAngles), pop[0], pop[1]))
print(np.corrcoef(lstAngles, lstStd))
plt.show()
# %%
# TJ energy gradient
fig, axs = plt.subplots(1, 3, sharey=True)
lstValues = []
lstAllValues = []
for a in dctAllTJ.keys():
    i = np.where(np.all(dctAllGB[a].GetAxis() == arrAxes, axis=1))[0][0]
    lstValues = dctAllTJ[a].GetTJEnergyGradient(4.05)
    arrRows = np.where(np.array(lstValues) < 0.3)[0]
    arrValues = np.array(lstValues)[arrRows]
    lstAllValues.append(arrValues)
    arrSigma = np.ones(len(arrValues)) * \
        lstSigmas[i].index(dctAllTJ[a].GetSigma())
    axs[i].scatter(arrSigma, arrValues, c=lstColours[i],
                   marker=lstMarkers[i], label='Small')
    axs[i].errorbar(np.mean(arrSigma)-0.25, np.mean(arrValues), 1.96 *
                    np.std(arrValues), c=lstColours[i], linestyle='', capsize=5, marker='+')
for i in range(3):
    axs[i].set_xticks(list(range(len(lstSigmas[i]))))
    axs[i].set_xticklabels(lstSigmas[i])
    axs[i].set_xlabel(strSigmaAxis)
    axs[i].legend([lstLegendAxes[i]])
axs[0].set_ylabel(strFAxis)
plt.show()

# for a in dctAllTJ.keys():
#     i = np.where(np.all(dctAllTJ[a].GetAxis() == arrAxes, axis=1))[0][0]
#     if i == intChoice:
#         lstValues= dctAllTJ[a].GetTJEnergyGradient(4.05)
#         arrRows = mf.LogNormalConfidenceInterval(lstValues,0.95)
#         arrValues = np.array(lstValues)[arrRows]
#         lstAllValues.append(arrValues)
#         if len(lstValues) > 0:
#             plt.scatter(dctAllTJ[a].GetSigma()*np.ones(len(arrValues)),arrValues, c=lstColours[i])
#             plt.xticks(lstSigmas[i])
#             #
#             # plt.scatter(dctAllTJ[a].GetSigma(),np.median(lstValues), c=lstColours[i])
# arrAllValues = np.concatenate(lstAllValues)
# #arrMaxValues = np.concatenate(lstMax)
# plt.show()
# plt.hist(arrAllValues, bins=20, color=lstColours[intChoice])
# # plt.scatter(*tuple(zip(*arrD)))
# plt.show()
# print(np.mean(arrAllValues),np.std(arrAllValues))

# %%
# TJ energy differences by delta
lstAllValues = []
lstMax = []
intChoice = 0
for a in dctAllTJ.keys():
    i = np.where(np.all(dctAllGB[a].GetAxis() == arrAxes, axis=1))[0][0]
    if i >= intChoice:
        arrD = dctAllTJ[a].GetDisplacements()[:, 1:]
        dctAllTJ[a].GetTJEnergyGradient(4.05)
        arrByDelta = dctAllTJ[a].GetTJForEachDelta()
        lstAllValues.append(np.concatenate(
            arrByDelta, axis=0))
        lstMax.append(
            np.array(list(map(lambda x: np.min(x)-np.max(x), arrByDelta))))
arrAllValues = np.concatenate(lstAllValues)
arrMaxValues = np.concatenate(lstMax)
plt.hist(arrAllValues, bins=15, color=lstColours[i])
# plt.scatter(*tuple(zip(*arrD)))
plt.show()
plt.hist(arrMaxValues, bins=15, color=lstColours[i])
# plt.scatter(*tuple(zip(*arrD)))
plt.show()

arrRows = mf.ConfidenceInterval(arrMaxValues, 0.95)
print(np.max(arrMaxValues[arrRows]), np.min(arrMaxValues[arrRows]))
# %%
# comparison of standard deviation by delta translation and dmin
lstAllDelta = []
lstAllDMin = []
intChoice = 0
for a in dctAllTJ.keys():
    i = np.where(np.all(dctAllGB[a].GetAxis() == arrAxes, axis=1))[0][0]
    if i >= intChoice:
        lstDelta = dctAllTJ[a].GetTJForEachDelta()
        lstDMin = dctAllTJ[a].GetTJForEachDMin()
        lstTemp = []
        for j in lstDelta:
            if len(j) > 1:
                lstTemp.append(np.std(j))
        fltDelta = np.mean(lstTemp)
        lstAllDelta.append(fltDelta)
        lstTemp = []
        for k in lstDMin:
            if len(k) > 1:
                lstTemp.append(np.std(k))
        fltDMin = np.mean(lstTemp)
        lstAllDMin.append(fltDMin)
        plt.scatter(fltDelta, fltDMin,
                    color=lstColours[i], marker=lstMarkers[i])
        plt.annotate(
            '$\Sigma$' + str(dctAllTJ[a].GetSigma()), (fltDelta, fltDMin))

#plt.scatter(lstAllDMin, lstAllDelta)
plt.xlabel('delta std')
plt.ylabel('dmin std')
plt.axis('square')
plt.xticks(np.linspace(0.02, 0.1, 9))
plt.yticks(np.linspace(0.02, 0.1, 9))
plt.show()
#%%
##Eich calcuation
lstValues = []
arrTJ = dctAllTJ['Axis001,5'].GetTJExcessPerLength()
arrPos = dctAllTJ['Axis001,5'].GetMinimumTJForEachDMin()
lstValues.append(arrTJ[arrPos])
arrTJ = dctAllTJ['Axis001,13'].GetTJExcessPerLength()
arrPos = dctAllTJ['Axis001,13'].GetMinimumTJForEachDMin()
lstValues.append(arrTJ[arrPos])
arrTJ = dctAllTJ['Axis001,17'].GetTJExcessPerLength()
arrPos = dctAllTJ['Axis001,17'].GetMinimumTJForEachDMin()
lstValues.append(arrTJ[arrPos])
arrValues = np.concatenate(lstValues)
print(np.mean(arrValues), np.std(arrValues))
#%%
for a in dctAllTJ.keys():
        if np.all(dctAllTJ[a].GetAxis() == arrAxes[0]):
            arrTJ = dctAllTJ[a].GetTJExcessPerLength()
            print(np.mean(arrTJ),np.std(arrTJ),dctAllTJ[a].GetSigma())
# %%
# excess TJ energy against difference in merged atoms from SGB to STJ
for a in dctAllTJ.keys():
    arrTJ = dctAllTJ[a].GetTJExcessPerLength()
    arrValues = dctAllTJ[a].GetValues()
    lstRows = dctAllTJ[a].GetAtomMergeDifferences()
    lstlegend = []
    if len(lstRows) > 0:
        for k in lstRows:
            arrD = arrValues[k[1]] - arrValues[k[0]]
            arrD = arrD[:,6] - arrD[:,7]
            print(np.mean(abs(arrD)),np.std(arrD))
            lstlegend.append([np.unique(arrValues[k[1],1])[0],np.unique(arrValues[k[0],1])[0]])
            plt.title(str(dctAllTJ[a].GetSigma()))
            plt.scatter(arrD, arrTJ[k[1]]-arrTJ[k[0]])
        plt.legend(lstlegend)
        plt.show()
# %%
# TJ excess energy against atom merge differences SGB to STJ on one scatter plot
lstTJs = []
lstNs = []
for a in dctAllTJ.keys():
    arrTJ = dctAllTJ[a].GetTJExcessPerLength()
    lstGB, lstTJ, lstPos1, lstPos2 = dctAllTJ[a].GetAtomMergeDifferences()
    if len(lstPos1) > 0:
        arrD = np.array(lstGB)-np.array(lstTJ)
        lstNs.append(arrD)
        lstTJs.append(arrTJ[np.array(lstPos2)]-arrTJ[np.array(lstPos1)])
        # plt.title(str(dctAllTJ[a].GetSigma()))
arrTJs = np.concatenate(lstTJs)
arrNs = np.concatenate(lstNs)
plt.scatter(arrNs, arrTJs)
plt.show()
# %%
# original atom merge check
for a in dctAllTJ.keys():
    arr, arrDMin, arrC = dctAllTJ[a].GetAtomMergeDifferences()
    for k in range(len(arrDMin)):
        plt.title(str(dctAllTJ[a].GetSigma()) + ',' + str(arrDMin[k]))
        intRange = np.max(arr[k])-np.min(arr[k])
        intRange = np.max([1, intRange]).astype('int')
        plt.hist(arr[k], bins=intRange)
        plt.show()
        print(np.mean(arr[k]))


# %%
# CSL grain boundaries group together with one scatter plot for each axis and split by sigma value
fig, axs = plt.subplots(1, 3, sharey=True)
#fig.suptitle('Vertically stacked subplots')


for a in dctAllGB.keys():
    i = np.where(np.all(dctAllGB[a].GetAxis() == arrAxes, axis=1))[0][0]
    arrDMin, arrGB = dctAllGB[a].GetCSLExcessByDMin(dctDMin[a])
    #arrSigma = dctAllGB[a].GetSigmaArrays(lstSigmas[i])
    arrSigma = np.ones(len(arrGB)) * \
        lstSigmas[i].index(dctAllGB[a].GetSigmaValue())
    axs[i].scatter(arrSigma, arrGB, c=lstColours[i],
                   marker=lstMarkers[i], label='Small')

for i in range(3):
    axs[i].set_xticks(list(range(len(lstSigmas[i]))))
    axs[i].set_xticklabels(lstSigmas[i])
    axs[i].set_xlabel(strSigmaAxis)
    axs[i].legend([lstLegendAxes[i]])
axs[0].set_ylabel(strCSLAxis)
axs[0].set_ylim([0, 0.06])
plt.show()
# %%
# excess cylindrical GB energies with a scatter plot for each axis
fig, axs = plt.subplots(1, 3, sharey=True)
lstTJ = []
for a in dctAllTJ.keys():
    i = np.where(np.all(dctAllTJ[a].GetAxis() == arrAxes, axis=1))[0][0]
    arrGB = dctAllTJ[a].GetCylindricalExcessPerArea(dctAllGB[a])
    arrSigma = dctAllTJ[a].GetSigmaArrays(lstSigmas[i])
    lstTJ.append(arrGB)
    axs[i].scatter(arrSigma, arrGB, c=lstColours[i],
                   marker=lstMarkers[i], label='Small')
    axs[i].errorbar(np.mean(arrSigma)-0.25, np.mean(arrGB), 1.96 *
                    np.std(arrGB), c=lstColours[i], linestyle='', capsize=5, marker='+')
for i in range(3):
    axs[i].set_xticks(list(range(len(lstSigmas[i]))))
    axs[i].set_xticklabels(lstSigmas[i])
    axs[i].legend([lstAxes[i]], loc='lower left')
    axs[i].set_xlabel(strSigmaAxis)
axs[0].set_ylabel(strCurved)
fig.tight_layout()
plt.show()
arrTJ = np.concatenate(lstTJ, axis=0)
print(len(np.where(arrTJ > 0)[0]), len(arrTJ))
# %%
# excess mean GB energies with a scatter plot for each axis
fig, axs = plt.subplots(1, 3, sharey=True)
lstTJ = []
for a in dctAllTJ.keys():
    i = np.where(np.all(dctAllTJ[a].GetAxis() == arrAxes, axis=1))[0][0]
    arrGB = dctAllTJ[a].GetMeanGB(dctAllGB[a])
    arrSigma = dctAllTJ[a].GetSigmaArrays(lstSigmas[i])
    lstTJ.append(arrGB)
    axs[i].scatter(arrSigma, arrGB, c=lstColours[i],
                   marker=lstMarkers[i], label='Small')
    axs[i].errorbar(np.mean(arrSigma)-0.25, np.mean(arrGB), 1.96 *
                    np.std(arrGB), c=lstColours[i], linestyle='', capsize=5, marker='+')
for i in range(3):
    axs[i].set_xticks(list(range(len(lstSigmas[i]))))
    axs[i].set_xticklabels(lstSigmas[i])
    axs[i].legend([lstAxes[i]], loc='lower left')
    axs[i].set_xlabel(strSigmaAxis)
axs[0].set_ylabel(strGBAxis)
axs[0].set_ylim([0, 0.2])
axs[0].set_yticks([0.0, 0.05, 0.1, 0.15, 0.2])
fig.tight_layout()
plt.show()
arrTJ = np.concatenate(lstTJ, axis=0)
print(len(np.where(arrTJ > 0)[0]), len(arrTJ))

# %%
# excess TJ energies with a scatter plot for each axis
fig, axs = plt.subplots(1, 3, sharey=True)
lstTJ = []
for a in dctAllTJ.keys():
    i = np.where(np.all(dctAllTJ[a].GetAxis() == arrAxes, axis=1))[0][0]
    arrTJ = dctAllTJ[a].GetTJExcessPerLength()
    arrSigma = dctAllTJ[a].GetSigmaArrays(lstSigmas[i])
    lstTJ.append(arrTJ)
    axs[i].scatter(arrSigma, arrTJ, c=lstColours[i],
                   marker=lstMarkers[i], label='Small')
    axs[i].errorbar(np.mean(arrSigma)-0.25, np.mean(arrTJ), 1.96 *
                    np.std(arrTJ), c=lstColours[i], linestyle='', capsize=5, marker='+')
for i in range(3):
    axs[i].set_xticks(list(range(len(lstSigmas[i]))))
    axs[i].set_xticklabels(lstSigmas[i])
    axs[i].legend([lstAxes[i]], loc='upper left')
    axs[i].set_xlabel(strSigmaAxis)
    axs[i].axhline(y=0, c='black', linestyle='--')
axs[0].set_ylabel(strTJAxis)
fig.tight_layout()
plt.show()
arrTJ = np.concatenate(lstTJ, axis=0)
print(len(np.where(arrTJ > 0)[0]), len(arrTJ))
# %%
# TJ energies split by delta
lstTJ = []
axsI = 0
lstWidths = []
intAxis = 2
for a in dctAllTJ.keys():
    i = np.where(np.all(dctAllTJ[a].GetAxis() == arrAxes, axis=1))[0][0]
lstWidths = [10, 10, 10, 10, 10]
fig, axs = plt.subplots(
    1, 5, gridspec_kw={'width_ratios': lstWidths}, sharey=True)
for a in dctAllTJ.keys():
    i = np.where(np.all(dctAllTJ[a].GetAxis() == arrAxes, axis=1))[0][0]
    if i == intAxis:
        arrTJ = dctAllTJ[a].GetTJForEachDelta()
        dCount = 1
        for x in arrTJ:
            axs[axsI].scatter(dCount*np.ones(len(x)), x,
                              c=lstColours[i], marker=lstMarkers[i], s=16)
            axs[axsI].plot(dCount*np.ones(len(x)), x,
                           c=lstColours[i])
            axs[axsI].set_xticks(list(range(11)))
            axs[axsI].set_xticklabels('')
            # axs[axsI].xaxis.set_major_locator(plt.ticker.MultipleLocator(5))
            #axs[axsI].axhline(y=0, c='black', linestyle='--')
            dCount += 1
        #axs[axsI].annotate('$\Sigma$' +str(dctAllTJ[a].GetSigma()), ((dCount-1)/2,0.1))
        axs[axsI].set_title('$\Sigma$' + str(dctAllTJ[a].GetSigma()))
        axs[axsI].set_xlabel(strDeltaAxis)
        axsI += 1
axs[0].set_ylabel(strTJAxis)
#plt.ylim([np.min(arrTJ)-0.06,np.max(arrTJ) +0.06])
plt.tight_layout()
plt.show()
#print(len(np.where(arrTJ > 0)[0]), len(arrTJ))

# %%
# excess TJ split by sigma and dmin for one axis at a time
lstTJ = []
axsI = 0
lstWidths = []
intAxis = 0
for a in dctAllTJ.keys():
    i = np.where(np.all(dctAllTJ[a].GetAxis() == arrAxes, axis=1))[0][0]
    if i == intAxis:
        lstDMins, lstDValue = dctAllTJ[a].GetPositionsByDMin()
        lstWidths.append(len(lstDValue))
print(lstWidths)
fig, axs = plt.subplots(
    1, 5, gridspec_kw={'width_ratios': lstWidths}, sharey=True)
for a in dctAllTJ.keys():
    i = np.where(np.all(dctAllTJ[a].GetAxis() == arrAxes, axis=1))[0][0]
    if i == intAxis:
        arrTJ = dctAllTJ[a].GetTJExcessPerLength()
        arrSigma = dctAllTJ[a].GetSigmaArrays(lstSigmas[i])
        lstDMins, lstDValue = dctAllTJ[a].GetPositionsByDMin()
        lstTJ.append(arrTJ)
        dCount = 0
        lstMins = []
        for x in range(len(lstDMins)):
            d = lstDMins[x]
            strLabel = '.' + str(lstDValue[x])
            axs[axsI].scatter(dCount*np.ones(len(d)), arrTJ[d],
                              c=lstColours[i], marker=lstMarkers[i], label='Small')

            axs[axsI].set_xticks(list(range(len(lstDValue))))
            axs[axsI].set_xticklabels(lstDValue)
            # axs[axsI].xaxis.set_major_locator(plt.ticker.MultipleLocator(5))
            axs[axsI].axhline(y=0, c='black', linestyle='--')
            dCount += 1
            lstMins.append(np.min(arrTJ[d]))
        lstPositions2, lstDMin2 = dctAllTJ[a].GetPositionsByDelta()
        # for p in range(len(lstPositions2)):
        #      axs[axsI].plot(lstDMin2[p], arrTJ[lstPositions2[p]],linestyle=':', c= lstColours[i])
        # axs[axsI].annotate('$\Sigma$' +str(dctAllTJ[a].GetSigma()), ((dCount-1)/2,0.1))
        axs[axsI].axhline(y=np.median(lstMins), c='black', linestyle=':')
        axs[axsI].set_title('$\Sigma$' + str(dctAllTJ[a].GetSigma()))
        axs[axsI].set_xlabel(strDMinAxis)
        axsI += 1
arrTJ = np.concatenate(lstTJ, axis=0)
#plt.legend([lstAxes[i]],loc = 'upper left')
axs[0].set_ylabel(strTJAxis)
#plt.ylim([np.min(arrTJ)-0.06,np.max(arrTJ) +0.06])
plt.tight_layout()
plt.show()
print(len(np.where(arrTJ > 0)[0]), len(arrTJ))
# %%
lstTJs = []
for a in dctAllTJ.keys():
    if np.all(dctAllTJ[a].GetAxis() == arrAxes[0]):
        if dctAllTJ[a].GetSigma() != 7:
            lstTJs.append(dctAllTJ[a].GetTJExcessPerLength())
arrTJs = np.concatenate(lstTJs)
print(np.mean(arrTJs), np.std(arrTJs))
# %%
# CSL grain boundaries all metastable states
#lstHLines = []
#lstXValues = []
#xstart = 0
axsI = 0
lstWidths = []
intAxis = 0
for a in dctAllGB.keys():
    i = np.where(np.all(dctAllGB[a].GetAxis() == arrAxes, axis=1))[0][0]
    if i == intAxis:
        lstWidths.append(len(dctAllGB[a].GetDMinValues(dctDMin[a])))
print(lstWidths)
fig, axs = plt.subplots(
    1, 5, gridspec_kw={'width_ratios': lstWidths}, sharey=True)
for a in dctAllGB.keys():
    i = np.where(np.all(dctAllGB[a].GetAxis() == arrAxes, axis=1))[0][0]
    if i == intAxis:
        arrGB = dctAllGB[a].GetCSLExcessPerArea()
        arrDMins = dctAllGB[a].GetDMinValues().astype('int')
        arrD = list(range(len(arrDMins)))
        axs[axsI].scatter(arrD, arrGB, c=lstColours[i],
                          marker=lstMarkers[i], label='Small')
        axs[axsI].set_xticks(arrD)
        axs[axsI].set_xticklabels(arrDMins.tolist())
        # axs[axsI].axhline(y=0,c='black',linestyle='--')
        axs[axsI].set_title('$\Sigma$' + str(dctAllTJ[a].GetSigma()))
        axs[axsI].set_xlabel(strDMinAxis)
        axs[axsI].set_ylim([0, 0.06])
        axsI += 1
axs[0].set_ylabel(strGBAxis)
plt.tight_layout()
plt.show()
# %%
# CSL grain boundary excess energy only valid dmins
axsI = 0
lstWidths = []
intAxis = 0
for a in dctAllGB.keys():
    i = np.where(np.all(dctAllGB[a].GetAxis() == arrAxes, axis=1))[0][0]
    if i == intAxis:
        intLength = len(dctAllGB[a].GetCSLExcessByDMin(dctDMin[a])[0])
        lstWidths.append(intLength)
print(lstWidths)
fig, axs = plt.subplots(
    1, 5, gridspec_kw={'width_ratios': lstWidths}, sharey=True)
for a in dctAllGB.keys():
    i = np.where(np.all(dctAllGB[a].GetAxis() == arrAxes, axis=1))[0][0]
    if i == intAxis:
        arrDMins, arrGB = dctAllGB[a].GetCSLExcessByDMin(dctDMin[a])
        arrDMins = arrDMins.astype('int')
        arrD = list(range(len(arrDMins)))
        axs[axsI].scatter(arrD, arrGB, c=lstColours[i],
                          marker=lstMarkers[i], label='Small')
        axs[axsI].set_xticks(arrD)
        axs[axsI].set_xticklabels(arrDMins.tolist())
        # axs[axsI].axhline(y=0,c='black',linestyle='--')
        axs[axsI].set_title('$\Sigma$' + str(dctAllTJ[a].GetSigma()))
        axs[axsI].set_xlabel(strDMinAxis)
        axs[axsI].set_ylim([0, 0.05])
        axsI += 1
axs[0].set_ylabel(strCSLAxis)
plt.tight_layout()
plt.show()
# %%
lstTJ = []
lstHLines = []
lstXValues = []
xstart = 0
intAxis = 2
for a in dctAllTJ.keys():
    i = np.where(np.all(dctAllTJ[a].GetAxis() == arrAxes, axis=1))[0][0]
    if i == intAxis:
        arrGB = dctAllTJ[a].GetTJExcessPerLength()
        lstDMins, lstDValue = dctAllTJ[a].GetPositionsByDMin()
        lstHLines.append(len(lstDValue))
        lstXValues.extend(lstDValue)
        lstTJ.append(arrTJ)
        for x in range(len(lstDMins)):
            d = lstDMins[x]
            strLabel = '.' + str(lstDValue[x])
            plt.scatter(xstart*np.ones(len(d)),
                        arrTJ[d], c=lstColours[i], marker=lstMarkers[i], label='Small')
            xstart += 1
        plt.annotate(
            '$\Sigma$' + str(dctAllTJ[a].GetSigma()), (xstart-(lstHLines[-1]+1)/2, 0.08))

arrTJ = np.concatenate(lstTJ, axis=0)
plt.legend([lstAxes[i]], loc='upper left')
arrHLines = np.array(lstHLines)
for l in range(len(lstHLines)):
    plt.axvline(x=np.sum(arrHLines[:l]), c='black', linestyle='--')
plt.xticks(list(range(len(lstXValues))), lstXValues)
plt.xlabel(strDMinAxis)
plt.axhline(y=0, c='black', linestyle='--')
axs[0].set_ylabel(strTJAxis)
plt.ylim([np.min(arrTJ)-0.06, np.max(arrTJ) + 0.06])
plt.tight_layout()
plt.show()
print(len(np.where(arrTJ > 0)[0]), len(arrTJ))
# %%
fig, axs = plt.subplots(1, 3, sharey=True)

for a in dctAllTJ.keys():
    i = np.where(np.all(dctAllTJ[a].GetAxis() == arrAxes, axis=1))[0][0]
    arrTJ = dctAllTJ[a].GetTJExcessPerLength()
    axs[i].hist(arrTJ, color=lstColours[i], bins=np.linspace(-0.4,
                                                             0.2, 24), density=False, stacked=True)
    axs[i].legend([lstAxes[i]])
    axs[i].set_xlabel(strTJAxis)
    axs[i].set_xlim([-0.4, 0.2])
    axs[i].set_xticks([-0.4, -0.2, 0, 0.2])
fig.tight_layout()
plt.show()
# %%
lst001 = []
lst101 = []
lst111 = []
lstGB001 = []
lstGB101 = []
lstGB111 = []
for a in dctAllTJ.keys():
    i = np.where(np.all(dctAllTJ[a].GetAxis() == arrAxes, axis=1))[0][0]
    if i == 0:
        lst001.append(dctAllTJ[a].GetTJExcessPerLength())
        lstGB001.append(dctAllTJ[a].GetMeanGB(dctAllGB[a]))
    elif i == 1:
        lst101.append(dctAllTJ[a].GetTJExcessPerLength())
        lstGB101.append(dctAllTJ[a].GetMeanGB(dctAllGB[a]))
    elif i == 2:
        lst111.append(dctAllTJ[a].GetTJExcessPerLength())
        lstGB111.append(dctAllTJ[a].GetMeanGB(dctAllGB[a]))
    else:
        print('error i =' + str(i))
arr001 = np.concatenate(lst001)
arr101 = np.concatenate(lst101)
arr111 = np.concatenate(lst111)
arrGB001 = np.concatenate(lstGB001)
arrGB101 = np.concatenate(lstGB101)
arrGB111 = np.concatenate(lstGB111)


print('001', np.mean(arr001), np.std(arr001), len(arr001))
print('101', np.mean(arr101), np.std(arr101), len(arr101))
print('111', np.mean(arr111), np.std(arr111), len(arr111))
print('GB001', np.mean(arrGB001), np.std(arrGB001), len(arrGB001))
print('GB101', np.mean(arrGB101), np.std(arrGB101), len(arrGB101))
print('GB111', np.mean(arrGB111), np.std(arrGB111), len(arrGB111))

fig, axs = plt.subplots(1, 3, sharey=True)
lstValues = []
lstValues.append(arr001)
lstValues.append(arr101)
lstValues.append(arr111)
for i in range(3):
    arrTJ = lstValues[i]
    axs[i].hist(arrTJ, color=lstColours[i], bins=np.linspace(-0.4,
                                                             0.2, 18), density=False, stacked=True)
    axs[i].legend([lstAxisNames[i]])
    axs[i].set_xlabel(strTJAxis)
    axs[i].set_xlim([-0.4, 0.2])
    axs[i].set_xticks([-0.4, -0.2, 0, 0.2])
fig.tight_layout()
plt.show()


fig, axs = plt.subplots(1, 3, sharey=True)
lstGBValues = []
lstGBValues.append(arrGB001)
lstGBValues.append(arrGB101)
lstGBValues.append(arrGB111)
arrGBValues = np.concatenate(lstGBValues)
for i in range(3):
    arrGB = lstGBValues[i]
    axs[i].hist(arrGB, color=lstColours[i], bins=np.linspace(
        np.min(arrGBValues), np.max(arrGBValues), 15), density=False, stacked=True)
    axs[i].legend([lstAxisNames[i]])
    axs[i].set_xlabel(strGBAxis)
    axs[i].set_xlim([np.min(arrGBValues), np.max(arrGBValues)])
    #axs[i].set_xticks([-0.4, -0.2, 0, 0.2])
fig.tight_layout()
plt.show()


lstAllValues = []
lstAllValues.append(arr001)
lstAllValues.append(arr101)
lstAllValues.append(arr111)
arrAllValues = np.concatenate(lstAllValues)
print(np.mean(arrAllValues), np.std(arrAllValues))

plt.hist(arrAllValues, color='gray', bins=np.linspace(-0.4,
                                                      0.2, 24), density=False, stacked=True)
plt.xlabel(strTJAxis)
plt.xlim([-0.4, -0.2])
plt.xticks([-0.4, -0.3, -0.2, -0.1, 0, 0.1, 0.2])
plt.tight_layout()
plt.show()


# %%
for a in dctAllTJ.keys():
    arrTJValues = dctAllTJ[a].GetTJExcessPerLength()
# excess grain boundary
    arrPositions = np.argmin(arrTJValues)
    objCSL = dctAllGB[a]
    arrGBValues = dctAllTJ[a].GetMeanGB(objCSL)
    # plt.scatter(np.mean(arrGBValues),np.mean(arrTJValues))
    plt.scatter(arrGBValues[arrPositions], arrTJValues[arrPositions])
plt.show()
# %%

lstTJs = []
lstGBs = []
for a in dctAllTJ.keys():
    i = np.where(np.all(arrAxes == dctAllGB[a].GetAxis(), axis=1))[0][0]
    arrTJ, arrGB = dctAllTJ[a].GetExcessEnergies()
    arrPositions = dctAllTJ[a].GetMinimumTJForEachDMin()
    lstTJs.append(arrTJ)
    lstGBs.append(arrGB)
    plt.scatter(arrGB[arrPositions], dctAllTJ[a].GetTJExcessPerLength()[
                arrPositions], c=lstColours[i], marker=lstMarkers[i], label='Small')
plt.axhline(y=0, c='black', linestyle='--')
plt.legend(lstMarkers, lstLegendAxes)
plt.ylabel(strCSLAxis)
plt.xlabel(strSigmaAxis)
plt.tight_layout()
plt.show()
arrTJs = np.concatenate(lstTJs, axis=0)
arrGBs = np.concatenate(lstGBs, axis=0)
print(np.corrcoef(arrGBs, arrTJs))


# %%
lstTJ = []
lstGB = []
for a in dctAllTJ.keys():
    i = np.where(np.all(arrAxes == dctAllGB[a].GetAxis(), axis=1))[0][0]
    arrPositions = dctAllTJ[a].GetMinimumTJForEachDMin()
    lstGB.append(dctAllTJ[a].GetMeanGB(dctAllGB[a])[arrPositions])
    lstTJ.append(dctAllTJ[a].GetTJExcessPerLength()[arrPositions])
    plt.scatter(lstGB[-1], lstTJ[-1], c=lstColours[i],
                marker=lstMarkers[i], label='Small')
    plt.annotate(str(dctAllTJ[a].GetSigma()), (lstGB[-1], lstTJ[-1]))
print(np.corrcoef(lstGB, lstTJ))
pop, popt = optimize.curve_fit(FitLine, lstGB, lstTJ)
xrange = np.linspace(min(lstGB), max(lstGB), 100)
print(pop)
plt.plot(xrange, FitLine(xrange, pop[0], pop[1]), c='black')
plt.axhline(y=0, c='black', linestyle='--')
# plt.legend(lstMarkers,lstLegendAxes)
plt.ylabel(strCSLAxis)
plt.xlabel(strGBAxis)
# plt.xticks(list(range(len(lstAllSigma))),lstAllSigma)
plt.tight_layout()
plt.show()

# %%
lstTJ = []
lstGB = []
for a in dctAllTJ.keys():
    i = np.where(np.all(arrAxes == dctAllGB[a].GetAxis(), axis=1))[0][0]
    arrTJs = dctAllTJ[a].GetTJExcessPerLength()
    intPos = np.argmin(np.abs(arrTJs-np.mean(arrTJs)))
    lstGB.append(dctAllTJ[a].GetMeanGB(dctAllGB[a])[intPos])
    lstTJ.append(arrTJs[intPos])
    plt.scatter(lstGB[-1], lstTJ[-1], c=lstColours[i],
                marker=lstMarkers[i], label='Small')
    #plt.scatter(dctAllTJ[a].GetExcessEnergy()[arrPositions], dctAllTJ[a].GetTJExcessPerLength()[arrPositions], c=lstColours[i],marker =lstMarkers[i],label='Small')
    plt.annotate(str(dctAllTJ[a].GetSigma()), (lstGB[-1], lstTJ[-1]))
# print(np.corrcoef(lstGB,lstTJ))
plt.axhline(y=0, c='black', linestyle='--')
# plt.legend(lstMarkers,lstLegendAxes)
plt.ylabel(strTJAxis)
plt.xlabel(strNWGBAxis)
# plt.xticks(list(range(len(lstAllSigma))),lstAllSigma)
# plt.tight_layout()
plt.show()


# %%
lstAllTJ = []
lstAllGB = []
for a in dctAllTJ.keys():
    i = np.where(np.all(arrAxes == dctAllGB[a].GetAxis(), axis=1))[0][0]
    #arrPositions = np.argmin(dctAllTJ[a].GetTJExcessPerLength())
    arrPositions = dctAllTJ[a].GetMinimumTJForEachDMin()
    lstAllTJ.append(gf.FindMediod(
        dctAllTJ[a].GetTJExcessPerLength()[arrPositions]))
    #arrPositions = np.argmin(dctAllTJ[a].GetExcessEnergy())
    lstAllGB.append(gf.FindMediod(
        dctAllTJ[a].GetMeanGB(dctAllGB[a])[arrPositions]))
    plt.scatter(lstAllGB[-1], lstAllTJ[-1], c=lstColours[i],
                marker=lstMarkers[i], label='Small')
    plt.annotate(str(dctAllTJ[a].GetSigma()), (lstAllGB[-1], lstAllTJ[-1]))
#lstAllTJ = np.concatenate(lstAllTJ)
#lstAllGB = np.concatenate(lstAllGB)
print(np.corrcoef(lstAllTJ, lstAllGB))
print(np.mean(lstAllTJ), np.std(lstAllTJ))
pop, popt = optimize.curve_fit(FitLine, lstAllGB, lstAllTJ)
xrange = np.linspace(min(lstAllGB), max(lstAllGB), 100)
print(pop)
plt.plot(xrange, FitLine(xrange, pop[0], pop[1]), c='black')
# plt.axhline(y=0,c='black',linestyle='--')
# plt.legend(lstMarkers,lstLegendAxes)
plt.ylabel(strTJAxis)
plt.xlabel(strGBAxis)
# plt.xticks(list(range(len(lstAllSigma))),lstAllSigma)
plt.tight_layout()
plt.show()
# %%
lstAllTJ = []
lstAllGB = []
for a in dctAllTJ.keys():
    i = np.where(np.all(arrAxes == dctAllGB[a].GetAxis(), axis=1))[0][0]
    #arrPositions = np.argmin(dctAllTJ[a].GetTJExcessPerLength())
    arrPositions = dctAllTJ[a].GetMinimumTJForEachDMin()
    lstAllTJ.append(
        np.median(dctAllTJ[a].GetTJExcessPerLength()[arrPositions]))
    #arrPositions = np.argmin(dctAllTJ[a].GetExcessEnergy())
    lstAllGB.append(
        np.median(dctAllTJ[a].GetMeanGB(dctAllGB[a])[arrPositions]))
    plt.scatter(lstAllGB[-1], lstAllTJ[-1], c=lstColours[i],
                marker=lstMarkers[i], label='Small')
    plt.annotate(str(dctAllTJ[a].GetSigma()), (lstAllGB[-1], lstAllTJ[-1]))
#lstAllTJ = np.concatenate(lstAllTJ)
#lstAllGB = np.concatenate(lstAllGB)
print(np.corrcoef(lstAllTJ, lstAllGB))
print(np.mean(lstAllTJ), np.std(lstAllTJ))
pop, popt = optimize.curve_fit(FitLine, lstAllGB, lstAllTJ)
xrange = np.linspace(min(lstAllGB), max(lstAllGB), 100)
print(pop)
plt.plot(xrange, FitLine(xrange, pop[0], pop[1]), c='black')
# plt.axhline(y=0,c='black',linestyle='--')
# plt.legend(lstMarkers,lstLegendAxes)
plt.ylabel(strTJAxis)
plt.xlabel(strGBAxis)
# plt.xticks(list(range(len(lstAllSigma))),lstAllSigma)
plt.tight_layout()
plt.show()
# %%

lstAllTJ = []
lstAllGB = []
for a in dctAllTJ.keys():
    i = np.where(np.all(arrAxes == dctAllGB[a].GetAxis(), axis=1))[0][0]
    #arrPositions = np.argmin(dctAllTJ[a].GetTJExcessPerLength())
    arrAllTJs = dctAllTJ[a].GetTJExcessPerLength()
    arrTJ = dctAllTJ[a].GetTJForEachDelta()
    arrPositions = np.array(
        list(map(lambda x: np.where(np.min(x) == arrAllTJs)[0][0], arrTJ)))
    lstAllTJ.append(np.median(arrAllTJs[arrPositions]))
    #arrPositions = np.argmin(dctAllTJ[a].GetExcessEnergy())
    lstAllGB.append(
        np.median(dctAllTJ[a].GetMeanGB(dctAllGB[a])[arrPositions]))
    plt.scatter(lstAllGB[-1], lstAllTJ[-1], c=lstColours[i],
                marker=lstMarkers[i], label='Small')
    plt.annotate(str(dctAllTJ[a].GetSigma()), (lstAllGB[-1], lstAllTJ[-1]))
#lstAllTJ = np.concatenate(lstAllTJ)
#lstAllGB = np.concatenate(lstAllGB)
print(np.corrcoef(lstAllTJ, lstAllGB))
print(np.mean(lstAllTJ), np.std(lstAllTJ))
pop, popt = optimize.curve_fit(FitLine, lstAllGB, lstAllTJ)
xrange = np.linspace(min(lstAllGB), max(lstAllGB), 100)
print(pop)
plt.plot(xrange, FitLine(xrange, pop[0], pop[1]), c='black')
# plt.axhline(y=0,c='black',linestyle='--')
# plt.legend(lstMarkers,lstLegendAxes)
plt.ylabel(strTJAxis)
plt.xlabel(strGBAxis)
# plt.xticks(list(range(len(lstAllSigma))),lstAllSigma)
plt.tight_layout()
plt.show()

# %%
lstTJ = []
for a in dctAllTJ.keys():
    if np.all(dctAllTJ[a].GetAxis() == arrAxes[0]):
        lstTJ.append(np.max(dctAllTJ[a].GetTJExcessPerLength()))
        intMinPos = np.argmin(dctAllTJ[a].GetTJExcessPerLength())
        print(dctAllTJ[a].GetValues()[intMinPos])
print(np.mean(lstTJ), np.std(lstTJ))

# %%
lstGB = []
for a in dctAllGB.keys():
    lstGB.append(np.min(dctAllGB[a].GetCSLExcessPerArea()))
    intMinPos = np.argmin(dctAllGB[a].GetCSLExcessPerArea())
    print(dctAllGB[a].GetSigmaValue(), dctAllGB[a].GetValues()[intMinPos])
# %%
for a in dctAllTJ.keys():
    arrTJ = dctAllTJ[a].GetTJExcessPerLength()
    intMin = np.argmin(arrTJ)
    intMax = np.argmax(arrTJ)
    print(dctAllTJ[a].GetAxis(), dctAllTJ[a].GetSigma(), dctAllTJ[a].GetValues()[
          intMin, :2], dctAllTJ[a].GetValues()[intMax, :2])


# %%