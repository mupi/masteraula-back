from django import template
from haystack.inputs import Clean
import unicodedata
import functools 

import unidecode
import re

connectives = [
	'abaixo', 'acima', 'adaptado', 'afirmar', 'alem', 'algmas', 'alguns', 'ali', 'alternativa', 'and', 'aos', 
	'apenas', 'apos', 'aquela', 'aquelas', 'aquele', 'aqueles', 'aqui', 'aquilo', 'aquilos', 'assim', 
	'assinale', 'ate', 'base', 'bem', 'boa', 'bom', 'cada', 'caso', 'certa', 'com', 
	'como', 'correta', 'correto', 'cuja', 'cujo', 'dada', 'dado', 'dai', 'dali', 'dando', 
	'daquela', 'daquelas', 'daquele', 'daqueles', 'daquilo', 'daquilos', 'dar', 'das', 'dava', 'dela', 
	'dele', 'demais', 'dentre', 'deram', 'desde', 'dessa', 'dessas', 'desse', 'desses', 'deu', 
	'deve', 'devia', 'disso', 'dissos', 'dos', 'ela', 'ele', 'entao', 'entre', 'entretanto', 
	'era', 'eram', 'essa', 'essas', 'esse', 'esses', 'esta', 'estao', 'estart', 'estas', 
	'estavam', 'este', 'estes', 'etc', 'exemplo', 'faz', 'fazendo', 'fez', 'fica', 'ficaram', 
	'ficou', 'fiz', 'fizeram', 'fizerem', 'foi', 'for', 'foram', 'havia', 'haviam', 'houve', 
	'houveram', 'htm', 'html', 'iii', 'incorreta', 'isso', 'issos', 'isto', 'istos', 'justificativa', 
	'leia', 'levaram', 'levou', 'lhe', 'lhes', 'logo', 'mais', 'mal', 'mas', 'mau', 
	'meio', 'menos', 'meus', 'muita', 'muitas', 'muito', 'muitos', 'nada', 'nao', 'naquela', 
	'naquelas', 'naquele', 'naqueles', 'naquilo', 'naquilos', 'nas', 'nela', 'nele', 'nem', 'nessa', 
	'nesse', 'nesta', 'neste', 'nisso', 'nisto', 'nos', 'nossa', 'nossas', 'nosso', 'nossos', 
	'num', 'numa', 'onde', 'ora', 'outra', 'outro', 'para', 'partir', 'pela', 'pelas', 
	'pelo', 'pelos', 'pode', 'podem', 'pois', 'por', 'porem', 'porisso', 'pos', 'pra', 
	'pre', 'pro', 'quais', 'qual', 'quando', 'quase', 'que', 'quem', 'refere', 'representa', 
	'sao', 'sei', 'seja', 'sem', 'ser', 'sera', 'seu', 'seus', 'sido', 'sob', 
	'sobre', 'somos', 'sou', 'sua', 'suas', 'tais', 'tal', 'tambem', 'tao', 'tem', 
	'tenha', 'tenham', 'tenho', 'tens', 'ter', 'teve', 'texto', 'the', 'tinha', 'tinham', 
	'toda', 'todavia', 'todo', 'traz', 'trouxe', 'tudo', 'uma', 'usar', 'uso', 'utilizava', 
	'utilizavam', 'utilizou', 'vai', 'vamo', 'vamos', 'vao', 'vem', 'vens', 'ver', 'vez', 
	'via', 'viam', 'vinham', 'vir', 'vol', 'vou', 'www', 
]

def stripaccents(value):
    if value is not None:
        return ''.join((c for c in unicodedata.normalize('NFD', value.lower()) if unicodedata.category(c) != 'Mn'))
    return ''

def prepare_document(value):
    if value is not None:
        value = re.sub('<.*?>', ' ', value.lower())
        value = ' '.join(list(set(re.findall('\w\w\w+', value))))
        return ''.join((c for c in unicodedata.normalize('NFD', value) if unicodedata.category(c) != 'Mn'))
    return ''

register = template.Library()
register.filter("stripaccents", stripaccents)
register.filter("prepare_document", prepare_document)