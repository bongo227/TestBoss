import re
import pickle
import os

from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams, LTRect, LTLine, LTTextBoxHorizontal
from pdfminer.pdfpage import PDFPage
from cStringIO import StringIO
from pdfminer.converter import PDFPageAggregator
from wand.image import Image

from question import Question
from util import find_between

class InvalidFilenameError(Exception):
    pass

class Paper():
    MONTH_REGEX = re.compile(r'(JAN|JUN)')
    YEAR_REGEX = re.compile(r'\d\d')
    QUALITY = 1

    def __init__(self, file_name, out_folder="/"):
        self._month = Paper.MONTH_REGEX.findall(file_name)[:-1]
        self._year = Paper.YEAR_REGEX.findall(file_name)[:-1]
        self._questions = []
        self._folder = out_folder

        ext = file_name[-3:]
        if ext == 'pdf':
            self._extract_pdf(file_name)


    def _extract_pdf(self, file_name):
        mark_sum = 0
        print "Extracting PDF"
        # Load pdf
        laparams = LAParams()
        rsrcmgr = PDFResourceManager()
        document = file(file_name, 'rb')
        device = PDFPageAggregator(rsrcmgr, laparams=laparams)
        interpreter = PDFPageInterpreter(rsrcmgr, device)

        q_num =  0
        for i, page in enumerate(PDFPage.get_pages(document)):
            # Get page layout
            interpreter.process_page(page)
            layout = device.get_result()


            # Extract metadata
            textboxes = [r for r in layout._objs if type(r) is LTTextBoxHorizontal ]
            work_out_y = 0
            marks = []
            answer_header = 0
            for t in textboxes:
                text = t.get_text()
                if "Answer space for question" in text:
                    work_out_y = int(t.y0)
                elif "marks]" in text:
                    marks.extend(find_between(text, "[", " marks]"))
                elif "mark]" in text:
                    marks.extend(find_between(text, "[", " mark]"))
                elif "......" in text:
                    # TODO: Find the correct amount of dots
                    pass
                elif text in ["QUESTION\n", "PART\n", "REFERENCE\n"]:
                    pass
                elif text in ["Do not write\noutside the\n", "box\n", "Turn over s\n"]:
                    pass
                elif text == "Answer all questions.\n":
                    answer_header = 74
                else:
                    print repr(text)
                    # if q_num == 6:
                    #     print repr(text)
            marks = [int(m) for m in marks]
            mark_sum += sum(marks)

            # Comver page into image
            img_path = "{}[{}]".format(file_name, i)
            img = Image(filename=img_path, resolution=int(72*Paper.QUALITY))
            
            # Set crop positions
            x = 46 * Paper.QUALITY
            y = (66 + answer_header) * Paper.QUALITY
            width = 489 * Paper.QUALITY
            height = (761 - answer_header - work_out_y) * Paper.QUALITY
            
            # Check for blank pages
            if height <= Paper.QUALITY or work_out_y <= 0:
                continue
            
            # Crop and save the image
            q_num += 1
            img.crop(x, y, width=width, height=height)
            img_path = os.path.join(self._folder, "q{}.jpg".format(q_num))
            img.save(filename=img_path)
            
            # Add question to questions
            self._questions.append(Question(img_path, marks))

        # Save class as pickle file
        pickle_path = os.path.join(self._folder, 'paper.pkl')
        pickle.dump(self, open(pickle_path, "wb"))

        print "Marks: {}".format(mark_sum)

    def get_month(self):
        return self._month

    def get_year(self):
        return self._year