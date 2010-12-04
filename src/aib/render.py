# -*- coding: utf-8 -*-
from models import Cache
from tipfy import get_config
from tipfy.ext.jinja2 import render_template
import re

NAMES = dict(get_config("aib", "boardlist"))

class Render(object):
  MAXREFS = 5
  OVER = get_config("aib", "overlay")

  def __init__(self, board, thread):
    self.board = board
    self.thread = thread

  def load(self,):
    self.cache = Cache.load("thread", self.board, self.thread)

    if not self.cache:
      self.cache = Cache.create("thread", self.board, self.thread)


  def create(self,op):

    data = {
        "op" : op,
        "id" : self.thread,
        "board" : self.board,
        "subject" : op.get("subject"),
    }

    self.cache = Cache.create("thread", self.board, self.thread)
    self.cache.data = render_template("thread.html", 
        thread = data,
	threads = [data],
        board = self.board,
        board_name = NAMES.get(self.board) or get_config("aib",
          "default_name"),
        boards = get_config("aib", "boardlist"), # context?
        overlay = self.board in self.OVER,
    )

  def add(self,post,new=False):
    if new:
      self.create(post)
    else:
      self.load()
      self.append(post)

  def append(self, post):
    assert self.cache.data, 'nowhere to append'

    self.post_html = render_template("post.html", post=post, board=self.board)

    self.cache.data = self.cache.data.replace(
        u"<!--NPHERE-->", self.post_html)

    refs = re.findall(">>([0-9]+)", post.get("text", "")) or []

    if refs:
      refhtml = render_template("ref.html", 
          board = self.board,
          thread = self.thread,
          refpost = post.get("post"),
          rainbow = post.get("rainbow")
      )

    for ref in refs[:self.MAXREFS]:
      pattern = u"<!--REF-%s-->" % ref
      self.cache.data = self.cache.data.replace(pattern, refhtml+pattern)

  def save(self):
    self.cache.put()
