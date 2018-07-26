from allauth.account import app_settings as allauth_settings
from allauth.utils import (email_address_exists,get_username_max_length)
from allauth.account.adapter import get_adapter
from allauth.account.utils import setup_user_email

from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.utils.text import slugify

from drf_haystack.serializers import HaystackSerializer, HaystackSerializerMixin

from rest_auth.registration import serializers as auth_register_serializers
from rest_auth import serializers as auth_serializers

from rest_framework import serializers, exceptions

from taggit.models import Tag

from masteraula.users.models import User, Profile
from masteraula.users.serializers import UserDetailsSerializer

from .models import (Discipline, TeachingLevel, LearningObject, Descriptor, Question,
                     Alternative, DocumentHeader, Document, DocumentQuestion)

# from .search_indexes import QuestionIndex, TagIndex

class TagListSerializer(serializers.Field):
    '''
    TagListSerializer para tratar o App taggit, ja que nao possui suporte para
    rest_framework
    '''
    def to_internal_value(self, data):
        if  type(data) is list:
            return data
        try:
            taglist = ast.literal_eval(data)
            return taglist
        except BaseException as e:
            raise serializers.ValidationError("expected a list of data")


    def to_representation(self, obj):
        if type(obj) is not list:
            return [{'name' : tag.name} for tag in obj.all()]
        return obj

class DisciplineSerialzier(serializers.ModelSerializer):
    class Meta:
        model = Discipline
        fields = (
            'id',
            'name'
        )

class TeachingLevelSerializer(serializers.ModelSerializer):
    class Meta:
        model = TeachingLevel
        fields = (
            'id',
            'name'
        )

class DescriptorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Descriptor
        fields = (
            'id',
            'name',
            'description'
        )

class AlternativeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Alternative
        fields = (
            'id',
            'text',
            'is_correct'
        )

class QuestionSerializer(serializers.ModelSerializer):
    author = UserDetailsSerializer(read_only=False)
    create_date = serializers.DateField(format="%Y/%m/%d", required=False, read_only=True)
    
    # alternatives = AlternativeSerializer(many=True, read_only=False)
    
    # disciplines = DisciplineSerialzier(read_only=False, many=True)
    # descriptors = DescriptorSerializer(read_only=False, many=True)
    # teaching_levels = TeachingLevelSerializer(read_only=False, many=True)
    
    tags = TagListSerializer(read_only=False)

    class Meta:
        model = Question
        fields = (
            'id',
            'author',
            'create_date',

            'statement',
            'learning_object',
            'resolution',
            'difficulty',
            'alternatives',

            'disciplines',
            'descriptors',
            'teaching_levels',
            'year',
            'source',

            'credit_cost',

            'tags',
        )
        depth = 1

class DocumentQuestionSerializer(serializers.ModelSerializer):

    class Meta:
        model = DocumentQuestion
        fields = (
            'question',
            'document',
            'order'
        )
        extra_kwargs = {
            'document' : { 'read_only' : True }
        }


class DocumentSerializer(serializers.ModelSerializer):
    questions = DocumentQuestionSerializer(many=True)

    class Meta:
        model = Document
        fields = (
            'name',
            'owner',
            'questions',
            'create_date',
            'secret',
            'document_header'
        )

class DocumentListSerializer(serializers.ModelSerializer):
    questions = DocumentQuestionSerializer(many=True, source='documentquestion_set')

    class Meta:
        model = Document
        fields = (
            'name',
            'owner',
            'questions',
            'create_date',
            'secret',
            'document_header'
        )

class DocumentCreateSerializer(serializers.ModelSerializer):
    questions = DocumentQuestionSerializer(many=True, source='documentquestion_set')

    class Meta:
        model = Document
        fields = (
            'name',
            'questions',
            'create_date',
            'secret',
            'document_header'
        )

    def validate_questions(self, value):
        documentQuestions = sorted(value, key=lambda k: k['order'])
        documentQuestions = [{'question' : dc['question'], 'order' : order} for order, dc in enumerate(documentQuestions)]
        return documentQuestions

    def create(self, validated_data):
        documentQuestions = validated_data.pop('documentquestion_set')
        document = Document.objects.create(**validated_data)

        for documentQuestion in documentQuestions:
            document.documentquestion_set.create(**documentQuestion)

        return document

# class ProfileSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Profile
#         fields = (
#             'credit_balance',
#         )

# class UserBasicSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = User
#         fields = (
#             # 'url',
#             'id',
#             'username',
#             'name',
#         )

# class UserSerializer(serializers.ModelSerializer):
#     # url = serializers.HyperlinkedIdentityField(view_name='masteraula:users-detail')

#     class Meta:
#         model = User
#         fields = (
#             # 'url',
#             'id',
#             'username',
#             'name',
#             'email',
#             'password'
#         )
#         extra_kwargs = {'password': {'write_only': True, 'required' : True},
#                         'username': {'required' : False}}

#     def create(self, validated_data):
#         user = User(username=validated_data['username'],
#                     name=validated_data['name'],
#                     email=validated_data['email'])
#         user.set_password(validated_data['password'])
#         user.save()

#         Profile.objects.create(user=user)

#         return user

# class UserProfileSerializer(serializers.ModelSerializer):
#     # url = serializers.HyperlinkedIdentityField(view_name='masteraula:users-detail')
#     profile = ProfileSerializer(read_only=True)

#     class Meta:
#         model = User
#         fields = (
#             # 'url',
#             'id',
#             'username',
#             'name',
#             'email',
#             'profile'
#         )
#         extra_kwargs = {'profile' : {'read_only' : True},
#                         'username': {'read_only' : True}}

# class UserUpdateSerializer(serializers.Serializer):
#     password = serializers.CharField(max_length=200)
#     name = serializers.CharField(max_length=200)
#     email = serializers.EmailField()

# class PasswordSerializer(serializers.Serializer):
#     password = serializers.CharField(max_length=200)
#     previous_password = serializers.CharField(max_length=200)

# class AnswerSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Answer
#         fields = (
#             'id',
#             'answer_text',
#             'is_correct'
#         )
#         extra_kwargs =  {'id': {'read_only': False, 'required' : False},
#                         'answer_text' : {'required' : True},
#                         'is_correct' : {'required' : True}
#                         }

# class SubjectSerializer(serializers.ModelSerializer):
#     slug = serializers.SerializerMethodField('slugify_subject')

#     def slugify_subject(self, subject):
#         return slugify(subject.subject_name)

#     class Meta:
#         model = Subject
#         fields = (
#             'id',
#             'subject_name',
#             'slug'
#         )
#         extra_kwargs =  {'subject_name': {'read_only': True},
#                         'id': {'read_only': False, 'required' : False},
#                         }

# class QuestionBasicSerializer(serializers.ModelSerializer):
#     subjects = SubjectSerializer(many=True, read_only=False)
#     tags = TagListSerializer(read_only=False)
#     author = UserSerializer(read_only=True)
#     # url = serializers.HyperlinkedIdentityField(view_name='masteraula:questions-detail')

#     class Meta:
#         model = Question
#         fields = (
#             # 'url',
#             'id',
#             'question_statement',
#             'level',
#             'author',
#             'create_date',
#             'credit_cost',
#             'tags',
#             'subjects',
#             'education_level',
#             'year',
#             'source'
#         )

# class QuestionSerializer(serializers.ModelSerializer):
#     question_parent = QuestionBasicSerializer(read_only=True)
#     answers = AnswerSerializer(many=True, read_only=False)
#     subjects = SubjectSerializer(many=True, read_only=False)
#     tags = TagListSerializer(read_only=False)
#     author = UserSerializer(read_only=True)
#     question_lists = serializers.SerializerMethodField('question_lists_serializer')
#     related_questions = serializers.SerializerMethodField('related_question_serializer')

#     def question_lists_serializer(self, question):
#        question_list_ids = [qql.question_list_id for qql in QuestionQuestion_List.objects.filter(question=question).order_by('question_list_id')]
#        return Question_ListBasicSerializer(Question_List.objects.filter(id__in=question_list_ids), many=True).data

#     def related_question_serializer(self, question):
#        question_children_ids = [q.id for q in Question.objects.filter(question_parent=question)]
#        question_siblings_ids = [q.id for q in Question.objects.filter(question_parent=question.question_parent)] if question.question_parent != None else []
#        if len(question_siblings_ids) > 0:
#            question_siblings_ids.remove(question.id)
#        return QuestionBasicSerializer(Question.objects.filter(id__in=question_siblings_ids+question_children_ids), many=True).data

#     class Meta:
#         model = Question
#         fields = (
#             # 'url',
#             'id',
#             'question_parent',
#             'question_statement',
#             'resolution',
#             'level',
#             'author',
#             'create_date',
#             'credit_cost',
#             'tags',
#             'answers',
#             'subjects',
#             'education_level',
#             'source',
#             'year',
#             'question_lists',
#             'related_questions'
#         )
#         extra_kwargs = {'tags': {'required' : True},
#                         'answers' : {'required' : True},
#                         'subjects' : {'required' : True}
#                         }

#     def validate_answers(self, value):
#         has_correct = False
#         error = None
#         for answer in value:
#             if answer['is_correct']:
#                 if has_correct:
#                     raise serializers.ValidationError('The question has two correct answers')
#                 has_correct = True

#         # Verifica se ha ao menos uma resposta correta
#         if not has_correct:
#             raise serializers.ValidationError('The question does not have any correct answer')

#         list_id = [answer['id'] for answer in value if 'id' in answer]
#         dblist_id = Answer.objects.filter(id__in=list_id)
#         if len(list_id) != len(dblist_id):
#             raise serializers.ValidationError('There is a answer with a new id that did not exist before')

#         return value

#     def create(self, validated_data):
#         tags = validated_data.pop('tags')
#         answers = validated_data.pop('answers')

#         question = Question.objects.create(question_statement=validated_data['question_statement'],
#                                             resolution=validated_data['resolution'],
#                                             level=validated_data['level'],
#                                             author=validated_data['author'])

#         for tag in tags:
#             question.tags.add(tag)

#         for answer in answers:
#             answer['id'] = None
#             new_answer = Answer.objects.create(question=question, **answer)
#             question.answers.add(new_answer)

#         # Adiciona a questoa a lista de disponiveis
#         author = question.author
#         author.profile.avaiable_questions.add(question)

#         # Atualiza o indice haystack
#         QuestionIndex().update_object(question)
#         return question

#     def update(self, instance, validated_data):
#         # Verifica se existe answer para partial_update (PATCH)
#         if 'answers' in validated_data:
#             answers = validated_data.pop('answers')

#             # Prepara listas para exclusao de respostas que nao fazem mais parte da pergunta
#             dbanswer = [answer.id for answer in list(instance.answers.all())]
#             answer_aux = [answer['id'] for answer in answers if 'id' in answer]
#             to_delete = list(set(dbanswer) - set(answer_aux))

#             # Deleta as respostas que nao estao mais sendo usadas
#             for id_answer in to_delete:
#                 removed_answer = Answer.objects.get(id=id_answer)
#                 removed_answer.delete()
#                 # instance.answers.remove(removed_answer)

#             # Atualiza as respostas
#             for answer in answers:
#                 if 'id' in answer:
#                     # Atualiza as questoes ja existentes
#                     dbanswer = Answer.objects.get(id=answer['id'])
#                     dbanswer.answer_text = answer['answer_text']
#                     dbanswer.is_correct = answer['is_correct']
#                     dbanswer.save()
#                 else:
#                     # Cria uma nova questao caso ela nao exista
#                     new_answer = Answer.objects.create(question=instance, **answer)
#                     instance.answers.add(new_answer)


#         # Verifica se existe tags para partial_update (PATCH)
#         if 'tags' in validated_data:
#             tags = validated_data.pop('tags')

#             # Cria lista para a criacao de novas tags e exclusao de tags que nao fazem mais parte
#             dbtags = [tag.name for tag in list(instance.tags.all())]
#             to_delete = list(set(dbtags) - set(tags))
#             to_create = list(set(tags) - set(dbtags))

#             for tag in to_create:
#                 instance.tags.add(tag)
#             for tag in to_delete:
#                 instance.tags.remove(tag)

#         # Verifica se existe subjects para partial_update (PATCH)
#         if 'subjects' in validated_data:
#             subjects =  validated_data.pop('subjects')
#             subjects =  [subject['id'] for subject in subjects]
#             # Cria lista para a criacao de novas tags e exclusao de tags que nao fazem mais parte
#             dbsubjects = [subject.id for subject in list(instance.subjects.all())]

#             to_delete = list(set(dbsubjects) - set(subjects))
#             to_create = list(set(subjects) - set(dbsubjects))

#             for subject_id in to_create:
#                 subject = Subject.objects.get(id=subject_id)
#                 instance.subjects.add(subject)
#             for subject_id in to_delete:
#                 subject = Subject.objects.get(id=subject_id)
#                 instance.subjects.remove(subject)

#         # Atualiza o indice haystack
#         QuestionIndex().update_object(instance)

#         return super().update(instance, validated_data)

# class QuestionOrderSerializer(serializers.ModelSerializer):
#     question = serializers.PrimaryKeyRelatedField(read_only=False, queryset=Question.objects.all())

#     class Meta:
#         model = QuestionQuestion_List
#         fields = (
#             'question',
#             'order',
#         )f

#     def create(self, validated_data):
#         question = validated_data.pop('question')

# class QuestionOrderDetailSerializer(serializers.ModelSerializer):
#     question = QuestionSerializer(read_only=False)

#     class Meta:
#         model = QuestionQuestion_List
#         fields = (
#             'question',
#             'order',
#         )

#     def create(self, validated_data):
#         question = validated_data.pop('question')

# class Question_ListDetailSerializer(serializers.ModelSerializer):
#     questions = QuestionOrderDetailSerializer(many=True, source='questionquestion_list_set', read_only=False)
#     owner = UserSerializer(read_only=False)
#     question_count = serializers.SerializerMethodField('count_questions')

#     def count_questions(self, question_list):
#         return len(question_list.questions.all())

#     class Meta:
#         model = Question_List
#         fields = (
#             # 'url',
#             'id',
#             'owner',
#             'question_list_header',
#             'secret',
#             'create_date',
#             # 'cloned_from',
#             'questions',
#             'question_count'
#         )
#         extra_kwargs = {'cloned_from': {'required' : False},
#                         'author' : {'required' : False}}

# class Question_ListBasicSerializer(serializers.ModelSerializer):
#     owner = UserSerializer(read_only=False)
#     question_count = serializers.SerializerMethodField('count_questions')

#     def count_questions(self, subject):
#         return len(subject.questions.all())

#     class Meta:
#         model = Question_List
#         fields = (
#             'id',
#             'owner',
#             'question_list_header',
#             'secret',
#             'create_date',
#             'question_count'
#         )
#         extra_kwargs = {'author' : {'required' : False}}

# class Question_ListSerializer(serializers.ModelSerializer):
#     questions = QuestionOrderSerializer(many=True, source='questionquestion_list_set', read_only=False)
#     owner = serializers.PrimaryKeyRelatedField(read_only=False, queryset=User.objects.all())

#     class Meta:
#         model = Question_List
#         fields = (
#             # 'url'
#             'id',
#             'owner',
#             'question_list_header',
#             'secret',
#             'create_date',
#             # 'cloned_from',
#             'questions'
#         )
#         extra_kwargs = {'cloned_from': {'required' : False},
#                         'author' : {'required' : False}}

#     def validate_questions(self, value):
#         questions_order = sorted(value, key=lambda k: k['order'])
#         questions_id = []

#         # Verifica a ordem da lista de ordens
#         expected = 1
#         for question_order in questions_order:
#             if question_order['order'] != expected:
#                 raise serializers.ValidationError('Invalid questions order')
#             expected = expected + 1
#             questions_id.append(question_order['question'])

#         if (len(questions_id) != len(set(questions_id))):
#             raise serializers.ValidationError('Duplicate question in the list')


#         return value

#     def validate(self, attrs):
#         owner = attrs.get('owner')
#         question_orders = attrs.get('questionquestion_list_set')

#         msg = None

#         for question_order in question_orders:
#             question = question_order.get('question')
#             # if question not in owner.profile.avaiable_questions.all():
#             #     msg = _('The question with id ' + str(question.id) + ' is not avaiable for this user')

#         if msg:
#             raise exceptions.ValidationError(msg)

#         return attrs

#     def create(self, validated_data):
#         if 'questionquestion_list_set' in validated_data:
#             questions_order = validated_data.pop('questionquestion_list_set')
#             questions_order = sorted(questions_order, key=lambda k: k['order'])

#         new_list = Question_List.objects.create(**validated_data)

#         for question_order in questions_order:
#             QuestionQuestion_List.objects.create(question_list=new_list, **question_order)
#         return new_list

#     def update(self, instance, validated_data):
#         if 'questionquestion_list_set' in validated_data:
#             questions_order = validated_data.pop('questionquestion_list_set')
#             questions_order = sorted(questions_order, key=lambda k: k['order'])

#             questions_ids = [item['question'].id for item in questions_order]

#             for question in instance.questions.all():
#                 # Apaga as questoes que sumiram da lista
#                 if question.id not in questions_ids:
#                     QuestionQuestion_List.objects.get(question=question.id,question_list=instance).delete()

#             for question_order in questions_order:
#                 try:
#                     # Se somente trocou a ordem (ou seja, o objeto ja existia)
#                     question = QuestionQuestion_List.objects.get(question=question_order['question'],question_list=instance)
#                     question.order = question_order['order']
#                     question.save()
#                 except:
#                     # Se for para criar um novo par
#                     QuestionQuestion_List.objects.create(question_list=instance, **question_order)

#         return super().update(instance, validated_data)

# class TagSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Tag
#         fields = ['name', 'slug']

# class QuestionSearchSerializer(HaystackSerializerMixin, QuestionSerializer):

#     class Meta(QuestionSerializer.Meta):
#         search_fields = [
#             'text',
#         ]
#         field_aliases = []
#         exclude = []
#         ignore_fields = ['text']

# class TagSearchSerializer(HaystackSerializer):
#     class Meta:
#         index_classes = [TagIndex]
#         fields = ['name', 'slug', 'tags_auto']
#         ignore_fields = ['tags_auto']
#         field_aliases = {
#             'q': 'tags_auto'
#         }