from django import template
from django.utils.safestring import mark_safe
import logging


register = template.Library()

TEMPLATE='<span class="rainbowid"><span style="background: none repeat scroll 0% 0%rgb(%d, %d, %d);">&nbsp;&nbsp;</span>'

## Tag flter: renders color codes to html
@register.filter(name='rainbow')
def rainbow(codes):
  if not codes:
    return ""

  logging.info("rainbow this: %s" % str(codes))
  return mark_safe(reduce(
      lambda x,a:a+x,
      map( lambda color: TEMPLATE %tuple(color), codes)
  ))

rainbow.is_safe = True

