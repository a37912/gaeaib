from tipfy.ext.jinja2 import get_env
import logging

TEMPLATE='<span style="background: none repeat scroll 0% 0%rgb(%d, %d, %d);">&nbsp;&nbsp;</span>'

## Tag flter: renders color codes to html
def rainbow(codes):
  if not codes:
    return ""

  logging.info("rainbow this: %s" % str(codes))
  return reduce(
      lambda x,a:a+x,
      map( lambda color: TEMPLATE %tuple(color), codes)
  )
