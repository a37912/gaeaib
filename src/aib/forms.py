# -*- coding: utf-8 -*-
import re

from tipfy import get_config
from wtforms import Form, ValidationError
from wtforms.fields import TextField, BooleanField, HiddenField

SIGN = "(%s)" % str.join(
    "|",
    get_config(__name__, "spamlist")
  )

## trat some data in in text field as spam
#
# bbcode links for example
def spam(form, field):
  if not form._fields['name'].raw_data:
    return

  if not field.data:
    return

  if re.search(SIGN, field.data):
    raise ValidationError("possible spam")

## Workarround for WTForms bug
#
# default value is applied only if field data is None
# assign default value if empty string passed
def fixempty(form, field):
  if not field.data:
    field.data = field.default

## Trap for spambots
#
# ensure field is empty, if anything passed here
# whole form is spam one
def beempty(form, field):
  if field.data:
    raise ValidationError("spambot")


## Dont allow empty text without attach
#
# ensure one of key or text values passed
# for some reason key may be [u""] in some cases
def attach(form, field):
  key = form._fields['key'].raw_data

  if key and key[0]:
    return

  if not field.data:
    raise ValidationError("empty post")
  

# New post or thread form
class PostForm(Form):

  name = TextField(validators=[fixempty], default="Anonymous")
  sage = BooleanField()
  text = TextField(validators=[spam, attach], default="")
  key = TextField()
  subject = TextField()

  # trap

  email = HiddenField(validators=[beempty])
  username = HiddenField(validators=[beempty])
