import re
import numpy as np
import GeometryFunctions as gf
from scipy import spatial
from sklearn.cluster import AffinityPropagation

class LAMMPSData(object):
    def __init__(self,strFilename: str):
        self.__dctTimeSteps = dict()
        lstNumberOfAtoms = []
        lstTimeSteps = []
        lstColumnNames = []
        lstBoundaryType = []
        self.__Dimensions = 3 # assume 3d unless file shows the problem is 2d
        with open(strFilename) as Dfile:
            while True:
                lstBounds = []
                try:
                    line = next(Dfile).strip()
                except StopIteration as EndOfFile:
                    break
                if "ITEM: TIMESTEP" != line:
                    raise Exception("Unexpected "+repr(line))
                timestep = int(next(Dfile).strip())
                lstTimeSteps.append(timestep)
                line = next(Dfile).strip()
                if "ITEM: NUMBER OF ATOMS" != line:
                    raise Exception("Unexpected "+repr(line))
                N = int(next(Dfile).strip())
                lstNumberOfAtoms.append(N)
                line = next(Dfile).strip()
                if "ITEM: BOX BOUNDS" != line[0:16]:
                    raise Exception("Unexpected "+repr(line))
                lstBoundaryType = line[17:].strip().split()
                lstBounds.append(list(map(float, next(Dfile).strip().split())))
                lstBounds.append(list(map(float, next(Dfile).strip().split())))
                if len(lstBoundaryType)%3 == 0:
                    lstBounds.append(list(map(float, next(Dfile).strip().split())))
                else:
                    self.__Dimensions = 2
                line = next(Dfile).strip()
                if "ITEM: ATOMS id" != line[0:14]:
                    raise Exception("Unexpected "+repr(line))
                lstColumnNames = line[11:].strip().split()
                intNumberOfColumns = len(lstColumnNames)
                objTimeStep = LAMMPSTimeStep(timestep, N,intNumberOfColumns)
                objTimeStep.SetColumnNames(lstColumnNames)
                objTimeStep.SetBoundBoxLabels(lstBoundaryType)
                objTimeStep.SetBoundBoxDimensions(lstBounds)
                for i in range(N):
                    line = next(Dfile).strip().split()
                    objTimeStep.SetRow(i,list(map(float,line)))
                self.__dctTimeSteps[str(timestep)] = objTimeStep            
            self.__lstTimeSteps = lstTimeSteps
            self.__lstNumberOfAtoms = lstNumberOfAtoms
    def GetTimeSteps(self):
        return self.__lstTimeSteps
    def GetAtomNumbers(self):
        return self.__lstNumberOfAtoms
    def GetTimeStep(self, strTimeStep: str):
        return self.__dctTimeSteps[strTimeStep]
    def GetTimeStepByIndex(self, intIndex : int):
        return self.__dctTimeSteps[str(self.__lstTimeSteps[intIndex])]
    def GetNumberOfDimensions(self)-> int:
        return self.__Dimensions 
        
            
class LAMMPSTimeStep(object):
    def __init__(self,fltTimeStep: float,intNumberOfAtoms: int, intNumberOfColumns: int):
        self.__NumberOfAtoms = intNumberOfAtoms
        self.__NumberOfColumns = intNumberOfColumns
        self.__TimeStep = fltTimeStep
        self.__AtomData = np.zeros([intNumberOfAtoms,intNumberOfColumns])
        self.__ColumnNames = []
        self.__BoundingBoxLabel = []
        self.__BoundBoxDimensions = []
        self.__Dimensions = 3 #assume three dimensional unless specificed otherwise
    def SetRow(self, intRowNumber: int, lstRow: list):
        self.__AtomData[intRowNumber] = lstRow
    def GetRow(self,intRowNumber: int):
        return self.__AtomData[intRowNumber]
    def GetRows(self, lstOfRows: list):
        return self.__AtomData[lstOfRows]
    def GetAtomData(self):
        return self.__AtomData
    def SetColumnNames(self, lstColumnNames):
        self.__ColumnNames = lstColumnNames
    def GetColumnNames(self): 
        return self.__ColumnNames
    def GetColumnByIndex(self, intStructureIndex: int):
        return self.__AtomData[:,intStructureIndex]
    def GetColumnByName(self, strColumnName: str):
        if self.__ColumnNames != []:
            intStructureIndex = self.__ColumnNames.index(strColumnName)
            return self.GetColumnByIndex(intStructureIndex)
    def SetBoundBoxLabels(self, lstBoundBox: list):
        self.__BoundBoxLabels = lstBoundBox
        if lstBoundBox[0] == 'xy':
            self.__Cuboid = False
            self.__BoundaryTypes = lstBoundBox[self.__Dimensions:]
        else:
            self.__Cuboid = True
            self.__BoundaryTypes = lstBoundBox
    def GetBoundBoxLabels(self):
        return self.__BoundBoxLabels
    def SetBoundBoxDimensions(self, lstBoundBox):
        self.__BoundBoxDimensions = np.array(lstBoundBox)
        self.__Dimensions = len(lstBoundBox)
        arrCellVectors = np.zeros([self.__Dimensions, self.__Dimensions])
        lstOrigin = []
        for j in range(len(lstBoundBox)):
            lstOrigin.append(lstBoundBox[j][0])
            arrCellVectors[j,j] = lstBoundBox[j][1] - lstBoundBox[j][0]
        if len(lstBoundBox[0]) ==3: #then there are tiltfactors so include "xy" tilt
            arrCellVectors[1,0] = lstBoundBox[0][2]
            if self.__Dimensions == 3: #and there is also a z direction so include "xz" and "yz" tilts
                arrCellVectors[0,0] = arrCellVectors[0,0] -arrCellVectors[1,0] 
                arrCellVectors[2,0] = lstBoundBox[1][2]
                arrCellVectors[2,1] = lstBoundBox[2][2]
        self.__Origin = np.array(lstOrigin)
        self.__CellVectors  = arrCellVectors   
        self.__CellCentre = np.mean(arrCellVectors,axis=0)*self.__Dimensions/2+self.__Origin
        self.__CellBasis = np.zeros([self.__Dimensions,self.__Dimensions])
        for j, vctCell in enumerate(self.__CellVectors):
            self.__CellBasis[j] = vctCell 
        self.__BasisConversion = np.linalg.inv(self.__CellBasis)
    def GetBasisConversions(self):
        return self.__BasisConversion
    def GetCellBasis(self):
        return self.__CellBasis
    def GetNumberOfAtoms(self):
        return self.__NumberOfAtoms
    def GetNumberOfColumns(self):
        return self.__NumberOfColumns
    def GetCellVectors(self)->np.array:
        return self.__CellVectors
    def GetOrigin(self):
        return self.__Origin
    def GetNumberOfDimensions(self)->int:
        return self.__Dimensions
    def GetCellCentre(self):
        return self.__CellCentre
    def PeriodicEquivalents(self, inPositionVector: np.array)->np.array: #For POSITION vectors only for points within   
        arrVector = np.array([inPositionVector])                         #the simulation cell
        arrCellCoordinates = np.matmul(inPositionVector, self.__BasisConversion)
        for i,strBoundary in enumerate(self.__BoundaryTypes):
            if strBoundary == 'pp':
                 if  arrCellCoordinates[i] > 0.5:
                     arrVector = np.append(arrVector, np.subtract(arrVector,self.__CellVectors[i]),axis=0)
                 elif arrCellCoordinates[i] <= 0.5:
                     arrVector = np.append(arrVector, np.add(arrVector,self.__CellVectors[i]),axis=0)                  
        return arrVector
    def MoveToSimulationCell(self, inPositionVector: np.array)->np.array:
        return gf.WrapVectorIntoSimulationCell(self.__CellBasis, self.__BasisConversion, inPositionVector)
    def PeriodicShiftCloser(self, inFixedPoint: np.array, inPointToShift: np.array)->np.array:
        arrPeriodicVectors = self.PeriodicEquivalents(inPointToShift)
        fltDistances = list(map(np.linalg.norm, np.subtract(arrPeriodicVectors, inFixedPoint)))
        return arrPeriodicVectors[np.argmin(fltDistances)]
    def StandardiseOrientationData(self):
        self.__AtomData[:, [self.GetColumnNames().index('OrientationX'),self.GetColumnNames().index('OrientationY'),self.GetColumnNames().index('OrientationZ'), self.GetColumnNames().index('OrientationW')]]=np.apply_along_axis(gf.FCCQuaternionEquivalence,1,self.GetOrientationData()) 
    def GetOrientationData(self)->np.array:
        return (self.__AtomData[:, [self.GetColumnNames().index('OrientationX'),self.GetColumnNames().index('OrientationY'),self.GetColumnNames().index('OrientationZ'), self.GetColumnNames().index('OrientationW')]])  
    def GetData(self, inDimensions: np.array, lstOfColumns):
        return np.where(self.__AtomData[:,lstOfColumns])

class OVITOSPostProcess(object):
    def __init__(self,arrGrainQuaternions: np.array, objTimeStep: LAMMPSTimeStep, intLatticeType: int):
        self.__GrainOrientations = arrGrainQuaternions
        self.__NumberOfGrains = len(arrGrainQuaternions)
        self.__LAMMPSTimeStep = objTimeStep
        self.__Dimensions = objTimeStep.GetNumberOfDimensions()
        self.__LatticeStructure = intLatticeType #lattice structure type as defined by OVITOS
        self.__intStructureType = int(objTimeStep.GetColumnNames().index('StructureType'))
        self.__intPositionX = int(objTimeStep.GetColumnNames().index('x'))
        self.__intPositionY = int(objTimeStep.GetColumnNames().index('y'))
        self.__intPositionZ = int(objTimeStep.GetColumnNames().index('z'))
        self.__intQuarternionW = objTimeStep.GetColumnNames().index('OrientationW')
        self.__intQuarternionX = objTimeStep.GetColumnNames().index('OrientationX')
        self.__intQuarternionY = objTimeStep.GetColumnNames().index('OrientationY')
        self.__intQuarternionZ = objTimeStep.GetColumnNames().index('OrientationZ')
        lstOtherAtoms = list(np.where(objTimeStep.GetColumnByIndex(self.__intStructureType).astype('int') == 0)[0])
        lstLatticeAtoms =  list(np.where(objTimeStep.GetColumnByIndex(self.__intStructureType).astype('int') ==intLatticeType)[0])
        lstUnknownAtoms = list(np.where(np.isin(objTimeStep.GetColumnByIndex(self.__intStructureType).astype('int') ,[0,1],invert=True))[0])
        self.__LatticeAtoms = lstLatticeAtoms
        self.__NonLatticeAtoms = lstOtherAtoms + lstUnknownAtoms
        self.__OtherAtoms = lstOtherAtoms
        self.__NonLatticeTree =  spatial.KDTree(list(zip(*self.__PlotList(lstOtherAtoms+lstUnknownAtoms))))
        self.__LatticeTree = spatial.KDTree(list(zip(*self.__PlotList(lstLatticeAtoms))))
        self.__UnknownAtoms = lstUnknownAtoms
        self.__TripleLineAtoms = []
    def GetNonLatticeAtoms(self):
        return self.__LAMMPSTimeStep.GetRows(self.__NonLatticeAtoms)
    def GetUnknownAtoms(self):
        return self.__LAMMPSTimeStep.GetRows(self.__UnknownAtoms)   
    def GetOtherAtoms(self):
        return self.__LAMMPSTimeStep.GetRows(self.__OtherAtoms)
    def GetNumberOfNonLatticeAtoms(self):
        return len(self.__NonLatticeAtoms)
    def GetNumberOfOtherAtoms(self)->int:
        return len(self.__LAMMPSTimeStep.GetRows(self.__OtherAtoms))
    def PlotGrainAtoms(self, strGrainNumber: str):
        return self.__PlotList(self.__LatticeAtoms)
    def PlotUnknownAtoms(self):
        return self.__PlotList(self.__UnknownAtoms)
    def PlotGBAtoms(self):
        return self.__PlotList(self.__GBAtoms)
    def PlotTripleLineAtoms(self):
        return self.__PlotList(self.__TripleLineAtoms)
    def PlotDislocations(self):
        return self.__PlotList(self.__Dislocations)
    def PlotPoints(self, inArray: np.array)->np.array:
        return inArray[:,0],inArray[:,1], inArray[:,2]
    def __PlotList(self, strList: list):
        arrPoints = self.__LAMMPSTimeStep.GetRows(strList)
        return arrPoints[:,self.__intPositionX], arrPoints[:,self.__intPositionY], arrPoints[:,self.__intPositionZ]
    def __GetCoordinate(self, intIndex: int):
        arrPoint = self.__LAMMPSTimeStep.GetRow(intIndex)
        return arrPoint[self.__intPositionX:self.__intPositionZ+1]
    def __GetCoordinates(self, strList: list):
        arrPoints = self.__LAMMPSTimeStep.GetRows(strList)
        return arrPoints[:,self.__intPositionX:self.__intPositionZ+1]
    # def FindClosestGrainPoint(self, arrPoint: np.array,strGrainKey: str)->np.array:
    #     arrPeriodicPoints = self.__LAMMPSTimeStep.PeriodicEquivalents(arrPoint)
    #     fltDistances, intIndices =  self.__dctGrainPointsTree[strGrainKey].query(arrPeriodicPoints)
    #     intMin = np.argmin(fltDistances)
    #     intDataIndex = intIndices[intMin]
    #     return self.__dctGrainPointsTree[strGrainKey].data[intDataIndex]
    def GetNumberOfGBAtoms(self)->int:
        return len(self.__GBAtoms)
    def GetGBAtoms(self):
        return self.__LAMMPSTimeStep.GetRows(self.__GBAtoms)
    def MakePeriodicDistanceMatrix(self, inVector1: np.array, inVector2: np.array)->np.array:
        arrPeriodicDistance = np.zeros([len(inVector1), len(inVector2)])
        for j in range(len(inVector1)):
            for k in range(j,len(inVector2)):
                arrPeriodicDistance[j,k] = self.PeriodicMinimumDistance(inVector1[j],inVector2[k])
        return arrPeriodicDistance
    def PartitionTripleLines(self):
        arrTripleLineAtoms = self.__GetCoordinates(self.__TripleLineAtoms)
        arrDistanceMatrix = spatial.distance_matrix(arrTripleLineAtoms, arrTripleLineAtoms)
        setIndices = set(range(len(self.__TripleLineAtoms)))
        lstAllTripleLines = []
        while len(setIndices) > 0:            
            setReturnedIndices = self.TripleLineList(setIndices.pop(),arrDistanceMatrix)
            setIndices = setIndices.difference(setReturnedIndices)
            lstAllTripleLines.append([self.__TripleLineAtoms[i] for i in setReturnedIndices])
        self.__TripleLineGroups = lstAllTripleLines
    def GetNumberOfTripleLines(self)->int:
        return len(self.__TripleLineGroups)
    def PlotNthTripleLine(self, intIndex: int):
        return self.__PlotList(self.__TripleLineGroups[intIndex])
    def TripleLineList(self,inIndex: int, arrDistanceMatrix: np.array)->list:
        counter = 0
        setTripleLineIndices = set()
        setIndices = {inIndex}
        fltCurrentMean = 4.05
        while (setTripleLineIndices != setIndices) and  (counter < len(self.__TripleLineAtoms)):
            setIndices = setIndices.union(setTripleLineIndices)
            arrCurrentMatrix = arrDistanceMatrix[list(setIndices)]
            setTripleLineIndices = set(np.argwhere(arrCurrentMatrix < fltCurrentMean)[:,1])
            counter += 1
        return setIndices 
    def MergePeriodicTripleLines(self):
        lstMergedIndices = []
        lstRemainingTripleLines = self.__TripleLineGroups
        lstCurrentTripleLine = []
        counter = 0
        while (len(lstRemainingTripleLines)> 0):
            lstCurrentTripleLine = lstRemainingTripleLines[0]
            lstRemainingTripleLines.remove(lstCurrentTripleLine)
            while (counter < len(lstRemainingTripleLines)):
                lstTripleLine = lstRemainingTripleLines[counter]
                if self.CheckTripleLineEquivalence (lstCurrentTripleLine,lstTripleLine):
                    lstCurrentTripleLine.extend(lstTripleLine)
                    lstRemainingTripleLines.remove(lstTripleLine)
                else:
                    counter += 1
            if len(lstCurrentTripleLine) > 5:
                lstMergedIndices.append(lstCurrentTripleLine)
            else:
                self.__UnknownAtoms.extend(lstCurrentTripleLine)
            counter = 0
        self.__TripleLineGroups = lstMergedIndices
    def CheckTripleLineEquivalence(self,lstTripleLineOne, lstTripleLineTwo)->bool:
        blnFound = False
        counter = 0
        intLengthOne = len(lstTripleLineOne)
        intLengthTwo = len(lstTripleLineTwo)
        while not blnFound and counter < intLengthOne*intLengthTwo:
            i = lstTripleLineOne[np.mod(counter, intLengthOne)]
            j = lstTripleLineTwo[np.mod(counter - i, intLengthTwo)]
            if (self.PeriodicMinimumDistance(self.__GetCoordinate(i), self.__GetCoordinate(j)) < 2*4.05):
                blnFound = True
            counter += 1
        return blnFound
    def SortByAngles(self,inPoints: np.array, inStructure):#rotates around a point and counts the number of transitions from GB to grain
        intCount = 0 # pass an array of the form [xcoord, ycoord, Structure]
        fltOldValue = inStructure[0]
        arrValues = np.zeros([len(inStructure),2])
        arrValues[:,0] = np.arctan2(inPoints[:,1],inPoints[:,0])
        arrValues[:,1] = np.round(inStructure,0)
        arrValues = arrValues[arrValues[:,0].argsort()]
        for j in arrValues:
            fltNewValue = j[-1]
            if int(fltNewValue) != int(fltOldValue):
                intCount += 1
                fltOldValue = fltNewValue
        return intCount
    def PeriodicMinimumDistance(self, inVector1: np.array, inVector2: np.array)->float:
        arrVectorPeriodic = self.__LAMMPSTimeStep.PeriodicEquivalents(np.abs(inVector1-inVector2))
        return np.min(np.linalg.norm(arrVectorPeriodic, axis=1))
    def ClassifyNonGrainAtoms(self):
        lstUnknownAtoms = []
        lstTripleLines = []
        lstDislocations = []
        lstGBAtoms = []
        lstNonGrainAtoms = self.__OtherAtoms+ self.__UnknownAtoms
        for j in lstNonGrainAtoms:
            setRemainingIndices =set()
            lstPointsIndices = []
            lstPoints = []
            lstOfCurrentGrainIndices = []
            intGrains = 0
            arrGBAtom = self.__GetCoordinate(j)
            fltBoundaryLength = self.FindGrainBoundaryLength(arrGBAtom)
            arrPeriodicPositions = self.__LAMMPSTimeStep.PeriodicEquivalents(arrGBAtom)
            arrPeriodicTranslations = arrPeriodicPositions - arrGBAtom
            for intIndex,arrPoint in enumerate(arrPeriodicPositions): 
                lstPointsIndices= self.__LatticeTree.query_ball_point(arrPoint, 2*fltBoundaryLength)
                if len(lstPointsIndices) > 0:
                    lstPoints.extend(np.subtract(self.__LatticeTree.data[lstPointsIndices],arrPeriodicTranslations[intIndex]))
            if len(lstPoints) > 0 :
                arrPoints = np.array(lstPoints)
                setRemainingIndices = set(range(len(arrPoints)))
                arrDistanceMatrix = spatial.distance.cdist(arrPoints, arrPoints,'euclidean')
            while len(setRemainingIndices) > 0 and intGrains < 4:
                lstOfCurrentGrainIndices =  self.FindGrainGroups(1.02*4.05/np.sqrt(2), arrPoints,arrDistanceMatrix, setRemainingIndices.pop())
                setRemainingIndices = setRemainingIndices.difference(set(lstOfCurrentGrainIndices))
                if len(lstOfCurrentGrainIndices) > 0:
                    intGrains += 1
            if (intGrains ==1):
                lstDislocations.append(j)
            elif (intGrains ==2):
                lstGBAtoms.append(j)
            elif intGrains == 3:
                lstTripleLines.append(j)
            else:
                lstUnknownAtoms.append(j) 
        self.__Dislocations = lstDislocations          
        self.__GBAtoms = lstGBAtoms
        self.__TripleLineAtoms = lstTripleLines
        self.__UnknownAtoms = lstUnknownAtoms
    def FindGrainBoundaryLength(self, arrPoint: np.array): #finds a grain boundary estimate at a grain boundary atom
        lstPointsIndices = self.__NonLatticeTree.query_ball_point(arrPoint, 3*4.05)
        arrPoints = self.__NonLatticeTree.data[lstPointsIndices]
        arrMidPoint = np.mean(arrPoints,axis=0)
        fltBoundary = self.__LatticeTree.query(arrMidPoint, 1)[0]
        # arrPoints = arrPoints - np.array([arrMidPoint])
        # matCov = np.cov(arrPoints[:,0], arrPoints[:,1])
        # eValues, eVectors = np.linalg.eig(matCov)
        # vctMax = gf.NormaliseVector(eVectors[:,np.argmax(eValues)]) 
        # vctPer = np.array([vctMax[1], -vctMax[0],0])
        # arrDistances = np.matmul(arrPoints, vctPer)
        # fltBoundary = 2*np.max(np.abs(arrDistances))
        return 2*fltBoundary
    def FindGrainGroups(self,fltDistance: float, arrPoints: np.array, inDistanceMatrix: np.array, intStart: int)->list:
        lstCurrentRows = [intStart]
        lstAllUsedRows = []
        while (len(lstCurrentRows) > 0):
            lstCurrentRows = np.argwhere(np.any(inDistanceMatrix[lstCurrentRows] > 0, axis = 0) & np.any(inDistanceMatrix[lstCurrentRows]< fltDistance,axis=0))
            lstCurrentRows = list(set(lstCurrentRows[:,0]) -set(lstAllUsedRows))
            lstAllUsedRows.extend(lstCurrentRows)
        return lstAllUsedRows
    def GetMergedTripleLine(self, intIndex)->np.array:
        return self.__LAMMPSTimeStep.GetRows(self.__TripleLineGroups[intIndex])
            