import boto3
import json
import base64
import time

from subprocess import call
from django.conf import settings


current_milli_time = lambda: int(round(time.time() * 1000))

class DocxGeneratorAWS():

    def __init__(self):
        # Faz o novo documento
        self.docx_name = str(current_milli_time())

        self.html_file = open(self.docx_name + '.html', 'w', encoding='utf8')
        self.html_file.write('<head><meta charset="UTF-8"></head>')
    

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
            if learning_object.source:
                self.html_file.write('<p>%s</p>' % learning_object.source)


    def write_question(self, question, question_counter):
        self.html_file.write('<h3>Questão %d</h3>\n' % (question_counter + 1))

        self.html_file.write(question.statement)
    

    def write_alternatives(self, question):
        question_item = 'a'
        for alternative in question.alternatives.all():
            self.html_file.write('<p>%s) %s </p>' % (question_item, alternative.text)) 
            question_item = chr(ord(question_item) + 1)


    def write_answers(self, questions):
        self.html_file.write('<h2> Gabarito </h2>')
        self.html_file.write('<table>')
        self.html_file.write('<tr><th><b> Questão </b></th><th><b> Resposta </b></th></tr>')

        for question_counter, question in enumerate(questions):
            self.html_file.write('<tr><td>{}</td>'.format(question_counter + 1))

            question_item = 'a'
            answered = False
            for answer in question.alternatives.all():
                if answer.is_correct:
                    self.html_file.write('<td>{}</td></tr>'.format(question_item))
                    answered = True
                question_item = chr(ord(question_item) + 1)

            if not answered:
                self.html_file.write('<td> Sem resposta </td></tr>')
        
        self.html_file.write('</table>')


    def close_html_file(self):
        self.html_file.close()


    def generate_document(self, document, answers=False):
        if not document.questions:
            raise exceptions.ValidationError('Can not generate an empty list')

        questions = [dq.question for dq in document.documentquestion_set.all().order_by('order')]

        # Saves the learning objects that have already been used
        learning_objects_questions = []

        for question_counter, question in enumerate(questions):

            if question_counter not in learning_objects_questions:
                
                # Verify if that the learning object has already been used
                current_learning_objects = [q for q in question.learning_objects.values().order_by('id')]
                if current_learning_objects:
                    first_question_counter = question_counter + 1
                    last_question_counter = first_question_counter
                    # Check the first and last question that uses that learning object
                    for i in range(first_question_counter, len(questions)):
                        if current_learning_objects != [q for q in questions[i].learning_objects.values().order_by('id')]:
                            break

                        learning_objects_questions.append(i)
                        last_question_counter = last_question_counter + 1
                    
                    self.write_learning_objects(question.learning_objects.all().order_by('id'), first_question_counter, last_question_counter)
                        
            self.write_question(question, question_counter)

            self.write_alternatives(question)

        if answers:
            self.write_answers(document.questions.all())
        
        self.close_html_file()

        if settings.RUNNING_DEVSERVER:
            call(['pandoc', '--reference-doc', 'reference.docx', '-o', self.docx_name + '.docx', self.docx_name + '.html'])
            return

        # Upload S3 file, call Lambda function and then Dwonload the result
        session = boto3.Session(
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name='us-east-2'
        )

        s3 = session.resource('s3')
        s3.meta.client.upload_file(self.docx_name + '.html', 'masteraula-documents',  'html/{}.html'.format(self.docx_name))

        client = session.client('lambda')
        event = {"filename" : self.docx_name}
        response = client.invoke(
            FunctionName = 'MasteraulaDocumentGenerator',
            InvocationType='RequestResponse',
            Payload=json.dumps(event)
        )
        s3.meta.client.download_file('masteraula-documents', 'docx/{}.docx'.format(self.docx_name), '{}.docx'.format(self.docx_name))
    