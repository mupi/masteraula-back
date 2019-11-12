import difflib
import unidecode

from fuzzywuzzy import process, fuzz
from taggit.models import Tag, TaggedItem

from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q

from masteraula.questions.models import Question, Discipline, Topic

process.SequenceMatcher = difflib.SequenceMatcher

ct = ContentType.objects.get(app_label='questions', model='question')

def prepare_choices_and_topics(discipline):
    choices = []
    name_topics = {}
    for topic in Topic.objects.filter(discipline=discipline):
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

def tag_similar_topic(discipline):
    with open('topics_{}.csv'.format(discipline.name), 'w') as matches, open('unmatched_topics_{}.csv'.format(discipline.name), 'w') as unmatches:
        questions = Question.objects.filter(Q(tags__isnull=False)&Q(disciplines__in=[discipline])&Q(disabled=False)).distinct().prefetch_related('tags', 'topics').order_by('id')

        choices, name_topics = prepare_choices_and_topics(discipline)
        id_questions = prepare_id_questions(questions)
        tagged_questions = prepare_tagged_questions(questions)

        for t in sorted(tagged_questions.keys()):
            res = process.extract(t, choices, scorer=fuzz.token_sort_ratio, limit=3)
            if res and res[0][1] > 80:
                matches.write('{},"{}",{}\n'.format(t, res, ' '.join([str(t) for t  in tagged_questions[t]])))
            else:
                unmatches.write('{},"{}",{}\n'.format(t, res, ' '.join([str(t) for t in tagged_questions[t]])))

class Command(BaseCommand):
    help = 'Check if tag has a similar topic inside the same discipline, if score is >80, is match, else, unmatch'

    def handle(self, *args, **options):
        
        for discipline in Discipline.objects.all():
            print(discipline.name)
            tag_similar_topic(discipline)

        print('Ok')