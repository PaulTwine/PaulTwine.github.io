import sys
import numpy as np
from scipy import stats
import GeometryFunctions as gf

def UpdateTemplate(lstOriginal: list, lstNew: list, strOldFilename: str,strNewFilename: str):
    fIn = open(strOldFilename, 'rt')
    fData = fIn.read()
    for j in range(len(lstOriginal)):
        fData = fData.replace(lstOriginal[j], lstNew[j])
    fIn.close()
    fIn = open(strNewFilename, 'wt')
    fIn.write(fData)
    fIn.close()

def WriteAnnealTemplate(strDirectory: str, strFilename: str, intTemp: int, intRuns = 100000):
    strLogFile =  strFilename + '.log'
    str1MinDumpFile = '1Min*.dmp'
    str2MinDumpFile = '2Min*.dmp'
    strDumpFile = '1Sim*.dmp'
    strDatFile = strFilename + '.dat'
    strFirstMin = '1Min.lst'
    strLastMin = '2Min.lst'
    strLAMMPS =''
    strLAMMPS += 'units metal\n'
    strLAMMPS += 'dimension 3\n'
    strLAMMPS += 'boundary p p p\n'
    strLAMMPS += 'atom_style atomic\n'
    strLAMMPS += 'box tilt large\n'
    strLAMMPS += 'read_data ' + strDatFile +'\n'
    strLAMMPS += 'log ' + strLogFile +  '\n'
    strLAMMPS += 'pair_style eam/alloy\n'
    strLAMMPS += 'pair_coeff * * Al03.eam.alloy Al\n'
    strLAMMPS += 'neighbor 0.3 bin\n'
    strLAMMPS += 'neigh_modify delay 10\n'
    strLAMMPS += 'thermo 100\n'
    strLAMMPS += 'compute pe1 all pe/atom\n'
    strLAMMPS += 'compute v all voronoi/atom\n'
    strLAMMPS += 'compute pt all ptm/atom default 0.15 all\n'
    strLAMMPS += 'compute st all stress/atom NULL virial\n'
    strLAMMPS += 'dump 1 all custom 100 ' + str1MinDumpFile + ' id x y z vx vy vz c_pe1 c_v[1] c_pt[1] c_pt[4] c_pt[5] c_pt[6] c_pt[7] c_st[1] c_st[2] c_st[3] c_st[4] c_st[5] c_st[6]\n'
    strLAMMPS += 'min_style fire\n'
    strLAMMPS += 'timestep 0.002\n'
    strLAMMPS += 'min_modify integrator verlet tmax 6.0 dmax 0.1\n'
    strLAMMPS += 'minimize 0.0 1.0e-6 10000 100000\n'
    strLAMMPS += 'write_dump all custom ' + strFirstMin + ' id x y z vx vy vz c_pe1 c_v[1] c_pt[1] c_pt[4] c_pt[5] c_pt[6] c_pt[7] c_st[1] c_st[2] c_st[3] c_st[4] c_st[5] c_st[6]\n'
    strLAMMPS += 'undump 1 \n'
    strLAMMPS += 'reset_timestep 0\n'
    strLAMMPS += 'timestep 0.001\n'
    strLAMMPS += 'dump 2 all custom 100 ' + strDumpFile + ' id x y z vx vy vz c_pe1 c_v[1] c_pt[1] c_pt[4] c_pt[5] c_pt[6] c_pt[7] c_st[1] c_st[2] c_st[3] c_st[4] c_st[5] c_st[6]\n'
    strLAMMPS += 'velocity all create ' + str(intTemp) + ' 24577\n'
    strLAMMPS += 'fix 2 all nvt temp ' + str(intTemp) + ' ' + str(intTemp) + ' $(100.0*dt)\n'
    strLAMMPS += 'run ' +str(intRuns) + '\n'
    strLAMMPS += 'unfix 2 \n'
    strLAMMPS += 'undump 2 \n'
    strLAMMPS += 'timestep 0.002\n'
    strLAMMPS += 'dump 3 all custom 100 ' + str2MinDumpFile + ' id x y z vx vy vz c_pe1 c_v[1] c_pt[1] c_pt[4] c_pt[5] c_pt[6] c_pt[7] c_st[1] c_st[2] c_st[3] c_st[4] c_st[5] c_st[6]\n'
    strLAMMPS += 'minimize 0.0 1.0e-6 10000 100000\n'
    strLAMMPS += 'write_dump all custom ' + strLastMin + ' id x y z vx vy vz c_pe1 c_v[1] c_pt[1] c_pt[4] c_pt[5] c_pt[6] c_pt[7] c_st[1] c_st[2] c_st[3] c_st[4] c_st[5] c_st[6]\n'
    fIn = open(strDirectory + strFilename + '.in', 'wt')
    fIn.write(strLAMMPS)
    fIn.close()


def WriteRestartTemplate(strDirectory: str, strFilename: str, intTemp: int,intTimeStart:int, intRuns = 100000):
    strLogFile =  strFilename + '.log'
    str2MinDumpFile = '2Min*.dmp'
    strDumpFile = '1Sim*.dmp'
    strDatFile = strFilename + '.dat'
    strLastMin = '2Min.lst'
    strLAMMPS =''
    strLAMMPS += 'units metal\n'
    strLAMMPS += 'dimension 3\n'
    strLAMMPS += 'boundary p p p\n'
    strLAMMPS += 'atom_style atomic\n'
    strLAMMPS += 'box tilt large\n'
    strLAMMPS += 'read_data ' + strDatFile +'\n'
    strLAMMPS += 'log ' + strLogFile +  '\n'
    strLAMMPS += 'pair_style eam/alloy\n'
    strLAMMPS += 'pair_coeff * * Al03.eam.alloy Al\n'
    strLAMMPS += 'neighbor 0.3 bin\n'
    strLAMMPS += 'neigh_modify delay 10\n'
    strLAMMPS += 'thermo 100\n'
    strLAMMPS += 'compute pe1 all pe/atom\n'
    strLAMMPS += 'compute v all voronoi/atom\n'
    strLAMMPS += 'compute pt all ptm/atom default 0.15 all\n'
    strLAMMPS += 'compute st all stress/atom NULL virial\n'
    strLAMMPS += 'reset_timestep ' + str(intTimeStart) + ' \n'
    strLAMMPS += 'timestep 0.001\n'
    strLAMMPS += 'dump 2 all custom 100 ' + strDumpFile + ' id x y z vx vy vz c_pe1 c_v[1] c_pt[1] c_pt[4] c_pt[5] c_pt[6] c_pt[7] c_st[1] c_st[2] c_st[3] c_st[4] c_st[5] c_st[6]\n'
    strLAMMPS += 'velocity all create ' + str(intTemp) + ' 24577\n'
    strLAMMPS += 'fix 2 all nvt temp ' + str(intTemp) + ' ' + str(intTemp) + ' $(100.0*dt)\n'
    strLAMMPS += 'run ' +str(intRuns) + '\n'
    strLAMMPS += 'unfix 2 \n'
    strLAMMPS += 'undump 2 \n'
    strLAMMPS += 'timestep 0.002\n'
    strLAMMPS += 'dump 3 all custom 100 ' + str2MinDumpFile + ' id x y z vx vy vz c_pe1 c_v[1] c_pt[1] c_pt[4] c_pt[5] c_pt[6] c_pt[7] c_st[1] c_st[2] c_st[3] c_st[4] c_st[5] c_st[6]\n'
    strLAMMPS += 'minimize 0.0 1.0e-6 10000 100000\n'
    strLAMMPS += 'write_dump all custom ' + strLastMin + ' id x y z vx vy vz c_pe1 c_v[1] c_pt[1] c_pt[4] c_pt[5] c_pt[6] c_pt[7] c_st[1] c_st[2] c_st[3] c_st[4] c_st[5] c_st[6]\n'
    fIn = open(strDirectory + strFilename + '.in', 'wt')
    fIn.write(strLAMMPS)
    fIn.close()

def WriteMinTemplate(strDirectory: str, strFilename: str):
    strLogFile =  strFilename + '.log'
    str1MinDumpFile = strFilename + '*.dmp'
    strDatFile = strFilename + '.dat'
    strFirstMin = strFilename + '.lst'
    strLAMMPS =''
    strLAMMPS += 'units metal\n'
    strLAMMPS += 'dimension 3\n'
    strLAMMPS += 'boundary p p p\n'
    strLAMMPS += 'atom_style atomic\n'
    strLAMMPS += 'box tilt large\n'
    strLAMMPS += 'read_data ' + strDatFile +'\n'
    strLAMMPS += 'log ' + strLogFile +  '\n'
    strLAMMPS += 'pair_style eam/alloy\n'
    strLAMMPS += 'pair_coeff * * Al03.eam.alloy Al\n'
    strLAMMPS += 'neighbor 0.3 bin\n'
    strLAMMPS += 'neigh_modify delay 10\n'
    strLAMMPS += 'thermo 100\n'
    strLAMMPS += 'compute pe1 all pe/atom\n'
    strLAMMPS += 'compute v all voronoi/atom\n'
    strLAMMPS += 'compute pt all ptm/atom default 0.15 all\n'
    strLAMMPS += 'compute st all stress/atom NULL virial\n'
    strLAMMPS += 'dump 1 all custom 100 ' + str1MinDumpFile + ' id x y z vx vy vz c_pe1 c_v[1] c_pt[1] c_pt[4] c_pt[5] c_pt[6] c_pt[7] c_st[1] c_st[2] c_st[3] c_st[4] c_st[5] c_st[6]\n'
    strLAMMPS += 'min_style fire\n'
    strLAMMPS += 'timestep 0.002\n'
    strLAMMPS += 'min_modify integrator verlet tmax 6.0 dmax 0.1\n'
    strLAMMPS += 'minimize 0.0 1.0e-6 10000 100000\n'
    strLAMMPS += 'write_dump all custom ' + strFirstMin + ' id x y z vx vy vz c_pe1 c_v[1] c_pt[1] c_pt[4] c_pt[5] c_pt[6] c_pt[7] c_st[1] c_st[2] c_st[3] c_st[4] c_st[5] c_st[6]\n'
    fIn = open(strDirectory + strFilename + '.in', 'wt')
    fIn.write(strLAMMPS)
    fIn.close()

def WriteGBDrivenTemplate(strDirectory: str, strFilename: str, intTemp: int, intRuns: int, lstEco: list, strEcoFilename: str):
    strLogFile =  strFilename + '.log'
    str1MinDumpFile = '1Min*.dmp'
    str2MinDumpFile = '2Min*.dmp'
    strDumpFile = '1Sim*.dmp'
    strDatFile = strFilename + '.dat'
    strFirstMin = '1Min.lst'
    strLastMin = '2Min.lst'
    strLAMMPS =''
    strLAMMPS += 'units metal\n'
    strLAMMPS += 'dimension 3\n'
    strLAMMPS += 'boundary p p p\n'
    strLAMMPS += 'atom_style atomic\n'
    strLAMMPS += 'box tilt large\n'
    strLAMMPS += 'read_data ' + strDatFile +'\n'
    strLAMMPS += 'log ' + strLogFile +  '\n'
    strLAMMPS += 'pair_style eam/alloy\n'
    strLAMMPS += 'pair_coeff * * Al03.eam.alloy Al\n'
    strLAMMPS += 'neighbor 0.3 bin\n'
    strLAMMPS += 'neigh_modify delay 10\n'
    strLAMMPS += 'thermo 100\n'
    strLAMMPS += 'compute pe1 all pe/atom\n'
    strLAMMPS += 'compute v all voronoi/atom\n'
    strLAMMPS += 'compute pt all ptm/atom default 0.15 all\n'
    strLAMMPS += 'compute st all stress/atom NULL virial\n'
    strLAMMPS += 'dump 1 all custom 100 ' + str1MinDumpFile + ' id x y z vx vy vz c_pe1 c_v[1] c_pt[1] c_pt[4] c_pt[5] c_pt[6] c_pt[7] c_st[1] c_st[2] c_st[3] c_st[4] c_st[5] c_st[6]\n'
    strLAMMPS += 'min_style fire\n'
    strLAMMPS += 'timestep 0.002\n'
    strLAMMPS += 'min_modify integrator verlet tmax 6.0 dmax 0.1\n'
    strLAMMPS += 'minimize 0.0 1.0e-6 10000 100000\n'
    strLAMMPS += 'write_dump all custom ' + strFirstMin + ' id x y z vx vy vz c_pe1 c_v[1] c_pt[1] c_pt[4] c_pt[5] c_pt[6] c_pt[7] c_st[1] c_st[2] c_st[3] c_st[4] c_st[5] c_st[6]\n'
    strLAMMPS += 'undump 1 \n'
    strLAMMPS += 'reset_timestep 0\n'
    strLAMMPS += 'timestep 0.001\n'
    if len(strEcoFilename) > 0:
        strLAMMPS += 'fix 1 all orient/eco ' +  str(lstEco[0]) + ' ' + str(lstEco[1]) + ' ' + str(lstEco[2])  + ' ' + strEcoFilename + '\n'
        strLAMMPS += 'fix_modify 1 energy yes \n'
    strLAMMPS += 'dump 2 all custom 100 ' + strDumpFile + ' id x y z vx vy vz c_pe1 c_v[1] c_pt[1] c_pt[4] c_pt[5] c_pt[6] c_pt[7] c_st[1] c_st[2] c_st[3] c_st[4] c_st[5] c_st[6]' 
    if len(strEcoFilename)> 0: 
        strLAMMPS += ' f_1[1] f_1[2] \n'
    else: 
        strLAMMPS += '\n'
    strLAMMPS += 'velocity all create ' + str(intTemp) + ' 24577\n'
    strLAMMPS += 'fix 2 all nvt temp ' + str(intTemp) + ' ' + str(intTemp) + ' $(100.0*dt)\n'
    strLAMMPS += 'run ' +str(intRuns) + '\n'
    strLAMMPS += 'unfix 2 \n'
    strLAMMPS += 'undump 2 \n'
    if len(strEcoFilename) > 0:
        strLAMMPS += 'unfix 1 \n'
    strLAMMPS += 'timestep 0.002\n'
    strLAMMPS += 'dump 3 all custom 100 ' + str2MinDumpFile + ' id x y z vx vy vz c_pe1 c_v[1] c_pt[1] c_pt[4] c_pt[5] c_pt[6] c_pt[7] c_st[1] c_st[2] c_st[3] c_st[4] c_st[5] c_st[6]\n'
    strLAMMPS += 'minimize 0.0 1.0e-6 10000 100000\n'
    strLAMMPS += 'write_dump all custom ' + strLastMin + ' id x y z vx vy vz c_pe1 c_v[1] c_pt[1] c_pt[4] c_pt[5] c_pt[6] c_pt[7] c_st[1] c_st[2] c_st[3] c_st[4] c_st[5] c_st[6]\n'
    fIn = open(strDirectory + strFilename + '.in', 'wt')
    fIn.write(strLAMMPS)
    fIn.close()

def WriteTJDrivenTemplate(strDirectory: str, strFilename: str, intTemp: int, intRuns: int, lstEco: list, lstEcoFilenames: list):
    strLogFile =  strFilename + '.log'
    str1MinDumpFile = '1Min*.dmp'
    str2MinDumpFile = '2Min*.dmp'
    strDumpFile = '1Sim*.dmp'
    strDatFile = strFilename + '.dat'
    strFirstMin = '1Min.lst'
    strLastMin = '2Min.lst'
    strLAMMPS =''
    strLAMMPS += 'units metal\n'
    strLAMMPS += 'dimension 3\n'
    strLAMMPS += 'boundary p p p\n'
    strLAMMPS += 'atom_style atomic\n'
    strLAMMPS += 'box tilt large\n'
    strLAMMPS += 'read_data ' + strDatFile +'\n'
    strLAMMPS += 'log ' + strLogFile +  '\n'
    strLAMMPS += 'pair_style eam/alloy\n'
    strLAMMPS += 'pair_coeff * * Al03.eam.alloy Al\n'
    strLAMMPS += 'neighbor 0.3 bin\n'
    strLAMMPS += 'neigh_modify delay 10\n'
    strLAMMPS += 'thermo 100\n'
    strLAMMPS += 'thermo_style custom step temp pe etotal press\n'
    strLAMMPS += 'compute pe1 all pe/atom\n'
    strLAMMPS += 'compute v all voronoi/atom\n'
    strLAMMPS += 'compute pt all ptm/atom default 0.15 all\n'
    strLAMMPS += 'compute st all stress/atom NULL virial\n'
    strLAMMPS += 'dump 1 all custom 100 ' + str1MinDumpFile + ' id x y z vx vy vz c_pe1 c_v[1] c_pt[1] c_pt[4] c_pt[5] c_pt[6] c_pt[7] c_st[1] c_st[2] c_st[3] c_st[4] c_st[5] c_st[6]\n'
    strLAMMPS += 'min_style fire\n'
    strLAMMPS += 'timestep 0.002\n'
    strLAMMPS += 'min_modify integrator verlet tmax 6.0 dmax 0.1\n'
    strLAMMPS += 'minimize 0.0 1.0e-6 10000 100000\n'
    strLAMMPS += 'write_dump all custom ' + strFirstMin + ' id x y z vx vy vz c_pe1 c_v[1] c_pt[1] c_pt[4] c_pt[5] c_pt[6] c_pt[7] c_st[1] c_st[2] c_st[3] c_st[4] c_st[5] c_st[6]\n'
    strLAMMPS += 'undump 1 \n'
    strLAMMPS += 'reset_timestep 0\n'
    strLAMMPS += 'timestep 0.001\n'
    strLAMMPS += 'fix 1 all orient/eco ' +  str(lstEco[0]) + ' ' + str(lstEco[1]) + ' ' + str(lstEco[2])  + ' ' + str(lstEcoFilenames[0]) + '\n'
    strLAMMPS += 'fix 2 all orient/eco ' +  str(lstEco[0]) + ' ' + str(lstEco[1]) + ' ' + str(lstEco[2])  + ' ' + str(lstEcoFilenames[1]) + '\n'
    strLAMMPS += 'fix_modify 1 energy yes \n'
    strLAMMPS += 'fix_modify 2 energy yes \n'
    strLAMMPS += 'dump 2 all custom 100 ' + strDumpFile + ' id x y z vx vy vz c_pe1 c_v[1] c_pt[1] c_pt[4] c_pt[5] c_pt[6] c_pt[7] c_st[1] c_st[2] c_st[3] c_st[4] c_st[5] c_st[6] f_1[1] f_1[2] f_2[1] f_2[2] \n'
    strLAMMPS += 'velocity all create ' + str(intTemp) + ' 24577\n'
    strLAMMPS += 'fix 3 all nvt temp ' + str(intTemp) + ' ' + str(intTemp) + ' $(100.0*dt)\n'
    strLAMMPS += 'run ' +str(intRuns) + '\n'
    strLAMMPS += 'unfix 3 \n'
    strLAMMPS += 'undump 2 \n'
    strLAMMPS += 'unfix 2 \n'
    strLAMMPS += 'unfix 1 \n'
    strLAMMPS += 'timestep 0.002\n'
    strLAMMPS += 'dump 3 all custom 100 ' + str2MinDumpFile + ' id x y z vx vy vz c_pe1 c_v[1] c_pt[1] c_pt[4] c_pt[5] c_pt[6] c_pt[7] c_st[1] c_st[2] c_st[3] c_st[4] c_st[5] c_st[6]\n'
    strLAMMPS += 'minimize 0.0 1.0e-6 10000 100000\n'
    strLAMMPS += 'write_dump all custom ' + strLastMin + ' id x y z vx vy vz c_pe1 c_v[1] c_pt[1] c_pt[4] c_pt[5] c_pt[6] c_pt[7] c_st[1] c_st[2] c_st[3] c_st[4] c_st[5] c_st[6]\n'
    fIn = open(strDirectory + strFilename + '.in', 'wt')
    fIn.write(strLAMMPS)
    fIn.close()

def LogNormalConfidenceInterval(arrValues: np.array, fltAlpha: float, blnInside = True)-> np.array:
    arrPositive = np.where(arrValues > 0)[0]
    arrLog = np.log(arrValues[arrPositive])
    mu,st = stats.norm.fit(arrLog)
    tupValues = stats.norm.interval(alpha=fltAlpha, loc=mu, scale=st)
    if blnInside:
        arrRows = np.where((arrLog > tupValues[0]) & (arrLog < tupValues[1]))[0]
    else:
        arrRows = np.where((arrLog < tupValues[0] ) | (arrLog > tupValues[1]))[0]
    return arrRows
def ConfidenceInterval(arrValues: np.array, fltAlpha: float, blnInside = True)-> np.array:
    mu,st = stats.norm.fit(arrValues)
    tupValues = stats.norm.interval(alpha=fltAlpha, loc=mu, scale=st)
    if blnInside:
        arrRows = np.where((arrValues > tupValues[0]) & (arrValues < tupValues[1]))[0]
    else:
        arrRows = np.where((arrValues < tupValues[0] ) | (arrValues > tupValues[1]))[0]
    return arrRows
def MatchPairsOfIDs(lstOldIDs: list, lstNewIDs: list):
        arrMatrix = np.zeros([len(lstNewIDs), len(lstOldIDs)])
        for i in range(len(lstNewIDs)):
            for j in range(len(lstOldIDs)):
                arrMatrix[i,j] = len(set(lstOldIDs[j]).intersection(lstNewIDs[i]))
        lstMatched = []
        for j in arrMatrix:
                blnMatched = False
                counter = 0
                while not(blnMatched) and counter < len(j):
                    k = gf.FindNthLargestPosition(j, counter)
                    if k not in lstMatched:
                        lstMatched.append(k[0])
                        blnMatched = True
                    counter += 1
        return lstMatched
def FlattenList(t):
    return [item for sublist in t for item in sublist]



        