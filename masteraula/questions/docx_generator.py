from html.parser import HTMLParser

from docx import *
from docx.shared import Inches, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
import urllib
from urllib.error import HTTPError

import re
import os
import datetime

import time

current_milli_time = lambda: int(round(time.time() * 1000))

class Docx_Generator():
    ''' Classe responsavel por realizer o parser para geracao de listas de
    questoes  '''
    # Controle do documento
    docx_title = ''
    column_index = -1

    def __init__(self, title):
        HTMLParser.__init__(self)
        # Faz o novo documento
        self.document = Document()
        self.docx_title = title
        self.html_file = open(str(current_milli_time()), 'w')
    
    def writeHtmlFile(self, questions):
        question_counter = 0
        for question in questions:
            question_counter = question_counter + 1
            self.html_file.write('<h1>Questao %d</h1>' % question_counter)
            for learning_object in question.learning_objects:
                if learning_object.image:
                    self.html_file.write('<img src="localhost:8000%s" />' % image)
                else:
                    self.html_file.write(learning_object.text)
            self.html_file.write(learning_object.statement)

            question_item = 'a'
            for alternative in question.alternatives.all():
                self.html_file.write(alternative.text)
                question_item = chr(ord(question_item) + 1)

    def closeHtmlFile(self):
        self.html_file.close()