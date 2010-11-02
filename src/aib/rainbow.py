# -*- coding: utf-8 -*-
import logging
from md5 import md5

from tipfy import get_config

TWRAPER = "<span class='rainbow'>%s</span>"
TEMPLATE='<span style="background: rgb(%d, %d, %d);">&nbsp;</span>'

## Tag flter: renders color codes to html
def rainbow(codes):
  if not codes:
    return ""

  logging.info("rainbow this: %s" % str(codes))
  return TWRAPER % reduce(
      lambda x,a:a+x,
      map( lambda color: TEMPLATE %tuple(color), codes)
  )

## Helper: calculates 5 colors for post
def old_make_rainbow(*a):
  # remove this shit 
  secret = 'YOBA'# FIXME
  a = map(str,a)
  a.insert(0,secret)
  key = str.join("-", a)

  codes = [[]]
  for x in md5(key).digest()[:15]:
    codes[-1].append(ord(x))

    if len(codes[-1]) == 3:
      codes.append([])

  logging.info("code: %s" % str(codes))

  return codes[:-1]

def make_rainbow(*a):
  """ function makes rainbow codes """
  secret = get_config('aib.rainbow', 'secret')
  a = map(str,a)
  a.insert(0,secret)
  key = str.join("-", a)
  rb_hash = md5(key).hexdigest()[:18]
  logging.info("rainbow code: %s" % rb_hash)
  return rb_hash
  