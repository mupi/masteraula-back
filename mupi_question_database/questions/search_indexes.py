from haystack import indexes
from .models import Question
from django.utils import timezone
import re

class QuestionIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True,use_template=True)
    qustion_id = indexes.IntegerField(model_attr='pk')
    author = indexes.CharField(model_attr='author')
    create_date = indexes.DateTimeField(model_attr='create_date')
    level = indexes.CharField(model_attr='level')
    question_text = indexes.CharField(model_attr='question_text')
    text_auto = indexes.EdgeNgramField(model_attr='question_text')
    tags = indexes.MultiValueField()

    def get_model(self):
        return Question

    def index_queryset(self, using=None):
        """Used when the entire index for model is updated."""
        return self.get_model().objects.filter(create_date__lte=timezone.now())


    def prepare_question_text(self, obj):
        cleaner = re.compile('<.*?>')
        return re.sub(cleaner, '', obj.question_text)

    def prepare_level(self, obj):
        if obj.level == 'E':
            return 'Facil'
        elif obj.level == 'M':
            return 'Medio'
        elif obj.level == 'H':
            return 'Dificil'
        return ''

    def prepare_tags(self, obj):
        return [tag.name for tag in obj.tags.all()]
