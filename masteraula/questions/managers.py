from django.db import models

class TopicManager(models.Manager):

    def get_parents_tree_values(self, disciplines_ids=None):
        all_topics = self.all().select_related('parent')
        if disciplines_ids:
            all_topics = all_topics.filter(discipline__in=disciplines_ids).distinct()

        all_topics = all_topics.values()
        roots = []
        topics_dict = {}

        for topic in all_topics:
            topics_dict[topic['id']] = topic

        children_dict = {}
        for topic in all_topics:
            topic['childs'] = []
            if not topic['parent_id']:
                roots.append(topic)
            else:
                if topic['parent_id'] in children_dict:
                    children_dict[topic['parent_id']].append(topic)
                else:
                    children_dict[topic['parent_id']] = [topic]

        new_nodes = roots
        while new_nodes:
            curr_nodes = new_nodes
            new_nodes = []
            for root in curr_nodes:
                root['childs'] = children_dict.get(root['id'], [])
                new_nodes += root['childs']

        return roots
        