from django.db import models
from django.db.models import Prefetch

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
        prefetchs = [Prefetch('childs', queryset=self.select_related('discipline'))]

        for i in range(depth):
            prefetchs.append(Prefetch('childs', queryset=self.select_related('discipline').prefetch_related(prefetchs[-1])))

        if disciplines:
            return self.filter(parent=None, discipline_id__in=disciplines).prefetch_related(prefetchs[-1])
        return self.filter(parent=None).prefetch_related(prefetchs[-1])