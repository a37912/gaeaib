# -*- coding: utf-8 -*-
import logging

from google.appengine.ext import db
from tipfy import get_config
from tipfy.ext.db import PickleProperty
from aetycoon import DerivedProperty, CompressedProperty
from jinja2.utils import escape

class Board(db.Model):
  thread = db.ListProperty(int)
  counter = db.IntegerProperty(default=0)

  @property
  def code(self):
    return self.key().name()

  @property
  def name(self):
    return get_config("aib.boards", self.code)

  @classmethod
  def load_counter(cls, board):
    ent = cls.get_by_key_name(board)
    if not ent:
      return 1
    ent.counter+=1
    ent.put()

    return ent.counter

  @classmethod
  def load(cls, board):
    ent = cls.get_by_key_name(board)

    return ent.thread if ent else None

class Thread(db.Model):

  REPLIES_MAIN = get_config("aib.ib", 'replies_main')
  posts = PickleProperty()

  @DerivedProperty
  def images(self):
    return [
        p.get("key") 
        for p in self.posts 
        if p.get('key')
    ] 

  @DerivedProperty
  def post_numbers(self):
    return [p.get("post") for p in self.posts]

  subject = db.StringProperty()
  board = db.StringProperty()
  id = db.IntegerProperty()

  @property
  def safe_subject(self):
    return escape(self.subject)

  @property
  def op(self):
    return self.posts[0]

  @property
  def tail_posts(self):
    if len(self.posts) > self.REPLIES_MAIN+1:
      off = -replies_main
    else:
      off = 1

    return self.posts[off:]

  @property
  def skip(self):
    skip = len(self.posts) - self.REPLIES_MAIN - 1

    if skip > 0:
      return skip

  @classmethod
  def load(cls, number, board):
    return cls.get(cls.gen_key(number, board))

  @classmethod
  def gen_key(cls, number, board):
    return db.Key.from_path("Thread", "%s/%d"%(board,number))

  @classmethod
  def create(cls, number, board):
    return cls(key=cls.gen_key(number, board),
        board=board, id=number)

  @classmethod
  def load_list(cls, numbers, board):

    keys = [
      cls.gen_key(num, board)
      for num in numbers
    ]

    return zip( numbers, db.get(keys))

class Cache(db.Model):
  comp = CompressedProperty(6)

  def get_data(self):
    return self.comp.decode("utf8")

  def set_data(self, val):
    self.comp = val.encode("utf8")


  data = property(get_data, set_data)

  @classmethod
  def gen_key(cls, mode, *a):
    f = getattr(cls, "gen_key_" + mode)

    return f(*a)

  @classmethod
  def gen_key_board(cls, board):
    return db.Key.from_path("Board", board, "Cache", "html")

  @classmethod
  def gen_key_thread(cls, board, thread):
    tkey = Thread.gen_key(thread, board)

    return db.Key.from_path("Cache", "html", parent=tkey)

  @classmethod
  def create(cls, *a, **kw):
    return cls(key=cls.gen_key(*a), **kw)


  @classmethod
  def load(cls, *a):
    cache = cls.get(cls.gen_key(*a))

    return cache

  @classmethod
  def delete(cls, *a):
    key=cls.gen_key(*a)

    db.delete(key)
