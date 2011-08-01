# -*- coding: utf-8 -*-
import logging
from jinja2 import contextfilter, Markup

from md5 import md5

from tipfy import get_config

import urllib
import draw

## Tag flter: renders color codes to html
@contextfilter
def rainbow(ctx, hexcode):
  colors = []
  for x in range(6):
    colors.append([int(c,16) for c in hexcode[x:x+3]])

  lines = draw.rb(colors) 

  return '<img src="data:image/png,%s" width=20 heigh=20 />' % urllib.quote(
          draw.data(lines)
        )

def install_jinja2():
  from tipfy.ext.jinja2 import get_env
  environment = get_env()
  environment.filters['rainbow'] = rainbow


def make_rainbow(*a):
  """ function makes rainbow codes """
  secret = get_config('aib.rainbow', 'secret')
  a = map(str,a)
  a.insert(0,secret)
  key = str.join("-", a)
  rb_hash = md5(key).hexdigest()[:18]
  logging.info("rainbow code: %s" % rb_hash)
  return rb_hash
