import logging

from google.appengine.ext import db
from google.appengine.api import memcache
from tipfy.ext.db import PickleProperty
from aetycoon import DerivedProperty, CompressedProperty
from const import *

class Board(db.Model):
  TPL = "threadlist-%s"
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
    memcache.set("posts-%s" % board, ent.counter)

    return ent.counter

  @classmethod
  def load(cls, board):
    ent = cls.get_by_key_name(board)

    return ent.thread if ent else None

class Thread(db.Model):
  TPL = "posts-%s-"
  TPL_ONE = "posts-%s-%d"

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

  @property
  def id(self):
    return self.key().id()

  @classmethod
  def load(cls, number, board):
    return cls.get(cls.gen_key(number, board))

  @classmethod
  def gen_key(cls, number, board):
    return db.Key.from_path("Board", board, "Thread", number)

  @classmethod
  def create(cls, number, board):
    return cls(key=cls.gen_key(number, board))

  @classmethod
  def load_list(cls, numbers, board):

    keys = [
      db.Key.from_path("Board", board, "Thread", num)
      for num in numbers
    ]

    return zip( numbers, db.get(keys))

class Cache(db.Model):
  comp = CompressedProperty(6)

  @classmethod
  def gen_key(cls, **kw):
    key_list  = []
    keys = kw.keys()
    keys.sort()

    for key in keys:
      key_list.extend( [key, kw.get(key)] )

    key_list.extend( ["Cache", "html"] )

    return str.join("/", map(str,key_list)), db.Key.from_path(*key_list)

  @classmethod
  def load(cls, **kw):

    key_str,key = cls.gen_key(**kw)

    data = None #memcache.get(key_str)

    if data:
      logging.info("got from cache %r" % key_str)
      return data

    ent = cls.get(key)

    if ent:
      logging.info("got from db cache %r" % key)
      memcache.set(key_str, ent.comp)
      return ent.comp

    logging.info("no cache %r" % key_str)

  @classmethod
  def save(cls, data, **kw):

    key_str,key = cls.gen_key(**kw)

    memcache.set(key_str, data)

    ent = cls(comp=data.encode('utf8'), key=key)
    ent.put()

  @classmethod
  def delete(cls, keys):
    keys = [cls.gen_key(**x) for x in  keys]
    logging.info("keys: %r" % keys)
    db.delete( [key for key_str,key in keys] )
    memcache.delete_multi( [key_str for key_str,key in keys] ) 

