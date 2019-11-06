import difflib
import unidecode
import csv

from fuzzywuzzy import process, fuzz
from taggit.models import Tag, TaggedItem

from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q

from masteraula.questions.models import Question, Discipline, Topic

process.SequenceMatcher = difflib.SequenceMatcher

ct = ContentType.objects.get(app_label='questions', model='question')

def prepare_choices_and_topics():
    choices = []
    name_topics = {}
    for topic in Topic.objects.all():
        choices.append(topic.name)

        if topic.name in name_topics:
            name_topics[topic.name].append(topic)
        else:
            name_topics[topic.name] = [topic]

    return choices, name_topics

def prepare_id_questions(questions):
    id_questions = {}
    for question in questions:
        id_questions[question.id] = question

    return id_questions

def prepare_tagged_questions(questions):
    tagged_questions = {}
    for question in questions:
        for tag in question.tags.all():
            if tag.name in tagged_questions:
                tagged_questions[tag.name].append(question.id)
            else:
                tagged_questions[tag.name] = [question.id]

    return tagged_questions

def tags_to_topics(discipline, choices, name_topics):
    with open('changed_topics_{}.csv'.format(discipline.name), 'a') as matches:
        questions = Question.objects.filter(Q(tags__isnull=False)&Q(disciplines__in=[discipline])&Q(disabled=False)).distinct().prefetch_related('tags', 'topics').order_by('id')

        id_questions = prepare_id_questions(questions)
        tagged_questions = prepare_tagged_questions(questions)

        for t in sorted(tagged_questions.keys()):
            res = process.extractOne(t, choices, scorer=fuzz.token_sort_ratio)
            if res and res[1] >= 100:
                print('{} -> {}'.format(t, res[0]))

                tag = Tag.objects.get(name=t)
                topics = name_topics[res[0]]

                for question_id in tagged_questions[t]:
                    question = id_questions[question_id]

                    for topic in topics:
                        question.topics.add(topic)
                    
                    print(question.pk)
                
                TaggedItem.objects.filter(tag=tag, object_id__in=tagged_questions[t], content_type=ct).delete()
                matches.write('{},"{}",{}\n'.format(t, res[0], ' '.join(str(a) for a in tagged_questions[t])))

def tags_to_topics_filename(reader, discipline):
    with open('changed_topics_{}.csv'.format(discipline.name), 'a') as matches:
        questions = Question.objects.filter(Q(tags__isnull=False)&Q(disciplines__in=[discipline])&Q(disabled=False)).distinct().prefetch_related('tags', 'topics').order_by('id')

        _, name_topics = prepare_choices_and_topics()
        id_questions = prepare_id_questions(questions)
        tagged_questions = prepare_tagged_questions(questions)

        for row in reader:
            if (row[0].strip() == ''):
                continue
            t = row[0].strip()
            res = eval(row[1])[0]
            print('{} -> {}'.format(t, res[0]))

            try:
                tag = Tag.objects.get(name=t)
                topics = name_topics[res[0]]
            except:
                print('Tag {} or topic {} does not exist'.format(t, res[0]))
                continue

            if t not in tagged_questions:
                print('Tag {} does not contain any question'.format(t))
                continue

            for question_id in tagged_questions[t]:
                question = id_questions[question_id]

                for topic in topics:
                    question.topics.add(topic)
                
                print(question.pk)
            
            TaggedItem.objects.filter(tag=tag, object_id__in=tagged_questions[t], content_type=ct).delete()
            matches.write('{},"{}",{}\n'.format(t, res[0], ' '.join(str(a) for a in tagged_questions[t])))

class Command(BaseCommand):
    help = 'Tranform tag into topic, if scrores 100, o filename and discipline passed'

    def add_arguments(self, parser):
        parser.add_argument('--filename', type=str, default='')
        parser.add_argument('--discipline', type=str, default='')

    def handle(self, *args, **options):
        if options['filename'] and options['discipline']:
            try:
                discipline = Discipline.objects.get(name=options['discipline'])
            except:
                print('Discipline {} does not exist'.format(options['discipline']))
                exit(1)

            with open(options['filename'], 'r') as csvfile:
                reader = csv.reader(csvfile, delimiter=',')
                tags_to_topics_filename(reader, discipline)
            return

        if options['filename'] or options['discipline']:
            print('Should pass filename with discipline')
            exit(1)
        
        choices, name_topics = prepare_choices_and_topics()
        for discipline in Discipline.objects.all():
            print(discipline.name)
            tags_to_topics(discipline, choices, name_topics)

        print('Ok')