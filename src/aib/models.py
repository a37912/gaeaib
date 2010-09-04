import logging

from google.appengine.ext import db
from google.appengine.api import memcache
from tipfy.ext.db import PickleProperty
#from aetycoon import DerivedProperty
from const import *

class Board(db.Model):
  TPL = "threadlist-%s"
  thread = db.ListProperty(int)
  counter = db.IntegerProperty(default=0)

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
    threads = memcache.get(cls.TPL % board)

    logging.info("cache threads %r" % threads) 
    if threads == None:
      logging.info("go to db")
      threads = cls.load_db(board)

      if threads:
        memcache.set(cls.TPL % board, threads)

    return threads or []

  @classmethod
  def load_db(cls, board):
    ent = cls.get_by_key_name(board)

    return ent.thread if ent else None

class Thread(db.Model):
  TPL = "posts-%s-"
  TPL_ONE = "posts-%s-%d"

  posts = PickleProperty()
  images = db.StringListProperty()

  @classmethod
  def load(cls, number, board):
    posts = memcache.get(cls.TPL_ONE % (board, number))

    if posts == None:
      posts = cls.load_db(number, board)

      if posts:
        memcache.set(cls.TPL_ONE % (board, number), posts)

    return posts or []

  @classmethod
  def load_db(cls, number, board):
    ent = cls.get(cls.gen_key(number, board))

    if ent:
      return ent.posts

  @classmethod
  def gen_key(cls, number, board):
    return db.Key.from_path("Board", board, "Thread", number)

  @classmethod
  def save(cls, number, board, posts):
    ent = cls(
        posts = posts, 
        images = [p.get("key") for p in posts if p.get('key')],
        key = cls.gen_key(number, board)
    )

    memcache.set(cls.TPL_ONE % (board, number), posts)

    return ent

  @classmethod
  def load_list(cls, numbers, board):
    keys = map(str, numbers)

    data =  memcache.get_multi(keys, cls.TPL % board)
    
    ret = []
    for num in numbers:
      th = data.get(str(num))

      if not th:
        logging.info("cant find %d %r, go to db" %(num,th))
        ret = cls.load_list_db(numbers, board)
        memcache.set_multi(
            dict(ret),
            key_prefix = cls.TPL % board
        )
        break

      ret.append( (num, th) )

    fail = numbers[:]
    for num, th in ret:
      if th:
        fail.remove(int(num))

    if fail:
      for num in fail:
        numbers.remove(num)
        
      Board.save(board, numbers)

    return ret

  @classmethod
  def load_list_db(cls, numbers, board):

    keys = [
      db.Key.from_path("Board", board, "Thread", num)
      for num in numbers
    ]

    return zip(
        map(str,numbers),
        map(
          lambda x : x.posts if x else [],
          filter(bool, db.get(keys))
        )
    )

class Cache(db.Model):
  data = db.TextProperty()

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

    data = memcache.get(key_str)

    if data:
      logging.info("got from cache %r" % key_str)
      return data

    ent = cls.get(key)

    if ent:
      logging.info("got from db cache %r" % key)
      return ent.data

    logging.info("no cache %r" % key_str)

  @classmethod
  def save(cls, data, **kw):

    key_str,key = cls.gen_key(**kw)

    memcache.set(key_str, data)

    ent = cls(data=data, key=key)
    ent.put()

  @classmethod
  def delete(cls, keys):
    keys = [cls.gen_key(**x) for x in  keys]
    logging.info("keys: %r" % keys)
    db.delete( [key for key_str,key in keys] )
    memcache.delete_multi( [key_str for key_str,key in keys] ) 
