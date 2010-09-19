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
  
# New post or thread form
class PostForm(Form):

  name = TextField()
  sage = BooleanField()
  text = TextField(validators=[spam])
  key = TextField()
  subject = TextField()


