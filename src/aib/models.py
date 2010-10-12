# -*- coding: utf-8 -*-
import logging

from google.appengine.ext import db
from google.appengine.api import memcache
from tipfy.ext.db import PickleProperty
from aetycoon import DerivedProperty, CompressedProperty
from const import *
from jinja2.utils import escape

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
  def safe_subject(self):
    return "$$$"
    logging.info("XXX:Subj %s " % self.subject)
    if len(self.subject)==0:
      return escape(subject)
    else:
      return u"Тред номер %s" % self.id()


  @classmethod
  def load(cls, number, board):
    thread = None#memcache.get(cls.TPL_ONE % (board, number))

    if thread == None:
      thread = cls.load_db(number, board)

    return thread

  @classmethod
  def load_db(cls, number, board):
    return cls.get(cls.gen_key(number, board))

  @classmethod
  def gen_key(cls, number, board):
    return db.Key.from_path("Board", board, "Thread", number)

  @classmethod
  def create(cls, number, board):
    return cls(key=cls.gen_key(number, board))

  @classmethod
  def load_list(cls, numbers, board):
    keys = map(str, numbers)

    data =  {}#memcache.get_multi(keys, cls.TPL % board)
    
    ret = []
    for num in numbers:
      th = data.get(str(num))

      if not th:
        logging.info("cant find %d %r, go to db" %(num,th))
        ret = cls.load_list_db(numbers, board)
        memcache.set_multi(
            dict([(str(num),th) for num, th in ret]),
            key_prefix = cls.TPL % board
        )
        break

      ret.append( (num, th) )

    return ret

  @classmethod
  def load_list_db(cls, numbers, board):

    keys = [
      db.Key.from_path("Board", board, "Thread", num)
      for num in numbers
    ]

    return zip(
        numbers,
        map(
          lambda x : {
            "posts":x.posts,
            "subject":x.subject
          } if x else {},
          db.get(keys)
        )
    )

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

