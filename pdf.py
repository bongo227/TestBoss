import os

from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams, LTRect, LTLine, LTTextBoxHorizontal
from pdfminer.pdfpage import PDFPage
from cStringIO import StringIO
from pdfminer.converter import PDFPageAggregator

from wand.image import Image

def process_pdf(path, out_folder):
    laparams = LAParams()
    rsrcmgr = PDFResourceManager()
    document = file(path, 'rb')
    device = PDFPageAggregator(rsrcmgr, laparams=laparams)
    interpreter = PDFPageInterpreter(rsrcmgr, device)

    for i, page in enumerate(PDFPage.get_pages(document)):
        # if i == 3:
        #     break

        print "Page {}".format(i)

        interpreter.process_page(page)
        layout = device.get_result()
        # print layout._objs
        
        space = 0
        textboxes = [r for r in layout._objs if type(r) is LTTextBoxHorizontal ]
        for t in textboxes:
            if t.get_text().startswith("Answer space for question"):
                space = t.y0

        img_path = os.path.join(os.getcwd(), "{}[{}]".format(path, i))
        # print img_path
        # img_path = path.replace('\\', '/')
        # print img_path
        scale = 1

        with Image(filename=img_path, resolution=int(72*scale)) as img:
            # Crop the margins
            x = 46 * scale
            y = 66 * scale
            width = 489 * scale
            height = 711 * scale
            # Crop the working out space
            height -= (space - 50) * scale
            
            if height > scale and space > 0:
                img.crop(int(x), int(y), width=int(width), height=int(height))
                img.save(filename="{}/q{}.jpg".format(out_folder, i))
