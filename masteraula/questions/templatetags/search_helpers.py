from django import template
from haystack.inputs import Clean
import unicodedata
import re

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