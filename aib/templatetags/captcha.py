from django import template
from django.utils.safestring import mark_safe
import logging
import recaptcha
from django.conf import settings

register = template.Library()

@register.simple_tag
def captcha():
  return mark_safe(recaptcha.displayhtml(settings.RECAPTCHA_PUB))

