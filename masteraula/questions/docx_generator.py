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
    ''' Classe responsavel por realizer o parser para geracao de listas de questoes  '''   

    def __init__(self):
        # Faz o novo documento
        self.document = Document()
        self.docx_name = str(current_milli_time())

        #self.html_file = open('file.html', 'w')
        self.html_file = open(self.docx_name + '.html', 'w', encoding='utf8')
        self.html_file.write('<head><meta charset="UTF-8"></head>')

    def write_title(self, document):
        #Insere o texto com o nome do documento
        self.html_file.write('<h1>%s</h1>' % document.name)
    
    def write_header(self, header):               
        self.html_file.write('<table>')
                
        if header.institution_name:
            self.html_file.write('<tr><td><b> Instituição: </b> %s </td></tr>' % header.institution_name)
        if header.discipline_name:
            self.html_file.write('<tr><td><b> Disciplina: </b> %s </td></tr>' % header.discipline_name)
        if header.professor_name:
            self.html_file.write('<tr><td><b> Professor(a): </b> %s </td></tr>' % header.professor_name)

        if header.student_indicator:
            self.html_file.write('<tr><td><b> Aluno: </b></td></tr>')
        if header.class_indicator:
            self.html_file.write('<tr><td><b> Turma: </b></td></tr>')
        if header.score_indicator:
            self.html_file.write('<tr><td><b> Nota da avaliação: </b></td></tr>')
        if header.date_indicator: 
            self.html_file.write('<tr><td><b> Data: </b>               /                /        </td></tr>')
      
        self.html_file.write('</table>')    
        
    def write_questions(self, questions):
        learning_objects_questions = []
        for question_counter, question in enumerate(questions):
            if question_counter not in learning_objects_questions:
                learning_objects = [q for q in question.learning_objects.values()]
                if learning_objects:
                    first = question_counter + 1
                    last = first
                    for i in range(first, len(questions)):
                        if learning_objects != [q for q in questions[i].learning_objects.values()]:
                            break
                        learning_objects_questions.append(i)
                        last = last + 1
                    
                    self.write_learning_objects(question.learning_objects.all(), first, last)

    
    def write_learning_objects(self, learning_objects, first, last):
        if first == last:
            self.html_file.write('<h2> Material para a questão %d</h2>\n' %  first)
        else:
            self.html_file.write('<h2> Material para a questão %d a %d </h2>\n' % (first, last))

        for learning_object in learning_objects:
            if learning_object.image:
                self.html_file.write('<img src="%s" />\n' % learning_object.image.url)
            else:
                self.html_file.write(learning_object.text)

    def write_questions(self, questions):
        learning_objects_questions = []

        for question_counter, question in enumerate(questions):
            if question_counter not in learning_objects_questions:
                learning_objects = [q for q in question.learning_objects.values()]
                if learning_objects:
                    first = question_counter + 1
                    last = first
                    for i in range(first, len(questions)):
                        if learning_objects != [q for q in questions[i].learning_objects.values()]:
                            break

                        learning_objects_questions.append(i)
                        last = last + 1
                    
                    self.write_learning_objects(question.learning_objects.all().order_by('id'), first, last)
                        
            self.html_file.write('<h3>Questão %d</h3>' % (question_counter + 1))

            self.html_file.write(question.statement)
            
            question_item = 'a'
            for alternative in question.alternatives.all():
                self.html_file.write('<p>%s) %s </p>' % (question_item, alternative.text)) 
                #self.html_file.write(alternative.text)
                question_item = chr(ord(question_item) + 1)

    def write_answers(self, questions):
        '''Faz o parser do gabarito, em formato de tabela'''

        question_counter = 0

        # Adiciona a tabela e seus cabecalhos
        self.html_file.write('<h2> Gabarito </h2>')
        self.html_file.write('<table>')
        self.html_file.write('<tr><th><b> Questão </b></th><th><b> Resposta </b></th></tr>')

       
        for question in questions:
            question_counter = question_counter + 1
            self.html_file.write('<tr><td> %d </td>' % question_counter)

            question_item = 'a'
            answered = False
            # Procura pela questao correta
            for answer in question.alternatives.all():
                if answer.is_correct:
                    self.html_file.write('<td> %s </td></tr>' % question_item)
                    answered = True
                question_item = chr(ord(question_item) + 1)

            # Se nao houve questao correta, adiciona sem resposta
            if not answered:
                self.html_file.write('<td> Sem resposta </td></tr>' % question_item)
        
        self.html_file.write('</table>')  

    def close(self):
        self.html_file.close()
        #Utiliza um arquivo como referencia para os estilos, pois o pandoc não intepreta atributos de css para converter em docx
        call(['pandoc', '--reference-doc', 'reference.docx', '-o', self.docx_name + '.docx', self.docx_name + '.html'])
        #call (['pandoc', self.docx_name + '.html', '-o', self.docx_name + '.docx'])
        os.remove(self.docx_name + '.html')
        return(self.docx_name)
        
