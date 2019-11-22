from masteraula.questions.models import Topic

all_topics = { topic.id:topic for topic in Topic.objects.prefetch_related('question_set') }
next_topics = [topic.id for topic in Topic.objects.filter(childs__isnull=True).filter(discipline__id=2)]

added = {}
while next_topics:
    curr = next_topics.pop(0)
    if curr in added:
        continue
        
    added[curr] = 1
    curr = all_topics[curr]

    if curr.parent:
        parent = all_topics[curr.parent_id]
        print('{} -> {}'.format(curr.name, parent.name))

        for question in curr.question_set.all():
            question.topics.add(parent)
            # print(question.id)

        next_topics.append(curr.parent_id)
    else:
        continue
