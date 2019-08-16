from django.db import models

class TopicManager(models.Manager):

    def max_depth(self):
        all_topics = self.all().select_related('parent')
        children_dict = {}

        for topic in all_topics:
            if topic.parent and topic.parent_id in children_dict:
                children_dict[topic.parent_id].append(topic)
            else:
                children_dict[topic.parent_id] = [topic]

        curr_nodes = self.filter(parent=None)
        depth = 0
        while curr_nodes:
            depth += 1
            new_nodes = []
            for node in curr_nodes:
                children = children_dict.get(node.id, [])
                if children:
                    new_nodes += children
            curr_nodes = new_nodes
        return depth


    def get_parents_tree(self, disciplines=None):
        depth = 3   # Hardcoded because whe already know the maximun depth of the tree
        # depth = self.max_depth()
        prefetch_args = []

        for i in range(depth):
            prefetch_args.append('__'.join(['childs'] * (i + 1)))
            prefetch_args.append('__'.join(['childs'] * i + ['discipline']))

        if disciplines:
            return self.filter(parent=None, discipline_id__in=disciplines).prefetch_related(*prefetch_args)
        return self.filter(parent=None).prefetch_related(*prefetch_args)


class QuestionManager(models.Manager):
    def get_list_questions(self, ):
        return self.filter(disabled=False).order_by('id').prefetch_related(
            'tags', 'alternatives', 'disciplines', 'teaching_levels', 'author',
            'learning_objects', 'learning_objects__tags',
            'topics', 'topics__discipline', 'topics__parent', 'topics__parent__discipline', 'topics__parent__parent', 'topics__parent__parent__discipline',
        )