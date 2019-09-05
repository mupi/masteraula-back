from django.db.models import Q
from .views import DisciplineReportsBaseView, prepare_texts_data
from . import report_functions

from masteraula.questions.models import LearningObject, Discipline

class ObjectsAllFilter(DisciplineReportsBaseView):
    template_name = 'reports/edit_object_text.html'
    header = 'Todas as detecções'

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        disciplines = request.POST.getlist('disciplines',[])
        
        if disciplines:
            learning_objects = LearningObject.objects.filter(text__isnull=False) \
                .filter(questions__disciplines__in=disciplines).distinct().order_by('id')
        if disciplines and learning_objects.count() > 0:
            ids, texts = zip(*[(lo.id, lo.text) for lo in learning_objects])
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

        learning_objects = LearningObject.objects.filter(id__in=ids).order_by('id')
        if learning_objects.count() > 0:
            ids, texts = zip(*[(lo.id, lo.text) for lo in learning_objects])

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


class ObjectsWithDivView(DisciplineReportsBaseView):
    template_name = 'reports/edit_object_text.html'
    header = 'Objetos com <div>'

    def queryset(self, disciplines):
        learning_objects = LearningObject.objects.filter(text__isnull=False).filter(text__contains='<div') \
            .filter(questions__disciplines__in=disciplines).distinct().order_by('id')
        if learning_objects.count() > 0:
            return zip(*[(lo.id, lo.text) for lo in learning_objects])
        return None

    def report_function(self, *args, **kwargs):
        return report_functions.process_tags_div(*args, **kwargs)


class ObjectsWithTextoAssociado(DisciplineReportsBaseView):
    template_name = 'reports/edit_object_text.html'
    header = 'Objetos com texto associado'

    def queryset(self, disciplines):
        learning_objects = LearningObject.objects.filter(text__isnull=False).filter(text__contains='texto_associado_questao') \
            .filter(questions__disciplines__in=disciplines).distinct().order_by('id')
        if learning_objects.count() > 0:
            return zip(*[(lo.id, lo.text) for lo in learning_objects])
        return None

    def report_function(self, *args, **kwargs):
        return report_functions.process_tags_texto_associado_inside_p(*args, **kwargs)


class ObjectsWithBrInsideP(DisciplineReportsBaseView):
    template_name = 'reports/edit_object_text.html'
    header = 'Objetos com <br> dentro de <p>'
    
    def queryset(self, disciplines):
        learning_objects = LearningObject.objects.filter(text__isnull=False).filter(text__contains='br') \
                    .filter(questions__disciplines__in=disciplines).distinct().order_by('id')
        if learning_objects.count() > 0:
            return zip(*[(lo.id, lo.text) for lo in learning_objects])
        return None

    def report_function(self, *args, **kwargs):
        return report_functions.process_tags_br_inside_p(*args, **kwargs)


class ObjectsWithEmptyP(DisciplineReportsBaseView):
    template_name = 'reports/edit_object_text.html'
    header = 'Objetos com tags <p> vazias'

    def queryset(self, disciplines):
        learning_objects = LearningObject.objects.filter(text__isnull=False) \
            .filter(questions__disciplines__in=disciplines).distinct().order_by('id')
        if learning_objects.count() > 0:
            return zip(*[(lo.id, lo.text) for lo in learning_objects])
        return None

    def report_function(self, *args, **kwargs):
        return report_functions.process_empty_p_tags(*args, **kwargs)


class ObjectsWithBoldItalic(DisciplineReportsBaseView):
    template_name = 'reports/edit_object_text.html'
    header = 'Objetos com tag <strong> ou <em>'

    def queryset(self, disciplines):
        learning_objects = LearningObject.objects.filter(text__isnull=False).filter(text__contains='font') \
            .filter(questions__disciplines__in=disciplines).distinct().order_by('id')
        if learning_objects.count() > 0:
            return zip(*[(lo.id, lo.text) for lo in learning_objects])
        return None

    def report_function(self, *args, **kwargs):
        return report_functions.process_bold_italic(*args, **kwargs)


class ObjectsWithSupSub(DisciplineReportsBaseView):
    template_name = 'reports/edit_object_text.html'
    header = 'Objetos com tag <sup> ou <sub>'

    def queryset(self, disciplines):
        learning_objects = LearningObject.objects.filter(text__isnull=False).filter(text__contains='vertical-align') \
            .filter(questions__disciplines__in=disciplines).distinct().order_by('id')
        if learning_objects.count() > 0:
            return zip(*[(lo.id, lo.text) for lo in learning_objects])
        return None

    def report_function(self, *args, **kwargs):
        return report_functions.process_super_sub(*args, **kwargs)


class ObjectsWithLineHeight(DisciplineReportsBaseView):
    template_name = 'reports/edit_object_text.html'
    header = 'Objetos com tag <sup> ou <sub>'

    def queryset(self, disciplines):
        learning_objects = LearningObject.objects.filter(text__isnull=False).filter(text__contains='lineheigth') \
            .filter(questions__disciplines__in=disciplines).distinct().order_by('id')
        if learning_objects.count() > 0:
            return zip(*[(lo.id, lo.text) for lo in learning_objects])
        return None

    def report_function(self, *args, **kwargs):
        return report_functions.process_line_heigth(*args, **kwargs)


class ObjectsWithPInsideP(DisciplineReportsBaseView):
    template_name = 'reports/edit_object_text.html'
    header = 'Objetos com tag <p> dentro de <p>'

    def queryset(self, disciplines):
        learning_objects = LearningObject.objects.filter(text__isnull=False) \
            .filter(questions__disciplines__in=disciplines).distinct().order_by('id')
        if learning_objects.count() > 0:
            return zip(*[(lo.id, lo.text) for lo in learning_objects])
        return None

    def report_function(self, *args, **kwargs):
        return report_functions.process_tags_p_inside_p(*args, **kwargs)


class ObjectsTagsPSpace(DisciplineReportsBaseView):
    template_name = 'reports/edit_object_text.html'
    header = 'Tags <p> sem espaço'

    def queryset(self, disciplines):
        learning_objects = LearningObject.objects.filter(text__isnull=False).filter(text__contains='</p><p>') \
            .filter(questions__disciplines__in=disciplines).distinct().order_by('id')
        if learning_objects.count() > 0:
            return zip(*[(lo.id, lo.text) for lo in learning_objects])
        return None

    def report_function(self, *args, **kwargs):
        return report_functions.process_tags_p_space(*args, **kwargs)