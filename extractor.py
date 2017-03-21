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
from wand.drawing import Drawing
from wand.compat import nested

def DebugExtract(path, out):
    # Load pdf
    laparams = LAParams()
    rsrcmgr = PDFResourceManager()
    document = file(path, 'rb')
    device = PDFPageAggregator(rsrcmgr, laparams=laparams)
    interpreter = PDFPageInterpreter(rsrcmgr, device)

    for i, page in enumerate(PDFPage.get_pages(document)):
        # Get page layout
        interpreter.process_page(page)
        layout = device.get_result()

        textboxes = [r for r in layout._objs if type(r) is LTTextBoxHorizontal]
        rects = [r for r in layout._objs if type(r) is LTRect]
        lines = [r for r in layout._objs if type(r) is LTLine]

        page_path = "{}[{}]".format(path, i)
        print i
        with Drawing() as draw:
            with Image(filename=page_path) as img:
                with Image(width=img.width, height=img.height, background=Color("white")) as background:
                    background.composite(img, 0, 0)
                    
                    # Draw rectangles
                    draw.fill_color = Color("transparent")
                    
                    totals = []
                    for txt in textboxes:
                        # print repr(txt.get_text())
                        if txt.get_text() in ["Total \n", "Marks  Total \n"]:
                            print "found total..."
                            totals.append(txt)
                    if len(totals) == 1:
                        totals.append(totals[0])

                    def draw_rects(objs, color):
                        draw.stroke_color = Color(color)
                        for obj in objs:
                            top = img.height - obj.y0
                            bottom = img.height - obj.y1
                            draw.rectangle(left=obj.x0, top=bottom, right=obj.x1, bottom=top)
                    # draw_rects(textboxes, "red")
                    boxes = []
                    box_count = len(totals) / 2
                    if len(rects) > 0:
                        for b in range(box_count):
                            print b
                            big = 1000000
                            x0 = big
                            # y0 = big
                            # ymax = big
                            # if b < box_count-1:
                            #     ymax = img.height - totals[b+2].y0  
                            x1 = 0
                            # y1 = totals[0].y1
                            # if b < box_count-1:
                            #     y1 = totals[b+1].y0
                            ymin = 55
                            ymax = big
                            
                            y0 = img.height - totals[b*2].y1
                            y1 = img.height - totals[b*2+1].y0
                            
                            if b < box_count - 1:
                                # Ensures the bottom of this block is above the next box
                                ymax = img.height - totals[(b+1)*2].y1
                                
                            if b > 0:
                                # Ensures that the top of this box is bellow the last box
                                ymin = boxes[-1][3] + 1

                            print y0, y1, ymin, ymax

                            # ymax = big
                            # if b < box_count-1:
                            #     ymax = totals[(b+1)*2].y1

                            # print "before:"
                            # print x0, y0, x1, y1, ymax

                            for r in rects:
                                x0 = min(r.x0, x0)
                                x1 = max(r.x1, x1)
                                if (img.height - r.y0) > ymin:
                                    y0 = min(img.height - r.y0, y0)
                                if (img.height - r.y1) < ymax:
                                    y1 = max(img.height - r.y1, y1)
                                
                            # print "after:"
                            # print x0, y0, x1, y1
                            
                            boxes.append((x0, y0, x1, y1))

                        if box_count > 0:
                            foo = 0
                            for (x0, y0, x1, y1) in boxes:
                                if foo == 0:
                                    draw.stroke_color = Color("green")
                                    draw.stroke_width = 1
                                elif foo == 1:
                                    draw.stroke_color = Color("red")
                                    draw.stroke_width = 1
                                foo += 1
                                draw.rectangle(left=x0, top=y0, right=x1, bottom=y1)

                        # if y1 > y0 and len(totals) > 0:
                            # draw.stroke_color = Color("green")
                            # draw.rectangle(left=x0, top=img.height-y1, right=x1, bottom=img.height-y0)
                            # draw.stroke_color = Color("blue")
                            # draw.rectangle(left=x0, top=img.height-totals[0].y1, right=x1, bottom=img.height-y0)

                    # draw_rects(rects, "blue")
                    draw(background)

                    background.save(filename=os.path.join(out, "t{}.png".format(i)))

DebugExtract('_MS.pdf', 'test/')