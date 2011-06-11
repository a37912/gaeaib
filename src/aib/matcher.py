from google.appengine.api import prospective_search as  matcher
from google.appengine.ext import db
from google.appengine.api import channel

from simplejson import dumps

from tipfy import RequestHandler, Response
from tipfy.ext.db import JsonProperty
import logging

class Handle(RequestHandler):
  def post(self):

    post = matcher.get_document(self.request.form)
    send = post.data

    for sub_id in self.request.form.getlist('id'):
      logging.info("send post to %s" % sub_id)
      try:
        channel.send_message(sub_id, dumps(send))
      except channel.InvalidChannelClientIdError:
        logging.error("inval client id %r" % sub_id)
      except channel.InvalidMessageError:
        logging.error("inval msg: %r" % dumps(send))

    return Response("ok")

class Post(db.Model):
  board = db.StringProperty()
  thread = db.IntegerProperty()
  data = JsonProperty()

  def put(self):
    assert False, "dont do this"

