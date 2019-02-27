from django.apps import AppConfig


class QuestionsConfig(AppConfig):
    name = 'masteraula.questions'

    def ready(self):
        import masteraula.questions.signals