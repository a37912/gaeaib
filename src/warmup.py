import os
import logging

from tipfy import RequestHandler, Response, get_config
from tipfy.ext.jinja2 import get_env
from urls import get_rules
from werkzeug.utils import import_string

jinja = get_env()

def warm_jinja2():
  for tpldir in get_config('tipfy.ext.jinja2', 'templates_dir'):
    warm_jinja2_tpldir(tpldir)

def warm_jinja2_tpldir(tpldir):
  for tpl in os.listdir(tpldir):
    logging.info("warm load tpl: %r" % tpl)

    jinja.get_template(tpl)

def warm_urls():
  for rule in get_rules():
    logging.info("warm rule: %r" % rule.handler)
    import_string(rule.handler)

class Do(RequestHandler):
  def get(self):
    warm_jinja2()
    warm_urls()
      
    return Response("ni-paaa")
