from django import template
import unicodedata

def stripaccents(value):
    if value is not None:
        return ''.join((c for c in unicodedata.normalize('NFD', value) if unicodedata.category(c) != 'Mn'))

register = template.Library()
register.filter("stripaccents", stripaccents)