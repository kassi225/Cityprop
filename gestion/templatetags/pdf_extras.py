import os
from django.conf import settings
from django import template

register = template.Library()

@register.filter
def pdf_static(path):
    return os.path.join(settings.STATIC_ROOT, path)
