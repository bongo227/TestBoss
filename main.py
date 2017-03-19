import os
import pickle
from subprocess import call

from pdf import process_pdf
from paper import Paper

folder_path = 'papers/'
papers = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join('papers/', f))]

for p in papers:
    test_paper = None

    # Create folder for questions
    paper_path = os.path.join('papers/', p)
    out_folder_path = paper_path[:-4] + '-Questions/'
    if not os.path.isdir(out_folder_path):
        # Make directory for files
        os.makedirs(out_folder_path)
        
        # Unlock pdfs
        unlocked_paper_path = os.path.join(out_folder_path, p[:-4] + "-u.pdf") 
        call(['qpdf', '--decrypt', paper_path, unlocked_paper_path])
        
        # Load/extract paper
        test_paper = Paper(unlocked_paper_path, out_folder_path)
    else:
        # Load/extract paper from pickle
        pickle_path = os.path.join(out_folder_path, 'paper.pkl')
        test_paper = pickle.load(file(pickle_path, 'rb'))

    print test_paper._questions