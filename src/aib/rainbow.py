# -*- coding: utf-8 -*-
import logging
from md5 import md5

TWRAPER = "<div class='rainbow'>%s</div>"
TEMPLATE='<div style="background: rgb(%d, %d, %d);"></div>'

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
def make_rainbow(*a):
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

