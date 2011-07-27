from google.appengine.ext import db
from tipfy.ext.db import PickleProperty

DAY = 3600 * 24

class DailyStat(db.Model):
  date_modify = db.DateTimeProperty(auto_now=True)
  date_create = db.DateTimeProperty(auto_now_add=True)

  info = PickleProperty()

  @classmethod
  def load(cls, time):
    time = int(time)
    time /= DAY
    time *= DAY
    key = "day_%d" % time

    return cls.get_or_insert(key_name=key)

class Config(db.Model):
  date_modify = db.DateTimeProperty(auto_now=True)
  config = PickleProperty()
