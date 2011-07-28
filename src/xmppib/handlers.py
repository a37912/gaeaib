import logging
import re
from google.appengine.api import xmpp
from google.appengine.api import prospective_search as  matcher

from tipfy import RequestHandler, Response

from aib.util import save_post, Post as MatchPost
from aib.models import ThreadIndex
import antiwipe.utils as antiwipe

class SubRequest(RequestHandler):
  def post(self):
    frm = self.request.form.get('from').split('/')[0]
    to = self.request.form.get("to").split('/')[0]
    board = to.split('@')[0]

    logging.info("sub: %r -> %r" % (frm, to))
    logging.info("sub form: %r" % self.request.form)

    xmpp.send_presence(frm, from_jid=to, status="My app's status")

    #xmpp.send_message(frm, "hello >.<", from_jid=to)

    sub(frm, board)

    return Response("ya")

def sub(jid, board):
    query = 'board:%s thread_flag:new' % (board,)
    matcher.subscribe(MatchPost, query, jid, topic='post')

def thread_lookup(th, board):
    thq = ThreadIndex.all(keys_only=True)
    thq.filter("board", board)
    thq.filter("post_numbers", int(th))

    thread = thq.get()
    if not thread:
      return

    _board, _thread = thread.parent().name().split('/')
    return int(_thread)


class Post(RequestHandler):
  def post(self):
    logging.info("chat form: %r" % self.request.form)
    frm = self.request.form.get('from')
    to = self.request.form.get("to")
    txt = self.request.form.get("body")
    jid,res = frm.split('/', 1)
    board = to.split('@')[0]

    if txt == 'SUB':
        sub(jid, board)
        return Response("ya")

    headline = txt[:txt.find('\n')]

    th = re.search('^>>(\d+)', headline)
    if th:
      th = thread_lookup(th.group(1), board)
    else:
      th = re.search('^>>/(\w+)/(\d+)', headline)
      if th:
        board,th = th.groups()
        th = thread_lookup(th, board)
      else:
        th = 'new'

    if not th:
      xmpp.send_message(frm, "WINRY WINRY WINRY", from_jid=to)
      return Response("ya")


    person = {}

    if not antiwipe.check(person, ip=jid, board=board, thread=th):
        xmpp.send_message(frm, "Posted. not really. Keep trying", from_jid=to)
        return Response("ya")

    logging.info('post: %r %r %s' % (board, th, txt))
    #board = 'test'

    args = {
        "text": txt,
        "subject": "",
        "name": "Anonymous",
    }
    post, thread = save_post(self.request, args, board, th, jid)

    MSG = "Posted http://42ch.org/%s/%d/#p%d" %(board, thread, post)

    #
    query = 'board:%s thread:%d' %(board, th)
    matcher.subscribe(MatchPost, query, jid, topic='post')


    xmpp.send_message(frm, MSG, from_jid=to,)

    return Response("ya")
