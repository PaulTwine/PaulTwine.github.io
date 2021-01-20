import numpy as np
import GeometryFunctions as gf
#import LatticeShapes as ls
import LatticeDefinitions as ld
import scipy as sc
from sympy.parsing.sympy_parser import parse_expr
from sympy import lambdify
from sympy.abc import x,y,z
from datetime import datetime
import copy as cp
import warnings

class PureCell(object):
    def __init__(self,inCellNodes: np.array): 
        self.__CellNodes = inCellNodes
        self.__NumberOfCellNodes = len(inCellNodes)
        self.__Dimensions = len(inCellNodes[0])
    def UnitVector(self, intNumber: int)->np.array:
        arrVector = np.zeros(self.Dimensions())
        if intNumber >= 0:
            arrVector[intNumber] = 1
        else:
            arrVector[-intNumber] = -1
        return np.array(arrVector)
    def GetCellCentre(self)->np.array:
        return 0.5*np.ones(self.Dimensions())
    def GetCellNode(self, inIndex: int)->np.array:
        return self.__CellNodes[inIndex]
    def GetCellNodes(self)->np.array:
        return self.__CellNodes
    def GetNumberOfCellNodes(self):
        return self.__NumberOfCellNodes
    def Dimensions(self)->int:
        return self.__Dimensions
    def CellDirectionalMotif(self, intBasisVector: int, intSign = 1)->np.array:
        inBasisVector = self.UnitVector(intBasisVector)
        if intSign ==-1:
                inBasisVector = -1*inBasisVector
        lstDeletedIndices = []
        for i,arrNode in enumerate(self.GetCellNodes()):
            if np.dot(inBasisVector, np.subtract(arrNode, self.GetCellCentre())) < 0:
                lstDeletedIndices.append(i)
        arrMotif = np.delete(self.GetCellNodes(), lstDeletedIndices, axis=0)       
        return arrMotif
    def SnapToCellNode(self, inNodePoint: np.array)->np.array:
        if (np.max(inNodePoint) < 1.0 and np.min(inNodePoint) >= 0.0):
            arrDistances = np.zeros(self.GetNumberOfCellNodes())
            for j,arrNode in enumerate(self.__CellNodes):
                arrDistances[j] = gf.RealDistance(inNodePoint, arrNode)
            intMinIndex = np.argmin(arrDistances)
        else:
            raise Exception('Cell co-ordinates must range from 0 to 1 inclusive')
        return self.__CellNodes[intMinIndex] 

class RealCell(PureCell):
    def __init__(self,inCellNodes: np.array, inLatticeParameters: np.array, inCellVectors=None):
        PureCell.__init__(self, inCellNodes)
        self.__LatticeParameters = inLatticeParameters
        if inCellVectors is None:
            self.__CellVectors = gf.StandardBasisVectors(self.Dimensions())
        else:
            self.__CellVectors = inCellVectors
        self.__RealCellVectors = np.zeros([self.Dimensions(),self.Dimensions()])
        for j in range(self.Dimensions()):
            self.__RealCellVectors[j] = inLatticeParameters[j]*self.__CellVectors[j]
        arrDistanceMatrix = sc.spatial.distance_matrix(self.__RealCellVectors,self.__RealCellVectors)
        self.__NearestNeighbourDistance = np.min(arrDistanceMatrix[arrDistanceMatrix > 0])
    def GetCellVectors(self)->np.array:
        return self.__CellVectors
    def GetRealCellVectors(self)->np.array:
        return self.__RealCellVectors
    def GetLatticeParameters(self):
        return self.__LatticeParameters
    def GetNearestNeighbourDistance(self):
        return self.__NearestNeighbourDistance
    
class GeneralLattice(RealCell):
    def __init__(self,inBasisVectors:np.array,inCellNodes: np.array,inLatticeParameters:np.array,inOrigin: np.array,inCellBasis = None):
        RealCell.__init__(self, inCellNodes,inLatticeParameters, inCellBasis)
        self.__UnitBasisVectors  = inBasisVectors # Cartesian basis vectors for the lattice
        self.__RealPoints = []
        self.__LatticePoints = []
        self.__CellPoints = []
        self.__AtomType = 1
        self.__Origin = inOrigin
        self.__LatticeParameters = inLatticeParameters
        self.__RealBasisVectors = np.zeros([self.Dimensions(),self.Dimensions()])
        self.__LinearConstraints = []
        self.__ConstrainType = []
        for j in range(self.Dimensions()):
            self.__RealBasisVectors[j] = inLatticeParameters[j]*inBasisVectors[j]
        self.__intConstraintRound = 8 #default value for the rounding precision for points lying on a linear constraint
    def GetConstraintRounding(self):
        return self.__intConstraintRound
    def SetConstraintRounding(self, intValue: int):
        self.__intConstraintRound = intValue #take care to call MakeRealPoints() for this to take effect
    def GetUnitBasisVectors(self)->np.array:
        return self.__UnitBasisVectors
    def GetRealBasisVectors(self)->np.array:
        return self.__RealBasisVectors
    def RemovePoints(self, inRealPoints: np.array):
        arrCheck = (self.__RealPoints[:, None] == inRealPoints).all(-1).any(-1)
        lstIndices = list(arrCheck == True)
        self.__DeletePoints(lstIndices)
    def __DeletePoints(self,lstDeletedIndices: list):
        self.__RealPoints = np.delete(self.__RealPoints, lstDeletedIndices, axis=0)
        self.__LatticePoints  = np.delete(self.__LatticePoints, lstDeletedIndices, axis=0) 
    def GetRealPoints(self)->np.array:
        return self.__RealPoints
    def MakeRealPoints(self, inClosedConstraints: np.array):
        #assumes constraints are closed (e.g. includes boundary points) To change this call
        #SetOpenConstraints(arrPositions) and an array of which constraints are open
        self.__LinearConstraints = inClosedConstraints
        self.__ConstraintTypes = list(len(inClosedConstraints)*'c')
        self.GenerateLatticeConstraints(inClosedConstraints)
        arrBounds = self.FindBoxConstraints(self.__LatticeConstraints)
        arrBounds[:,0] = np.floor(arrBounds[:,0])
        arrBounds[:,1] = np.ceil(arrBounds[:,1])
        arrCellPoints = np.array(gf.CreateCuboidPoints(arrBounds))
        arrLatticePoints = self.MakeLatticePoints(arrCellPoints)
        arrLatticePoints = np.delete(arrLatticePoints, self.CheckLatticeConstraints(arrLatticePoints), axis = 0)
        self.GenerateRealPoints(arrLatticePoints)
    def MakeLatticePoints(self, inCellPoints):
        arrLatticePoints = np.empty([self.GetNumberOfCellNodes()*len(inCellPoints), self.Dimensions()])
        for i, position in enumerate(inCellPoints):
            for j, cell in enumerate(self.GetCellNodes()):
                arrLatticePoints[j+i*self.GetNumberOfCellNodes()] = np.add(position,cell)
        return np.unique(arrLatticePoints, axis = 0)
    def GenerateRealPoints(self, inLatticePoints):
        self.__LatticePoints = inLatticePoints
        arrRealPoints = np.round(np.matmul(inLatticePoints, self.GetRealCellVectors()),10)
        self.__RealPoints = np.round(np.matmul(arrRealPoints, self.GetUnitBasisVectors()),10)
        self.__RealPoints = np.add(self.__Origin, self.__RealPoints)
    def GenerateLatticeConstraints(self, inConstraints: np.array):
        rtnArray = np.zeros([len(inConstraints),len(inConstraints[0])])
        tmpArray = np.zeros([3])
        for i in range(len(inConstraints)):
            arrVector = inConstraints[i,:-1]
            fltLength = np.linalg.norm(arrVector)
            arrVector = arrVector/fltLength
            arrConstraint = inConstraints[i,3]*arrVector/fltLength**2
            arrVector = np.matmul(arrVector, np.linalg.inv(self.GetRealBasisVectors()))
            arrConstraint = np.matmul(arrConstraint, np.linalg.inv(self.GetRealBasisVectors()))
            for k in range(3):
                rtnArray[i,k] = np.dot(arrVector,self.GetCellVectors()[k]) # generally a non-Carteisan Basis
                tmpArray[k] = np.dot(arrConstraint, self.GetCellVectors()[k])
            fltLength = np.linalg.norm(rtnArray[i,:3])
            rtnArray[i,:3] = rtnArray[i,:3]/fltLength 
            rtnArray[i,3] = gf.InnerProduct(rtnArray[i,:3], tmpArray,np.linalg.inv(self.GetCellVectors()))
        self.__LatticeConstraints = rtnArray
    def CheckLinearConstraints(self,inPoints: np.array)-> np.array: #returns indices to delete for real coordinates  
        arrPositions = np.subtract(np.matmul(inPoints, np.transpose(self.__LinearConstraints[:,:-1])), np.transpose(self.__LinearConstraints[:,-1])) #if it fails any constraint then the point is put in the deleted list
        arrClosed = np.argwhere(np.round(arrPositions,self.__intConstraintRound) > 0)[:,0]                
        return np.unique(arrClosed)
    def CheckLatticeConstraints(self,inPoints: np.array)-> np.array: #returns indices to delete   
        arrPositions = np.subtract(np.matmul(inPoints, np.transpose(self.__LatticeConstraints[:,:-1])), np.transpose(self.__LatticeConstraints[:,-1]))
        arrClosed = np.argwhere(np.round(arrPositions,self.__intConstraintRound) > 0)[:,0]       
        return np.unique(arrClosed)
    def SetOpenConstraints(self, arrOpenConstraints: np.array, intRound = 5): #pass the linear constraint positions that are open
        arrPositions = np.subtract(np.matmul(self.__RealPoints, np.transpose(self.__LinearConstraints[arrOpenConstraints,:-1])), np.transpose(self.__LinearConstraints[arrOpenConstraints,-1]))
        arrOpen = np.argwhere(np.round(arrPositions,intRound) == 0)[:,0]   #makes the selected constraints open and removes points on the boundary
        for j in arrOpenConstraints: #update the linear constraint label types
            self.__ConstraintTypes[j] = 'o'    
        if np.size(arrOpen) > 0:
            self.__DeletePoints(arrOpen)
    def GetConstraintTypes(self):
        return self.__ConstraintTypes
    def GetNumberOfAtoms(self)->int:
        return len(self.__RealPoints)
    def GetAtomType(self)->int:
        return self.__AtomType
    def GetOrigin(self)->np.array:
        return self.__Origin
    def SetOrigin(self, inArray: np.array):
        self.__Origin = inArray
    def MatLabPlot(self):
        return zip(*self.GetRealPoints())
    def LinearConstrainRealPoints(self, inConstraint: np.array):
        lstDeletedIndices = gf.CheckLinearConstraint(self.__RealPoints, inConstraint)
        self.__DeletePoints(lstDeletedIndices)
    def RemovePlaneOfAtoms(self, inPlane: np.array):
        lstDeletedIndices = gf.CheckLinearEquality(self.__RealPoints, inPlane, 0.01)
        self.__DeletePoints(lstDeletedIndices)
    #FindBoxConstraint only works for linear constraints. Searches for all the vertices where three constraints #simultaneously apply and then finds the points furthest from the origin.
    def FindBoxConstraints(self,inConstraints: np.array, fltTolerance = 0.0001)->np.array:
        intLength = len(inConstraints)
        intCombinations = int(np.math.factorial(intLength)/(np.math.factorial(3)*np.math.factorial(intLength-3)))
        arrMatrix = np.zeros([3,4])
        arrPoints = np.zeros([intCombinations, 3])
        arrRanges = np.zeros([3,2])
        counter = 0
        for i in range(intLength):
            for j in range(i+1,intLength):
                for k in range(j+1,intLength):
                    arrMatrix[0] = inConstraints[i]
                    arrMatrix[1] = inConstraints[j]
                    arrMatrix[2] = inConstraints[k]
                    if abs(np.linalg.det(arrMatrix[:,:-1])) > fltTolerance:
                        arrPoints[counter] = np.matmul(np.linalg.inv(arrMatrix[:,:-1]),arrMatrix[:,-1])
                        counter += 1
                    else:
                        arrPoints = np.delete(arrPoints, counter, axis=0)
        for j in range(len(arrRanges)):
            arrRanges[j,0] = np.min(arrPoints[:,j])
            arrRanges[j,1] = np.max(arrPoints[:,j])
        return(arrRanges)
    def ApplyGeneralConstraint(self,strFunction, strVariables='[x,y,z]'): #default scalar value is less than or equal to 0 if "inside" the region
        lstVariables = parse_expr(strVariables)
        fltFunction = lambdify(lstVariables,parse_expr(strFunction))
        arrFunction = lambda X : fltFunction(X[0],X[1],X[2])
        arrLess = np.array(list(map(arrFunction, self.__RealPoints)))
        lstDeletedIndices = np.where(arrLess > 0)[0]
        self.__DeletePoints(lstDeletedIndices)
    def GetQuaternionOrientation(self)->np.array:
        return gf.FCCQuaternionEquivalence(gf.GetQuaternionFromBasisMatrix(np.transpose(self.GetUnitBasisVectors())))     
    def GetLinearConstraints(self):
        return self.__LinearConstraints
    def GetLatticeConstraints(self):
        return self.__LatticeConstraints
class ExtrudedRectangle(GeneralLattice):
    def __init__(self, fltLength: float, fltWidth: float, fltHeight: float, inBasisVectors: np.array, inCellNodes: np.array ,inLatticeParameters: np.array, inOrigin: np.array, inCellBasis= None):
        arrConstraints = np.zeros([6,4])
        arrConstraints[0] = np.array([1,0,0,fltLength])
        arrConstraints[1] = np.array([-1,0,0,0])
        arrConstraints[2] = np.array([0,1,0,fltWidth])
        arrConstraints[3] = np.array([0,-1,0,0])
        arrConstraints[4] = np.array([0,0,1,fltHeight])
        arrConstraints[5] = np.array([0,0,-1,0])
        GeneralLattice.__init__(self,inBasisVectors, inCellNodes, inLatticeParameters,inOrigin, inCellBasis)
        self.MakeRealPoints(arrConstraints)

class ExtrudedParalleogram(GeneralLattice):
    def __init__(self, arrLength: np.array, arrWidth: float, fltHeight: float, inBasisVectors: np.array, inCellNodes: np.array ,inLatticeParameters: np.array, inOrigin: np.array, inCellBasis= None):
        arrZ = np.array([0,0,1])
        arrConstraints = np.zeros([6,4])
        arrConstraints[0,:3] = gf.NormaliseVector(np.cross(arrLength, arrZ))
        arrConstraints[0,3] = 0
        arrConstraints[1,:3] = -gf.NormaliseVector(np.cross(arrLength, arrZ))
        arrConstraints[1,3] = np.linalg.norm(np.cross(arrLength,arrWidth)/np.linalg.norm(arrWidth))
        arrConstraints[2,:3] = -gf.NormaliseVector(np.cross(arrWidth, arrZ))
        arrConstraints[2,3] = 0
        arrConstraints[3,:3] = gf.NormaliseVector(np.cross(arrWidth, arrZ))
        arrConstraints[3,3] = np.linalg.norm(np.cross(arrLength,arrWidth)/np.linalg.norm(arrLength))
        arrConstraints[4,:3] = -arrZ
        arrConstraints[4,3] = 0
        arrConstraints[5,:3] = arrZ
        arrConstraints[5,3] = fltHeight
        GeneralLattice.__init__(self,inBasisVectors, inCellNodes, inLatticeParameters,inOrigin, inCellBasis)
        self.MakeRealPoints(arrConstraints)


class ExtrudedRegularPolygon(GeneralLattice):
    def __init__(self, fltSideLength: float, fltHeight: float, intNumberOfSides: int, inBasisVectors: np.array, inCellNodes: np.array, inLatticeParameters: np.array, inOrigin: np.array, inCellBasis=None):
        intDimensions = len(inBasisVectors[0])
        arrConstraints = np.zeros([intNumberOfSides + 2,intDimensions+1])
        arrNormalVector = np.zeros(intDimensions)
        arrSideVector = np.zeros(intDimensions)
        arrVerticalVector = np.zeros(intDimensions)
        arrNormalVector[1] = -1
        arrSideVector[0] = fltSideLength
        arrVerticalVector[-1] = 1
        fltAngle = 2*np.pi/intNumberOfSides
        arrNextPoint = np.zeros([intDimensions])
        for j in range(intNumberOfSides):
            arrNextPoint += arrSideVector
            for k in range(len(arrConstraints[0])-1):
                arrConstraints[j,k] = arrNormalVector[k]
            arrConstraints[j, -1] = np.dot(arrNormalVector, arrNextPoint)
            arrNormalVector = gf.RotateVector(arrNormalVector,arrVerticalVector, fltAngle)
            arrSideVector = gf.RotateVector(arrSideVector,arrVerticalVector, fltAngle)
        arrConstraints[-2,-2] = -1
        arrConstraints[-2,-1] = 0
        arrConstraints[-1,-2] = 1
        arrConstraints[-1,-1] = fltHeight
        GeneralLattice.__init__(self,inBasisVectors, inCellNodes, inLatticeParameters,inOrigin, inCellBasis)
        self.MakeRealPoints(arrConstraints)

class SimulationCell(object):
    def __init__(self, inBoxVectors: np.array):
        self.Dimensions = len(inBoxVectors[0])
        self.BoundaryTypes = ['p']*self.Dimensions #assume periodic boundary conditions as a default
        self.SetOrigin(np.zeros(self.Dimensions))
        self.dctGrains = dict() #dictionary of RealGrain objects which form the simulation cell
        self.SetParallelpipedVectors(inBoxVectors)
        self.blnPointsAreWrapped = False
        self.__FileHeader = ''
        self.GrainList = []
    def AddGrain(self,inGrain, strName = None):
        if strName is None:
            strName = str(len(self.dctGrains.keys())+1)
        self.dctGrains[strName] = inGrain
        self.GrainList = list(self.dctGrains.keys())
    def GetGrain(self, strName: str):
        return self.dctGrains[strName]
    def GetNumberOfGrains(self)->int:
        return len(self.GrainList)
    def GetTotalNumberOfAtoms(self):
        if self.blnPointsAreWrapped:
            intNumberOfAtoms = len(self.__UniqueRealPoints)
        else: 
            intNumberOfAtoms = 0
            for j in self.GrainList:
                intNumberOfAtoms += self.GetGrain(j).GetNumberOfAtoms()
        return intNumberOfAtoms
    def GetRealBasisVectors(self):
        return self.__BasisVectors
    def SetBoundaryTypes(self,inList: list): #boundaries can be periodic 'p' or fixed 'f'
        self.BoundaryTypes = inList    
    def GetNumberOfAtomTypes(self):
        lstAtomTypes = []
        for j in self.GrainList:
            intCurrentAtomType = self.GetGrain(j).GetAtomType()
            if intCurrentAtomType not in lstAtomTypes: 
                lstAtomTypes.append(intCurrentAtomType)
        return len(lstAtomTypes)
    def GetMinimumSimulationBox(self)->np.array:
        arrSize = self.GrainList[0].GetBoundingBox()
        for CurrentGrain in self.GrainList:
            arrCurrentBox = CurrentGrain.GetBoundingBox()
            for coordinate, arrDimensions in enumerate(arrCurrentBox):
                if arrDimensions[0] < arrSize[coordinate][0]:
                    arrSize[coordinate][0] = arrDimensions[0]
                if arrDimensions[1] > arrSize[coordinate][1]:
                    arrSize[coordinate][1] = arrDimensions[1]
        return arrSize
    def UseMinimumSimulationBox(self):
        arrSize = self.GetMinimumSimulationBox()
        self._Size = arrSize
    def SetFileHeader(self, inString: str):
        self.__FileHeader = inString
    def WrapVectorIntoSimulationBox(self, inVector: np.array)->np.array:
        return gf.WrapVectorIntoSimulationCell(self.__BasisVectors, self.__InverseBasis, inVector)
    def WriteLAMMPSDataFile(self,inFileName: str):        
        now = datetime.now()
        strDateTime = now.strftime("%d/%m/%Y %H:%M:%S")
        with open(inFileName, 'w') as fdata:
            fdata.write('## ' + strDateTime + ' ' + self.__FileHeader + '\n')
            fdata.write('{} atoms\n'.format(self.GetTotalNumberOfAtoms()))
            fdata.write('{} atom types\n'.format(self.GetNumberOfAtomTypes()))
            fdata.write('{} {} xlo xhi\n'.format(self.__xlo,self.__xhi))
            fdata.write('{} {} ylo yhi\n'.format(self.__ylo,self.__yhi))
            if self.Dimensions == 3:
                fdata.write('{} {} zlo zhi\n'.format(self.__zlo,self.__zhi))
                fdata.write('{}  {} {} xy xz yz \n'.format(self.__xy,self.__xz,self.__yz))
            elif self.Dimensions ==2:
                fdata.write('{}  xy \n'.format(self.__xy))
            fdata.write('\n')
            fdata.write('Atoms\n\n')
            if self.blnPointsAreWrapped:
                for j in range(len(self.__UniqueRealPoints)):
                    fdata.write('{} {} {} {} {}\n'.format(j+1,self.__AtomTypes[j], *self.__UniqueRealPoints[j]))
            else:
                count = 1
                for j in self.GrainList:
                    for position in self.GetGrain(j).GetRealPoints():
                        fdata.write('{} {} {} {} {}\n'.format(count,self.GetGrain(j).GetAtomType(), *position))
                        count = count + 1
    def SetOrigin(self,inOrigin: np.array):
        self.__Origin = inOrigin
        self.__xlo = inOrigin[0]
        self.__ylo = inOrigin[1]
        self.__zlo = inOrigin[2]
    def GetOrigin(self):
        return self.__Origin 
    def SetParallelpipedVectors(self,inArray: np.array): 
        self.__BoxVectors = inArray
        self.__xhi = inArray[0][0] - self.__Origin[0]
        self.__xy = inArray[1][0] 
        self.__yhi = inArray[1][1] - self.__Origin[1]
        if self.Dimensions == 3:
            self.__xz = inArray[2][0] 
            self.__yz = inArray[2][1] 
            self.__zhi = inArray[2][2] - self.__Origin[2]
            self.__BasisVectors = np.array([[self.__xhi,0,0],[self.__xy, self.__yhi,0],[self.__xz, self.__yz,self.__zhi]])
            lstBasisVectors = []
            for j in self.__BasisVectors:
                lstBasisVectors.append(gf.NormaliseVector(j))
            self.__UnitBasisVectors = np.array(lstBasisVectors)
            self.__InverseUnitBasis = np.linalg.inv(self.__UnitBasisVectors)
            self.__InverseBasis = np.linalg.inv(self.__BasisVectors)
    def WrapAllPointsIntoSimulationCell(self, intRound = 5)->np.array:
        lstUniqueRowindices = []
        arrAllAtoms = np.zeros([self.GetTotalNumberOfAtoms(),self.Dimensions])
        arrAllAtomTypes = np.ones([self.GetTotalNumberOfAtoms()],dtype=np.int8)
        i = 0
        for j in self.GrainList:
            for fltPoint in self.GetGrain(j).GetRealPoints():
                arrAllAtomTypes[i] = self.GetGrain(j).GetAtomType()
                arrAllAtoms[i] = fltPoint
                i = i + 1
        arrAllAtoms = np.round(self.WrapVectorIntoSimulationBox(arrAllAtoms),intRound)
        self.__UniqueRealPoints,lstUniqueRowindices = np.unique(arrAllAtoms,axis=0,return_index=True)
        self.__AtomTypes = arrAllAtomTypes[lstUniqueRowindices]  
        self.blnPointsAreWrapped = True
    def PlotSimulationCellAtoms(self):
        if self.blnPointsAreWrapped:
            return tuple(zip(*self.__UniqueRealPoints))
    def RemovePlaneOfAtoms(self, inPlane: np.array, fltTolerance: float):
        arrPointsOnPlane = gf.CheckLinearEquality(np.round(self.__UniqueRealPoints,10), inPlane,fltTolerance)
        self.__UniqueRealPoints = np.delete(self.__UniqueRealPoints,arrPointsOnPlane, axis=0)   
    def GetRealPoints(self)->np.array:
        if self.blnPointsAreWrapped:
            return self.__UniqueRealPoints
        else:
            raise("Error: Points need to be wrapped into simulation cell")

class Grain(object):
    def __init__(self, intGrainNumber: int):
        self.__GrainID = intGrainNumber
        self.__GlobalID = -1
        self.__AdjacentGrainBoundaries = []
        self.__AdjacentJunctionLines = []
        self.__AdjacentGrains = []
        self.__GrainCentre = []
    def SetAdjacentGrainBoundaries(self, lstAdjacentGrainBoundaries):
        self.__AdjacentGrainBoundaries
    def GetAdjacentGrainBoundaries(self):
        return self.__AdjacentGrainBoundaries
    def SetAdjacentJunctionLines(self, lstAdjacentJunctionLines):
        self.__AdjacentJunctionLines
    def GetAdjacentJunctionLines(self):
        return self.__AdjacentJunctionLines
    def SetGrainCentre(self, arrGrainCentre):
        self.__GrainCentre = arrGrainCentre
    def GetGrainCentre(self):
        return self.__GrainCentre
        
class DefectMeshObject(object):
    def __init__(self,inMeshPoints: np.array, intID: int):
        self.__MeshPoints = inMeshPoints
        self.__ID = intID
        self.__OriginalID = intID
        self.__AtomIDs = []
        self.__AdjustedMeshPoints = [] #these are general mesh points adjusted to correct for the limited accuracy of the QuantisedCuboid object
        self.__Volume = 0
        self.__PE = 0
    def GetMeshPoints(self):
        return np.copy(self.__MeshPoints)
    def GetOriginalID(self):
        return self.__OriginalID 
    def GetID(self):
        return self.__ID
    def SetID(self, intID):
        self.__ID = intID
    def GetNumberOfAtoms(self):
        return len(self.__AtomIDs)
    def SetAtomIDs(self, inlstIDs: list):
        self.__AtomIDs = list(map(int,inlstIDs))
    def GetAtomIDs(self)->list:
        return cp.copy(self.__AtomIDs)
    def AddAtomIDs(self, inList):
        inList = set(map(int,inList))
        self.__AtomIDs = list(inList.union(self.__AtomIDs))
    def RemoveAtomIDs(self, inList):
        setAtomIDs = set(self.__AtomIDs)
        self.__AtomIDs = list(setAtomIDs.difference(inList))
    def SetMeshPoints(self, inPoints):
        self.__MeshPoints = inPoints
    def SetAdjustedMeshPoints(self, inPoints: np.array):
        self.__AdjustedMeshPoints = inPoints
    def GetAdjustedMeshPoints(self)->np.array:
        return self.__AdjustedMeshPoints
    def SetVolume(self, fltVolume):
        self.__Volume = fltVolume 
    def GetVolume(self):
        return self.__Volume
    def GetVolumePerAtom(self):
        if self.GetNumberOfAtoms() > 0: 
            return self.__Volume/self.GetNumberOfAtoms()
    def GetAtomicDensity(self):
        if self.__Volume > 0 and len(self.__AtomIDs) > 0:
            return len(self.__AtomIDs)/self.__Volume
        else:
            return 0   
    def SetPeriodicDirections(self, inList):
        self.__PeriodicDirections = inList
    def GetPeriodicDirections(self):
        return cp.copy(self.__PeriodicDirections)
    def GetTotalPE(self, fltPEDatum = None):
        if fltPEDatum is None:
            return self.__PE
        else:
            return self.__PE - fltPEDatum*self.GetNumberOfAtoms()
    def SetTotalPE(self, fltPE):
        self.__PE = fltPE 
    def GetPEPerAtom(self, fltPEDatum = None):
        if self.GetNumberOfAtoms() > 0:
            return self.GetTotalPE(fltPEDatum)/len(self.__AtomIDs)
    def GetPEPerVolume(self, fltPEDatum = None):
        if self.__Volume > 0:
            return self.GetTotalPE(fltPEDatum)/self.__Volume
    

class GeneralJunctionLine(DefectMeshObject):
    def __init__(self,inMeshPoints: np.array, intID: int):
        DefectMeshObject.__init__(self,inMeshPoints, intID)
        self.__AdjacentGrains = []
        self.__AdjacentGrainBoundaries = []
        self.__PeriodicDirections = []
    def SetAdjacentGrains(self, inList):
        self.__AdjacentGrains = inList
    def GetAdjacentGrains(self)->list:
        return cp.copy(self.__AdjacentGrains)
    def SetAdjacentGrainBoundaries(self, inList):
        self.__AdjacentGrainBoundaries = inList
    def GetAdjacentGrainBoundaries(self)->list:
        return cp.copy(self.__AdjacentGrainBoundaries)
   
class GeneralGrainBoundary(DefectMeshObject):
    def __init__(self,inMeshPoints: np.array, intID: str):
        DefectMeshObject.__init__(self,inMeshPoints, intID)
        self.__AdjacentGrains = []
        self.__AdjacentJunctionLines = []
        self.__AdjacentGrainBoundaries = []
        self.__PeriodicDirections = [] 
        self.__GlobalAdjacentJunctionLines = []   
    def SetAdjacentGrains(self, inList):
        self.__AdjacentGrains = inList
    def GetAdjacentGrains(self)->list:
        return cp.copy(self.__AdjacentGrains) 
    def SetAdjacentJunctionLines(self, inList):
        self.__AdjacentJunctionLines = inList
    def GetAdjacentJunctionLines(self)->list:
        return cp.copy(self.__AdjacentJunctionLines)
   
class DefectObject(object):
    def __init__(self, fltTimeStep = None):
        if fltTimeStep is not None:
            self.__TimeStep = fltTimeStep
        else:
            self.__TimeStep = []
        self.__dctJunctionLines = dict()
        self.__dctGrainBoundaries = dict()
    def AddJunctionLine(self, objJunctionLine: GeneralJunctionLine):
        self.__dctJunctionLines[objJunctionLine.GetID()] = objJunctionLine 
    def AddGrainBoundary(self, objGrainBoundary: GeneralGrainBoundary):
        self.__dctGrainBoundaries[objGrainBoundary.GetID()] = objGrainBoundary
    def GetJunctionLine(self, intLocalKey: int):
        return self.__dctJunctionLines[intLocalKey]
    def GetGrainBoundary(self, intLocalKey):
        return self.__dctGrainBoundaries[intLocalKey]      
    def GetJunctionLineIDs(self):
        return list(self.__dctJunctionLines.keys())
    def GetGrainBoundaryIDs(self):
        return list(self.__dctGrainBoundaries.keys())
    def GetAdjacentGrainBoundaries(self, intJunctionLine: int)->list:
        lstAdjacentGrainBoundaries = []
        for j in self.GetJunctionLine(intJunctionLine).GetAdjacentGrainBoundaries():
            lstAdjacentGrainBoundaries.append(self.GetGrainBoundary(j).GetID())
        return lstAdjacentGrainBoundaries
    def GetAdjacentJunctionLines(self, intGrainBoundary: int)->list:
        lstAdjacentJunctionLines = []
        for j in self.GetGrainBoundary(intGrainBoundary).GetAdjacentJunctionLines():
            lstAdjacentJunctionLines.append(self.GetJunctionLine(j).GetID())
        return lstAdjacentJunctionLines
    def SetTimeStep(self, fltTimeStep):
        self.__TimeStep = fltTimeStep
    def GetTimeStep(self):
        return self.__TimeStep
    def ImportData(self, strFilename: str):
        with open(strFilename,'r') as fdata:
            blnNotEnd = True
            try:
                line = next(fdata).strip()
                objJunctionLine = None
                objGrainBoundary = None
                while blnNotEnd:
                    if line == "Time Step":
                        self.__TimeStep = int(next(fdata).strip())
                        line = next(fdata).strip()
                    elif line == "Junction Line":
                        intJL = int(next(fdata).strip())
                        line = next(fdata).strip()
                        if line == "Mesh Points":
                            line = next(fdata).strip()    
                            arrMeshPoints = np.array(eval(line))
                            objJunctionLine = GeneralJunctionLine(arrMeshPoints, intJL)
                            line = next(fdata).strip()
                        if line == "Adjacent Grains":
                            line = next(fdata).strip()    
                            objJunctionLine.SetAdjacentGrains(eval(line))
                            line = next(fdata).strip()
                        if line == "Adjacent Grain Boundaries":
                            line = next(fdata).strip()
                            objJunctionLine.SetAdjacentGrainBoundaries(eval(line))
                            line = next(fdata).strip()
                        if line == "Periodic Directions":
                            line = next(fdata).strip()
                            objJunctionLine.SetPeriodicDirections(eval(line))
                            line = next(fdata).strip()
                        if line == "Atom IDs":
                            line = next(fdata).strip()
                            objJunctionLine.SetAtomIDs(eval(line))
                            line = next(fdata).strip()
                        if line == "Volume":
                            line = next(fdata).strip()
                            objJunctionLine.SetVolume(eval(line))
                            line = next(fdata).strip()
                        if line == "PE":
                            line = next(fdata).strip()
                            objJunctionLine.SetTotalPE(eval(line))
                            line = next(fdata).strip()
                        if line == "Adjusted Mesh Points":
                            line = next(fdata).strip()
                            arrAdjustedMeshPoints = np.array(eval(line))
                            objJunctionLine.SetAdjustedMeshPoints(arrAdjustedMeshPoints)
                            line = next(fdata).strip()
                        self.AddJunctionLine(objJunctionLine)       
                    elif line == "Grain Boundary":
                        intGB = int(next(fdata).strip())
                        line = next(fdata).strip()
                        if line == "Mesh Points":
                            line = next(fdata).strip()    
                            arrMeshPoints = np.array(eval(line))
                            objGrainBoundary = GeneralGrainBoundary(arrMeshPoints, intGB)
                            line = next(fdata).strip()
                        if line == "Adjacent Grains":
                            line = next(fdata).strip()    
                            objGrainBoundary.SetAdjacentGrains(eval(line))
                            line = next(fdata).strip()
                        if line == "Adjacent Junction Lines":
                            line = next(fdata).strip()
                            objGrainBoundary.SetAdjacentJunctionLines(eval(line))
                            line = next(fdata).strip()
                        if line == "Periodic Directions":
                            line = next(fdata).strip()
                            objGrainBoundary.SetPeriodicDirections(eval(line))
                            line = next(fdata).strip()
                        if line == "Atom IDs":
                            line = next(fdata).strip()
                            objGrainBoundary.SetAtomIDs(eval(line))
                            line = next(fdata).strip()
                        if line == "Volume":
                            line = next(fdata).strip()
                            objGrainBoundary.SetVolume(eval(line))
                            line = next(fdata).strip()
                        if line == "PE":
                            line = next(fdata).strip()
                            objGrainBoundary.SetTotalPE(eval(line))
                            line = next(fdata).strip()
                        if line == "Adjusted Mesh Points":
                            line = next(fdata).strip()
                            arrAdjustedMeshPoints = np.array(eval(line))
                            objGrainBoundary.SetAdjustedMeshPoints(arrAdjustedMeshPoints)
                            line = next(fdata).strip()
                        self.AddGrainBoundary(objGrainBoundary)
                    else:
                        blnNotEnd = False
            except StopIteration as EndOfFile:
                if objJunctionLine is not None:
                    self.AddJunctionLine(objJunctionLine) #Some fields are optional so end of file may come
                if objGrainBoundary is not None:
                    self.AddGrainBoundary(objGrainBoundary) #before the GB or JL objects have been added        
                blnNotEnd = False

class SigmaCell(object):
    def __init__(self, arrRotationAxis: np.array, inCellNodes: np.array):
        intGCD = np.gcd.reduce(arrRotationAxis)
        self.__RotationAxis = (arrRotationAxis/intGCD).astype('int')
        if np.all(self.__RotationAxis == np.array([0,0,1])):
            self.__LatticeBasis = gf.StandardBasisVectors(3)
            self.__CellHeight = 1
        else:
            fltAngle, arrVector = gf.FindRotationVectorAndAngle(arrRotationAxis, np.array([0,0,1]))
            self.__LatticeBasis = gf.RotatedBasisVectors(fltAngle,arrVector)
            self.__CellHeight = np.linalg.norm(self.__RotationAxis)
        self.__CellType = inCellNodes
        self.__BasisVectors = []
    def GetRotationAxis(self):
        return self.__RotationAxis
    def GetSigmaValues(self, intSigmaMax):
        return  gf.CubicCSLGenerator(self.__RotationAxis, intSigmaMax)
    def MakeCSLCell(self, intSigmaValue: int, arrHorizontalVector = np.array([1,0,0])):
        arrSigma = self.GetSigmaValues(2*intSigmaValue)
        arrRows = np.argwhere(arrSigma[:,0] == intSigmaValue)
        if len(arrRows) > 0:
            intSigmaValue == arrSigma[arrRows[0],0]
            h = self.__CellHeight
            l = intSigmaValue
            fltSigma = arrSigma[arrRows[0],1]
            objFirstLattice = ExtrudedRectangle(l,l,np.sqrt(3),gf.RotateVectors(0,np.array([0,0,1]),self.__LatticeBasis), self.__CellType, np.ones(3),np.zeros(3))
            objSecondLattice = ExtrudedRectangle(l,l,np.sqrt(3),gf.RotateVectors(fltSigma,np.array([0,0,1]),self.__LatticeBasis),self.__CellType,np.ones(3),np.zeros(3))
            arrPoints1 = objFirstLattice.GetRealPoints()
            arrPoints2 = objSecondLattice.GetRealPoints()
            arrDistanceMatrix = sc.spatial.distance_matrix(arrPoints1, arrPoints2)
            lstPoints = np.where(arrDistanceMatrix < 1e-5)[0]
            arrCSLPoints = arrPoints1[lstPoints]
            arrBase = arrCSLPoints[arrCSLPoints[:,2] == 0.0]
            lstBase = arrBase.tolist()
            lstBase.remove(np.zeros(3).tolist())
            arrBase = np.array(lstBase)
            arrDistances = np.linalg.norm(arrBase,axis=1)
            arrClosestPoint = gf.NormaliseVector(arrBase[np.argmin(arrDistances)])
            fltdotX =  np.arccos(np.dot(arrClosestPoint, arrHorizontalVector))
            fltAngle2 = -fltdotX
            self.__LatticeRotations = np.array([fltAngle2, fltSigma+ fltAngle2])
            objFirstLattice = ExtrudedRectangle(l,l,h,gf.RotateVectors(fltAngle2,np.array([0,0,1]),self.__LatticeBasis), self.__CellType, np.ones(3),np.zeros(3))
            objSecondLattice = ExtrudedRectangle(l,l,h,gf.RotateVectors(fltSigma+fltAngle2,np.array([0,0,1]),self.__LatticeBasis),self.__CellType,np.ones(3),np.zeros(3))
            arrPoints1 = objFirstLattice.GetRealPoints()
            arrPoints2 = objSecondLattice.GetRealPoints()
            arrDistanceMatrix = sc.spatial.distance_matrix(arrPoints1, arrPoints2)
            lstPoints = np.where(arrDistanceMatrix < 1e-5)[0]
            arrCSLPoints = arrPoints1[lstPoints]
            arrBase = arrCSLPoints[arrCSLPoints[:,2] == 0.0]
            lstBase = arrBase.tolist()
            lstBase.remove(np.zeros(3).tolist())
            arrBase = np.array(lstBase)
            arrDistances = np.linalg.norm(arrBase, axis=1)
            lstPositions = gf.FindNthSmallestPosition(arrDistances, 0)
            arrVector1 = arrBase[lstPositions[0]]
            if len(lstPositions) > 1:
                arrVector2 = arrBase[lstPositions[1]]
            else:
                arrVector2 = arrBase[gf.FindNthSmallestPosition(arrDistances,1)[0]]

            if np.dot(arrVector1, arrHorizontalVector) > np.dot(arrVector2, arrHorizontalVector):   
                self.__BasisVectors = np.array([arrVector1, arrVector2, h*np.array([0,0,1])])
            else:
                self.__BasisVectors = np.array([arrVector2, arrVector1, h*np.array([0,0,1])])
        else:
            warnings.warn("Invalid sigma value for axis " + str(self.__RotationAxis))
    def GetBasisVectors(self):
        return self.__BasisVectors
    def GetLatticeRotations(self):
        return self.__LatticeRotations