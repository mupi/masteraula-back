from django import forms
from django.utils.translation import ugettext_lazy as _

from haystack.query import SearchQuerySet

from ckeditor.widgets import CKEditorWidget

from haystack.forms import SearchForm

from .models import Question, Answer

class QuestionForm(forms.ModelForm):
    # question_header = forms.CharField(max_length=50, label='Titulo da questao')
    # question_text = forms.CharField(widget=CKEditorWidget(), label='Corpo da questao')
    # resolution = forms.CharField(widget=CKEditorWidget(), label='Resolucao esperada')
    #
    # level = forms.CharField(label='Level da questao')
    class Meta:
        model = Question
        fields = ('question_header', 'question_text', 'resolution', 'level')
        labels = {
            'question_header': _('Titulo da questao'),
            'question_text': _('Enunciado'),
            'resolution': _('Resolucao esperada'),
            'level': _('Dificuldade'),
        }
        widgets = {
            'question_header': forms.TextInput(attrs={'placeholder': 'ex.: Enem 2015'}),
            'question_header': forms.TextInput(attrs={'class': 'form-control'}),
            'level': forms.Select(attrs={'class': 'form-control'}),
            # 'question_text': forms.TextInput(attrs={'placeholder': 'ex.: Quanto da 2+2*2?'}),
            # 'resolution': forms.TextInput(attrs={'placeholder': 'ex.: 6. Era esperado que o aluno soubesse que a multiplicacao vem antes da adicao'}),
        }
        # help_texts = {
        #     'question_header': _('Coloque o titulo da questao. Exemplo: enem 2015'),
        #     'question_text': _('Enunciado da questao'),
        #     'resolution': _('A resolucao esperada pelo aluno, ou seja, a ordem logica passo-a-passo da resolucao da questao'),
        # }
        error_messages = {
            'question_header': {
                'max_length': _("This writer's name is too long."),
            },
        }


class AnswerForm(forms.ModelForm):
    # question_header = forms.CharField(max_length=50, label='Titulo da questao')
    # question_text = forms.CharField(widget=CKEditorWidget(), label='Corpo da questao')
    # resolution = forms.CharField(widget=CKEditorWidget(), label='Resolucao esperada')
    #
    # level = forms.CharField(label='Level da questao')
    class Meta:
        model = Answer
        fields = ('answer_text', 'is_correct')
        labels = {
            'answer_text': _('Resposta'),
            'is_correct': _('Correto?'),
        }
        # widgets = {
        #     'question_header': forms.TextInput(attrs={'placeholder': 'ex.: Enem 2015'}),
        #     'question_header': forms.TextInput(attrs={'class': 'form-control'}),
        #     'level': forms.Select(attrs={'class': 'form-control'}),
            # 'question_text': forms.TextInput(attrs={'placeholder': 'ex.: Quanto da 2+2*2?'}),
            # 'resolution': forms.TextInput(attrs={'placeholder': 'ex.: 6. Era esperado que o aluno soubesse que a multiplicacao vem antes da adicao'}),
        # }
        # help_texts = {
        #     'question_header': _('Coloque o titulo da questao. Exemplo: enem 2015'),
        #     'question_text': _('Enunciado da questao'),
        #     'resolution': _('A resolucao esperada pelo aluno, ou seja, a ordem logica passo-a-passo da resolucao da questao'),
        # }
        # error_messages = {
        #     'question_header': {
        #         'max_length': _("This writer's name is too long."),
        #     },
        # }

class QuestionSearchForm(SearchForm):

    def no_query_found(self):
        self.query = True
        return self.searchqueryset.all()

class QuestionTagSearchForm(SearchForm):
    tags = forms.CharField(required=False)

    def search(self):
        sqs = SearchQuerySet().models(Question).order_by('create_date')

        if not self.is_valid():
            return self.no_query_found()

        if self.cleaned_data['tags']:
            sqs = sqs.filter(tags__in=self.cleaned_data['tags'].split(' '))

        return sqs
