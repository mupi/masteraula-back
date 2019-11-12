from django import template
from haystack.inputs import Clean
import unicodedata
import re
from get_conectives import connectives

def stripaccents(value):
    if value is not None:
        return ''.join((c for c in unicodedata.normalize('NFD', value.lower()) if unicodedata.category(c) != 'Mn'))
    return ''

def stripaccents_str(value):
    if type(value) is not str:
        value = str(value)
    if value is not None:
        return ''.join((c for c in unicodedata.normalize('NFD', value) if unicodedata.category(c) != 'Mn'))
    return ''

def prepare_document(value):
    if value is not None:
        value = re.sub('<.*?>', ' ', value.lower())
        value = ' '.join(list(set(re.findall('\w\w\w+', value))))
        return ''.join((c for c in unicodedata.normalize('NFD', value) if unicodedata.category(c) != 'Mn'))
    return ''

def only_key_words(value):
    def cmp(str1):
        return len(str1)

    value = prepare_document(value)
    if value is not None:
        return ' '.join(keyword for keyword in sorted(value.split(), key=cmp) if keyword not in connectives)
    return ''

register = template.Library()
register.filter("stripaccents", stripaccents)
register.filter("stripaccents_str", stripaccents)
register.filter("prepare_document", prepare_document)