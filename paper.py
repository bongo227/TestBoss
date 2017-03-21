import re
import pickle
import os
import subprocess
import math

from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams, LTRect, LTLine, LTTextBoxHorizontal
from pdfminer.pdfpage import PDFPage
from cStringIO import StringIO
from pdfminer.converter import PDFPageAggregator
from wand.image import Image
from wand.color import Color

from question import Question
from util import find_between


class InvalidFilenameError(Exception):
    pass


class Paper():
    MONTH_REGEX = re.compile(r'(JAN|JUN)')
    YEAR_REGEX = re.compile(r'\d\d')
    MODULE_REGEX = re.compile(r'(MPC1|MPC2|MPC3|MPC4|MS1B|MS2B|MS03|MS04)')
    QUALITY = 1

    def __init__(self, qp_path, ms_path):
        self._month = Paper.MONTH_REGEX.findall(qp_path)[0]
        self._year = Paper.YEAR_REGEX.findall(qp_path)[-1]
        self._module = Paper.MODULE_REGEX.findall(qp_path)[0]
        self._questions = []

        # Create output directory
        self._folder = os.path.join(
            os.getcwd(), "papers/", "{}-{}{}".format(self._module, self._month, self._year))
        if os.path.isdir(self._folder):
            # Folder exsists so load from pickle file
            with open(os.path.join(self._folder, 'paper.pkl'), 'rb') as f:
                class_data = pickle.load(f)
                self.__dict__.update(class_data)
            return
        else:
            os.makedirs(self._folder)

        # Unlock PDF's
        unlocked_qp = os.path.join(self._folder, "_QP.pdf")
        subprocess.call(['qpdf', '--decrypt', qp_path, unlocked_qp])
        unlocked_ms = os.path.join(self._folder, "_MS.pdf")
        subprocess.call(['qpdf', '--decrypt', ms_path, unlocked_ms])

        # Extract PDF's
        self._extract_qp(unlocked_qp)
        self._extract_ms(unlocked_ms)

        # Save class as pickle file
        pickle_path = os.path.join(self._folder, 'paper.pkl')
        pickle.dump(self.__dict__, open(pickle_path, "wb"))

    def _save_cropped(self, name, img, x, y, width, height):
        with Image(img) as cropped:
            cropped.crop(x, y, width, height)
            path = os.path.join(self._folder, name + ".png")
            cropped.save(filename=path)

    def _extract_qp(self, file_name):
        mark_sum = 0
        print "Extracting QP"

        # Load pdf
        laparams = LAParams()
        rsrcmgr = PDFResourceManager()
        document = file(file_name, 'rb')
        device = PDFPageAggregator(rsrcmgr, laparams=laparams)
        interpreter = PDFPageInterpreter(rsrcmgr, device)

        q_num = 0
        for i, page in enumerate(PDFPage.get_pages(document)):
            # Get page layout
            interpreter.process_page(page)
            layout = device.get_result()

            # Extract metadata
            textboxes = [r for r in layout._objs if type(
                r) is LTTextBoxHorizontal]
            work_out_y = 0
            answer_header = 0
            marks = []

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
                    pass
                    # print repr(text)

            marks = [int(m) for m in marks]
            mark_sum += sum(marks)

            # Comver page into image
            img_path = "{}[{}]".format(file_name, i)
            img = Image(filename=img_path, resolution=int(72 * Paper.QUALITY))

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
            self._questions.append(Question(img_path, q_num, marks))

        print "Marks: {}".format(mark_sum)

    def _extract_ms(self, file_name):
        print "Extracting MS"

        self._new_questions = []
        self._questions.reverse()
        current_question = self._questions.pop()

        # Load PDF
        laparams = LAParams()
        rsrcmgr = PDFResourceManager()
        document = file(file_name, 'rb')
        device = PDFPageAggregator(rsrcmgr, laparams=laparams)
        interpreter = PDFPageInterpreter(rsrcmgr, device)

        for i, page in enumerate(PDFPage.get_pages(document)):
            if i != 3:
                continue

            # Convert pdf page to png
            img_path = os.path.join(self._folder, "temp.png")
            with Image(filename=file_name + "[{}]".format(i),
                       resolution=int(72 * Paper.QUALITY)) as img:

                with Image(width=img.width, height=img.height,
                           background=Color("white")) as background:
                    background.composite(img, 0, 0)
                    background.save(filename=img_path)

            # Load png to crop
            with Image(filename=img_path) as img:
                # Set initial crop
                x = 28 * Paper.QUALITY
                y = 0
                width = 567 * Paper.QUALITY
                height = img.height

                # Get page layout
                interpreter.process_page(page)
                layout = device.get_result()

                # Extract metadata
                textboxes = [r for r in layout._objs if isinstance(
                    r, LTTextBoxHorizontal)]

                ms_top = 0

                for textbox in textboxes:
                    text = textbox.get_text()

                    if text in ["Solution \n", "Mark \n", "Total \n", "Comment \n"]:
                        if ms_top == text.y0 or ms_top == 0:
                            ms_top = text.y0
                        else:
                            pass
                            # Crop up to this point and reset (2 questions on page)
                    else:
                        print repr(text)

                path = os.path.join(self._folder, "m{}.png".format(i))
                img.crop(x, y, width, height)
                img.save(filename=path)

                # # Extract metadata
                # textboxes = [r for r in layout._objs if isinstance(
                #     r, LTTextBoxHorizontal)]
                # q_num = 0
                # q_y = 0
                # q_height = 0
                # for textbox in textboxes:
                #     text = textbox.get_text()

                #     q_passed = False
                #     if text.startswith("Q"):
                #         q_passed = True
                #         try:
                #             q_num = int(text[1])
                #         except ValueError:
                #             pass
                #     elif text.startswith("\nQ"):
                #         q_passed = True
                #         try:
                #             q_num = int(text[3])
                #         except ValueError:
                #             pass

                #     if q_passed:
                #         if q_y > 0:
                #             y = q_y
                #             new_q_y = img.height - int(textbox.y1) - 4
                #             height = new_q_y - q_y
                #             self._save_cropped("m{}".format(
                #                 q_num), img, img_x, y, img_width, height)
                #             q_y = new_q_y
                #         else:
                #             q_y = img.height - int(textbox.y1) - 4

                # if q_num > 0:
                #     self._save_cropped("m{}".format(
                #         q_num), img, img_x, q_y, img_width, img_height)

            os.remove(img_path)

    def get_month(self):
        """
        Gets the month of the paper (JUN or JUL).
        """
        return self._month

    def get_year(self):
        """
        Gets the last to digits of the papers year.
        """
        return self._year
