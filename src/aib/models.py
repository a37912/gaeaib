import logging

from google.appengine.ext import db
from tipfy.ext.db import PickleProperty
from aetycoon import DerivedProperty, CompressedProperty
from const import *

class Board(db.Model):
  thread = db.ListProperty(int)
  counter = db.IntegerProperty(default=0)

  @property
  def code(self):
    return self.key().name()

  @property
  def name(self):
    return boardlist.get(self.code)

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
  def op(self):
    return self.posts[0]

  @property
  def tail_posts(self):
    if len(self.posts) > REPLIES_MAIN+1:
      off = -REPLIES_MAIN
    else:
      off = 1

    return self.posts[off:]

  @property
  def skip(self):
    skip = len(self.posts) - REPLIES_MAIN - 1

    if skip > 0:
      return skip

  @classmethod
  def load(cls, number, board):
    return cls.get(cls.gen_key(board, number))

  @classmethod
  def gen_key(cls, board, number):
    return db.Key.from_path("Thread", "%s/%d"%(board,number))

  @classmethod
  def create(cls, number, board):
    return cls(key=cls.gen_key(board, number), 
        board=board, id=number)

  @classmethod
  def load_list(cls, numbers, board):

    keys = [
      cls.gen_key(board, num)
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
    tkey = Thread.gen_key(board, thread)

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
