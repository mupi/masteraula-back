from taggit.models import Tag, TaggedItem
from masteraula.questions.models import Question, Discipline, Topic
from django.contrib.contenttypes.models import ContentType

from django.db.models import Q

from fuzzywuzzy import process, fuzz
import difflib

import unidecode

process.SequenceMatcher = difflib.SequenceMatcher

ct = ContentType.objects.get(app_label='questions', model='question')

for discipline in Discipline.objects.all():
    print(discipline.name)

    with open('topics_{}.csv'.format(discipline.name), 'w') as matches, open('unmatched_topics_{}.csv'.format(discipline.name), 'w') as unmatches:
        tagged_questions = {}
        questions = Question.objects.filter(Q(tags__isnull=False)&Q(disciplines__in=[discipline])&Q(disabled=False)).distinct().prefetch_related('tags', 'topics').order_by('id')
        id_questions = {}

        choices = []
        name_topics = {}
        for topic in Topic.objects.filter(discipline=discipline):
            choices.append(topic.name)

            if topic.name in name_topics:
                name_topics[topic.name].append(topic)
            else:
                name_topics[topic.name] = [topic]

        for question in questions:
            id_questions[question.id] = question

        for question in questions:
            for tag in question.tags.all():
                if tag.name in tagged_questions:
                    tagged_questions[tag.name].append(question.id)
                else:
                    tagged_questions[tag.name] = [question.id]

        for t in sorted(tagged_questions.keys()):
            print(t)
            res = process.extract(t, choices, scorer=fuzz.token_sort_ratio, limit=3)
            if res and res[0][1] > 80:
                matches.write('{} , "{}", {}\n'.format(t, res, ' '.join([str(t) for t  in tagged_questions[t]])))
            else:
                unmatches.write('{} , "{}", {}\n'.format(t, res, ' '.join([str(t) for t in tagged_questions[t]])))