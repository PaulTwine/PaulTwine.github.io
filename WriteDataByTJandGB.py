import numpy as np
import sys
import AxisSigmaDeltaStores as AS
strDir = str(sys.argv[1]) # '/home/paul/csf4_scratch/TJ/Axis001/TJSigma13/'
strType = str(sys.argv[2]) # 'TJ'
lstAxis = eval(sys.argv[3])
intSigma = int(sys.argv[4])
intDir = int(sys.argv[5])
intDelta = int(sys.argv[6])
objGB = AS.PopulateDeltaStore(intSigma,np.array(lstAxis),strDir,strType,intDir,intDelta , True)


