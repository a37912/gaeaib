from google.appengine.api import prospective_search as  matcher
from google.appengine.api import xmpp

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
      if '@' in sub_id:
        whoami = '%(board)s@bankaiapp.appspotchat.com' % send
        MSG = """Posted http://42ch.org/%(board)s/%(thread)d/#p%(last)d\n\n%(text)s""" % send
        xmpp.send_message(sub_id, MSG, from_jid=whoami)
        continue

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
  thread_flag = db.StringProperty()
  data = JsonProperty()

  def put(self):
    assert False, "dont do this"

