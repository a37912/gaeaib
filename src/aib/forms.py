from wtforms import Form
from wtforms.fields import TextField, BooleanField

# New post or thread form
class PostForm(Form):

  name = TextField()
  sage = BooleanField()
  text = TextField()
  key = TextField()
  subject = TextField()


