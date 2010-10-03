from models import Cache
from tipfy.ext.jinja2 import render_template
from const import *
from mark import markup
import re
from cgi import escape

class Render(object):
  MAXREFS = 5
  def __init__(self, board, thread):
    self.board = board
    self.thread = thread

  def load(self,):
    self.html = Cache.load(Board=self.board, Thread=self.thread)

    if self.html:
      self.html = self.html.decode('utf8')


  def _markup(self, post):
    post = post.copy()
    post['html'] = markup(
        board=self.board, postid=post.get("post"),
        data = escape(post.get('text')),
    )

    return post

  def create(self,op):
    op = self._markup(op)

    data = {
        "op" : op,
        "id" : self.thread,
        "board" : self.board,
        "subject" : op.get("subject"),
    }
    self.html = render_template("thread_new.html", 
        threads = (data,),
        board = self.board,
        board_name = boardlist.get(self.board, "Woooo???"),
        boards = boardlist_order,
    )

  def add(self,post,new=False):
    if new:
      self.create(post)
    else:
      self.load()
      self.append(post)

  def append(self, post):
    assert self.html, 'nowhere to append'

    post = self._markup(post)

    post_html = render_template("post.html", post=post)

    self.html = self.html.replace(
        u"<!--NPHERE-->", post_html)

    refs = re.findall(">>([0-9]+)", post.get("text", "")) or []

    if refs:
      refhtml = render_template("ref.html", 
          board = self.board,
          thread = self.thread,
          refpost = post.get("post"),
          rainbow = post.get("rainbow_html")
      )

    for ref in refs[:self.MAXREFS]:
      pattern = u"<!--REF-%s-->" % ref
      self.html = self.html.replace(pattern, refhtml+pattern)

  def save(self):
    Cache.save(self.html, Board=self.board, Thread=self.thread)

