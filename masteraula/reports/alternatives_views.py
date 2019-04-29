from .views import DisciplineReportsBaseView, prepare_texts_data
from . import report_functions

from masteraula.questions.models import Alternative, Discipline

class AlternativesAllFilter(DisciplineReportsBaseView):
    template_name = 'reports/edit_alternative_text.html'
    header = 'Todas as detecções'

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        disciplines = request.POST.getlist('disciplines',[])
        
        if disciplines:
            alternatives = Alternative.objects.filter(question__disciplines__in=disciplines).distinct().order_by('id')
        if alternatives.count() > 0:
            ids, texts = zip(*[(a.id, a.text) for a in alternatives])
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
            report_functions.process_empty_p_tags
        ]
        all_res = [func(ids, texts) for func in all_res]
        ids = list(set([item for sublist, _, _ in all_res for item in sublist]))

        if not ids:
            return super().render_to_response(context)

        alternatives = Alternative.objects.filter(id__in=ids).order_by('id')
        if alternatives.count() > 0:
            ids, texts = zip(*[(a.id, a.text) for a in alternatives])

        functions = [
            report_functions.process_tags_div,
            report_functions.process_tags_br_inside_p, 
            report_functions.process_tags_texto_associado_inside_p,
            report_functions.process_bold_italic,
            report_functions.process_super_sub,
            report_functions.process_line_heigth,
            report_functions.process_tags_p_inside_p,
            report_functions.process_empty_p_tags
        ]

        clean = texts
        all_status = []
        for f in functions:
            _, _, clean, status = f(ids, clean, True, True)
            all_status.append(status)

        context['data'] = prepare_texts_data(ids, texts, clean, list(zip(*all_status)))

        return super().render_to_response(context)



class AlternativesWithDivView(DisciplineReportsBaseView):
    template_name = 'reports/edit_alternative_text.html'
    header = 'Alternativas com <div>'

    def queryset(self, disciplines):
        alternatives = Alternative.objects.filter(text__contains='<div').filter(question__disciplines__in=disciplines).distinct().order_by('id')
        if alternatives.count() > 0:
            return zip(*[(a.id, a.text) for a in alternatives])
        return None

    def report_function(self, *args, **kwargs):
        return report_functions.process_tags_div(*args, **kwargs)

class AlternativesWithTextoAssociado(DisciplineReportsBaseView):
    template_name = 'reports/edit_alternative_text.html'
    header = 'Alternativas com texto associado'

    def queryset(self, disciplines):
        alternatives = Alternative.objects.filter(text__contains='texto_associado_questao').filter(question__disciplines__in=disciplines).distinct().order_by('id')
        if alternatives.count() > 0:
            return zip(*[(a.id, a.text) for a in alternatives])
        return None

    def report_function(self, *args, **kwargs):
        return report_functions.process_tags_texto_associado_inside_p(*args, **kwargs)

class AlternativesWithBrInsideP(DisciplineReportsBaseView):
    template_name = 'reports/edit_alternative_text.html'
    header = 'Alternativas com <br> dentro de <p>'
    
    def queryset(self, disciplines):
        alternatives = Alternative.objects.filter(text__contains='br').filter(question__disciplines__in=disciplines).distinct().order_by('id')
        if alternatives.count() > 0:
            return zip(*[(a.id, a.text) for a in alternatives])
        return None

    def report_function(self, *args, **kwargs):
        return report_functions.process_tags_br_inside_p(*args, **kwargs)

class AlternativesWithEmptyP(DisciplineReportsBaseView):
    template_name = 'reports/edit_alternative_text.html'
    header = 'Alternativas com tags <p> vazias'

    def queryset(self, disciplines):
        alternatives = Alternative.objects.filter(question__disciplines__in=disciplines).distinct().order_by('id')
        if alternatives.count() > 0:
            return zip(*[(a.id, a.text) for a in alternatives])
        return None

    def report_function(self, *args, **kwargs):
        return report_functions.process_empty_p_tags(*args, **kwargs)


class AlternativesWithBoldItalic(DisciplineReportsBaseView):
    template_name = 'reports/edit_alternative_text.html'
    header = 'Alternativas com tag <strong> ou <em>'

    def queryset(self, disciplines):
        alternatives = Alternative.objects.filter(text__contains='font').filter(question__disciplines__in=disciplines).distinct().order_by('id')
        if alternatives.count() > 0:
            return zip(*[(a.id, a.text) for a in alternatives])
        return None

    def report_function(self, *args, **kwargs):
        return report_functions.process_bold_italic(*args, **kwargs)


class AlternativesWithSupSub(DisciplineReportsBaseView):
    template_name = 'reports/edit_alternative_text.html'
    header = 'Alternativas com tag <sup> ou <sub>'

    def queryset(self, disciplines):
        alternatives = Alternative.objects.filter(text__contains='vertical-align').filter(question__disciplines__in=disciplines).distinct().order_by('id')
        if alternatives.count() > 0:
            return zip(*[(a.id, a.text) for a in alternatives])
        return None

    def report_function(self, *args, **kwargs):
        return report_functions.process_super_sub(*args, **kwargs)


class AlternativesWithLineHeight(DisciplineReportsBaseView):
    template_name = 'reports/edit_alternative_text.html'
    header = 'Alternativas com tag <sup> ou <sub>'

    def queryset(self, disciplines):
        alternatives = Alternative.objects.filter(text__contains='lineheigth').filter(question__disciplines__in=disciplines).distinct().order_by('id')
        if alternatives.count() > 0:
            return zip(*[(a.id, a.text) for a in alternatives])
        return None

    def report_function(self, *args, **kwargs):
        return report_functions.process_line_heigth(*args, **kwargs)

class AlternativesWithPInsideP(DisciplineReportsBaseView):
    template_name = 'reports/edit_alternative_text.html'
    header = 'Alternativas com tag <p> dentro de <p>'

    def queryset(self, disciplines):
        alternatives = Alternative.objects.filter(question__disciplines__in=disciplines).distinct().order_by('id')
        if alternatives.count() > 0:
            return zip(*[(a.id, a.text) for a in alternatives])
        return None

    def report_function(self, *args, **kwargs):
        return report_functions.process_tags_p_inside_p(*args, **kwargs)