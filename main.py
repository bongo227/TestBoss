import os
from pdf import process_pdf
from subprocess import call

folder_path = 'papers/'
papers = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join('papers/', f))]

for p in papers:
    # Create folder for questions
    paper_path = os.path.join('papers/', p)
    out_folder_path = paper_path[:-4] + '-Questions/'
    unlocked_paper_path = os.path.join(out_folder_path, p[:-4] + "-u.pdf") 
    if not os.path.isdir(out_folder_path):
        os.makedirs(out_folder_path)

        # Unlock pdfs
        call(['qpdf', '--decrypt', paper_path, unlocked_paper_path])

        process_pdf(unlocked_paper_path, out_folder_path)
