from .views import DisciplineReportsBaseView, prepare_texts_data
from . import report_functions

from masteraula.questions.models import Question, Discipline

class StatementsAllFilter(DisciplineReportsBaseView):
    template_name = 'reports/edit_question_statement.html'
    header = 'Todas as detecções'

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        disciplines = request.POST.getlist('disciplines',[])
        
        if disciplines:
            questions = Question.objects.filter(disciplines__in=disciplines).order_by('id')
        if disciplines and questions.count() > 0:
            ids, texts = zip(*[(q.id, q.statement) for q in questions])
        else:
            return super().render_to_response(context)
        
        all_res = [
            report_functions.process_tags_div,
            report_functions.process_tags_br_inside_p,
            report_functions.process_tags_texto_associado_inside_p,
            report_functions.process_bold_italic,
            report_functions.process_super_sub,
            report_functions.process_line_heigth,
            report_functions.process_tags_p_inside_p,
            report_functions.process_empty_p_tags,
            report_functions.process_tags_p_space
        ]
        all_res = [func(ids, texts) for func in all_res]
        ids = list(set([item for sublist, _, _ in all_res for item in sublist]))

        if not ids:
            return super().render_to_response(context)

        questions = Question.objects.filter(id__in=ids).order_by('id')
        if questions.count() > 0:
            ids, texts = zip(*[(q.id, q.statement) for q in questions])

        functions = [
            report_functions.process_tags_div,
            report_functions.process_tags_br_inside_p, 
            report_functions.process_tags_texto_associado_inside_p,
            report_functions.process_bold_italic,
            report_functions.process_super_sub,
            report_functions.process_line_heigth,
            report_functions.process_tags_p_inside_p,
            report_functions.process_empty_p_tags,
            report_functions.process_tags_p_space
        ]

        clean = texts
        all_status = []
        for f in functions:
            _, _, clean, status = f(ids, clean, True, True)
            all_status.append(status)

        context['data'] = prepare_texts_data(ids, texts, clean, list(zip(*all_status)))

        return super().render_to_response(context)

class StatementsWithDivView(DisciplineReportsBaseView):
    template_name = 'reports/edit_question_statement.html'
    header = 'Questões com <div>'

    def queryset(self, disciplines):
        questions =  Question.objects.filter(disciplines__in=disciplines).filter(statement__contains='<div').order_by('id')
        if questions.count() > 0:
            return zip(*[(q.id, q.statement) for q in questions])
        return None

    def report_function(self, *args, **kwargs):
        return report_functions.process_tags_div(*args, **kwargs)

class StatementsWithTextoAssociado(DisciplineReportsBaseView):
    template_name = 'reports/edit_question_statement.html'
    header = 'Questões com texto associado'

    def queryset(self, disciplines):
        questions = Question.objects.filter(disciplines__in=disciplines).filter(statement__contains='texto_associado_questao').order_by('id')
        if questions.count() > 0:
            return zip(*[(q.id, q.statement) for q in questions])
        return None

    def report_function(self, *args, **kwargs):
        return report_functions.process_tags_texto_associado_inside_p(*args, **kwargs)

class StatementsWithBrInsideP(DisciplineReportsBaseView):
    template_name = 'reports/edit_question_statement.html'
    header = 'Questões com tag <br> dentro de <p>'

    def queryset(self, disciplines):
        questions = Question.objects.filter(disciplines__in=disciplines).filter(statement__contains='br').order_by('id')
        if questions.count() > 0:
            return zip(*[(q.id, q.statement) for q in questions])
        return None

    def report_function(self, *args, **kwargs):
        return report_functions.process_tags_br_inside_p(*args, **kwargs)

class StatementsWithEmptyP(DisciplineReportsBaseView):
    template_name = 'reports/edit_question_statement.html'
    header = 'Questões com tags <p> vazias'

    def queryset(self, disciplines):
        questions = Question.objects.filter(disciplines__in=disciplines).order_by('id')
        if questions.count() > 0:
            return zip(*[(q.id, q.statement) for q in questions])
        return None

    def report_function(self, *args, **kwargs):
        return report_functions.process_empty_p_tags(*args, **kwargs)


class StatementsWithBoldItalic(DisciplineReportsBaseView):
    template_name = 'reports/edit_question_statement.html'
    header = 'Questões com tag <strong> ou <em>'

    def queryset(self, disciplines):
        questions = Question.objects.filter(disciplines__in=disciplines).filter(statement__contains='font').order_by('id')
        if questions.count() > 0:
            return zip(*[(q.id, q.statement) for q in questions])
        return None

    def report_function(self, *args, **kwargs):
        return report_functions.process_bold_italic(*args, **kwargs)


class StatementsWithSupSub(DisciplineReportsBaseView):
    template_name = 'reports/edit_question_statement.html'
    header = 'Questões com tag <sup> ou <sub>'

    def queryset(self, disciplines):
        questions = Question.objects.filter(disciplines__in=disciplines).filter(statement__contains='vertical-align').order_by('id')
        if questions.count() > 0:
            return zip(*[(q.id, q.statement) for q in questions])
        return None

    def report_function(self, *args, **kwargs):
        return report_functions.process_super_sub(*args, **kwargs)


class StatementsWithLineHeight(DisciplineReportsBaseView):
    template_name = 'reports/edit_question_statement.html'
    header = 'Questões com tag <sup> ou <sub>'

    def queryset(self, disciplines):
        questions = Question.objects.filter(disciplines__in=disciplines).filter(statement__contains='line-heigth').order_by('id')
        if questions.count() > 0:
            return zip(*[(q.id, q.statement) for q in questions])
        return None

    def report_function(self, *args, **kwargs):
        return report_functions.process_line_heigth(*args, **kwargs)

class StatementsWithPInsideP(DisciplineReportsBaseView):
    template_name = 'reports/edit_question_statement.html'
    header = 'Questões com tag <p> dentro de <p>'

    def queryset(self, disciplines):
        questions = Question.objects.filter(disciplines__in=disciplines).order_by('id')
        if questions.count() > 0:
            return zip(*[(q.id, q.statement) for q in questions])
        return None

    def report_function(self, *args, **kwargs):
        return report_functions.process_tags_p_inside_p(*args, **kwargs)

class StatementsTagsPSpace(DisciplineReportsBaseView):
    template_name = 'reports/edit_question_statement.html'
    header = 'Questões com tags <p> sem espaço'

    def queryset(self, disciplines):
        questions = Question.objects.filter(disciplines__in=disciplines).filter(statement__contains='</p><p>').order_by('id')
        print(len(questions))
        if questions.count() > 0:
            return zip(*[(q.id, q.statement) for q in questions])
        return None

    def report_function(self, *args, **kwargs):
        return report_functions.process_tags_p_space(*args, **kwargs)