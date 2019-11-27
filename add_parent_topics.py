from masteraula.questions.models import Topic

topics = [t for t in Topic.objects.filter(childs__isnull=True).prefetch_related('question_set').select_related('parent')]

added = {}
while topics:
    next_topics = []
    while topics:
        curr = topics.pop(0)
        if curr.id in added:
            continue
            
        added[curr.id] = 1

        if curr.parent:
            print('{} -> {}'.format(curr.name, curr.parent.name))

            for question in curr.question_set.all():
                question.topics.add(curr.parent)
                # print(question.id)
            next_topics.append(curr.parent_id)

    print('-' * 10)
    next_topics = list(set(next_topics))
    print(next_topics)
    topics = [t for t in Topic.objects.filter(id__in=next_topics).prefetch_related('parent__question_set').select_related('parent')]