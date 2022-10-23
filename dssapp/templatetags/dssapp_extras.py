from django import template

register = template.Library()

@register.filter
def seq_index(sequence, position):
    return sequence[position]