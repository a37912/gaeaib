# -*- coding: utf-8 -*-
import logging

from google.appengine.ext import db
from tipfy import get_config
from tipfy.ext.db import PickleProperty
from aetycoon import DerivedProperty, CompressedProperty, TransformProperty 
from jinja2.utils import escape

class Board(db.Model):
  OLD_LIM = 50

  thread = db.ListProperty(int, indexed=False)
  counter = db.IntegerProperty(default=0)
  date_modify = db.DateTimeProperty(auto_now=True)

  NAMES = dict(get_config("aib", "boardlist"))

  @DerivedProperty
  def old(self):
    return self.counter > self.OLD_LIM

  @DerivedProperty
  def named(self):
    return self.code in self.NAMES

  @property
  def code(self):
    return self.key().name()

  @property
  def name(self):
    return self.NAMES.get(self.code)

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

class ThreadIndex(db.Model):
  @DerivedProperty
  def images(self):
    return [
        p.get("key") 
        for p in self.parent().posts 
        if p.get('key')
    ] 

  @DerivedProperty
  def post_numbers(self):
    return [p.get("post") for p in self.parent().posts]

  @DerivedProperty
  def post_count(self):
    return len(self.parent().posts)

  @DerivedProperty
  def board(self):
    return self.parent().board


class Thread(db.Model):

  REPLIES_MAIN = get_config("aib.ib", 'replies_main')
  posts = PickleProperty()

  subject = db.StringProperty(indexed=False)
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
      off = -self.REPLIES_MAIN
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

class GenKey(object):

  @classmethod
  def gen_key(cls, mode, *a, **kw):
    f = getattr(cls, "gen_key_" + mode)

    return f(*a, **kw)

  @classmethod
  def gen_key_board(cls, board, name=None):
    name = name or cls.DEF_KEY
    return db.Key.from_path("Board", board, cls.kind(), name)

  @classmethod
  def gen_key_thread(cls, board, thread, name=None):
    name = name or cls.DEF_KEY
    tkey = Thread.gen_key(thread, board)

    return db.Key.from_path(cls.kind(), name, parent=tkey)

  @classmethod
  def create(cls, *a, **kw):
    return cls(key=cls.gen_key(*a), **kw)


  @classmethod
  def load(cls, *a, **kw):
    cache = cls.get(cls.gen_key(*a, **kw))

    return cache

  @classmethod
  def remove(cls, *a):
    key=cls.gen_key(*a)

    db.delete(key)


class Cache(db.Model, GenKey):
  DEF_KEY = "html"

  comp = CompressedProperty(6)

  def get_data(self):
    return self.comp.decode("utf8")

  def set_data(self, val):
    self.comp = val.encode("utf8")


  data = property(get_data, set_data)

class Rss(db.Model, GenKey):
  DEF_KEY = "rss"
  posts = db.ListProperty(unicode, indexed=False)

  date_modify = db.DateTimeProperty(auto_now=True)

  xml = CompressedProperty(6)
