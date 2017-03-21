import os
import pickle
from subprocess import call

from paper import Paper

folder_path = 'papers/'
qp = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join('papers/', f)) and "QP-" in f]
ms = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join('papers/', f)) and "MS-" in f]

qp = sorted(qp)
ms = sorted(ms)

for i in range(len(qp)):
    qp_path = os.path.join('papers/', qp[i])
    ms_path = os.path.join('papers/', ms[i])
    test_paper = Paper(qp_path, ms_path)
    print test_paper._questions