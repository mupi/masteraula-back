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
from subprocess import call

current_milli_time = lambda: int(round(time.time() * 1000))

class Docx_Generator():
    ''' Classe responsavel por realizer o parser para geracao de listas de
    questoes  '''   

    def __init__(self):
        # Faz o novo documento
        self.document = Document()
        self.docx_name = str(current_milli_time())

        #self.html_file = open('file.html', 'w')
        self.html_file = open(self.docx_name + '.html', 'w')
        self.html_file.write('<head> <meta charset="UTF-8"> </head>')
    
    def writeQuestions(self, questions):
        question_counter = 0
        for question in questions:
            question_counter = question_counter + 1
            self.html_file.write('<h1>Questão %d</h1>' % question_counter)
            for learning_object in question.learning_objects.all():
                if learning_object.image:
                    self.html_file.write('<img src="localhost:8000%s" />' % image)
                else:
                    self.html_file.write(learning_object.text)
            self.html_file.write(question.statement)

            question_item = 'a'
            for alternative in question.alternatives.all():
                self.html_file.write('<p>%s) %s</p>' % (question_item, alternative.text)) 
                #self.html_file.write(alternative.text)
                question_item = chr(ord(question_item) + 1)
        

    def close(self):
        self.html_file.close()
        call (['pandoc', self.docx_name + '.html', '-o',self.docx_name + '.docx'])
        os.remove(self.docx_name + '.html')
        return(self.docx_name)
        