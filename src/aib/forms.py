# -*- coding: utf-8 -*-
import re

from tipfy import get_config
from wtforms import Form, ValidationError
from wtforms.fields import TextField, BooleanField

SIGN = "(%s)" % str.join(
    "|",
    get_config(__name__, "spamlist")
  )

def spam(form, field):
  if not form._fields['name'].raw_data:
    return

  if not field.data:
    return

  if re.search(SIGN, field.data):
    raise ValidationError("possible spam")

def fixempty(form, field):
  if not field.data:
    field.data = field.default
  
# New post or thread form
class PostForm(Form):

  name = TextField(validators=[fixempty], default="Anonymous")
  sage = BooleanField()
  text = TextField(validators=[spam])
  key = TextField()
  subject = TextField()


