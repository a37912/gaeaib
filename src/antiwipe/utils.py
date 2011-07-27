from time import time
import logging

from google.appengine.api import memcache
from google.appengine.ext import deferred

from tipfy import get_config

import models

CONFIG_KEYS = [
    "wipe_stat_interval",
    "interval",
    "quota",
    "quota_all",
    "wipe_interval_ratio",
    "wipe_quota_ratio",
    "wipe_huge_interval_ratio",
]

class Wipe(Exception):
  pass

_config = {}

def load__config(**cx):
  if _config:
    return

  for key in CONFIG_KEYS:
    _config[key] = get_config('aib.antiwipe', key)


def load_db_config(**cx):
  cfg = models.Config.get_by_key_name("only")
  if not cfg:
    return

  _config.update(cfg.config)


def ip_check(interval, quota, ip, _cx, **cx):

  qkey = "ip-%s" % ip
  current = memcache.get(qkey) or 0
  current += 1
  memcache.set(qkey, current, time=interval)

  _cx['fail'] = False
  if current > quota:
    _cx['fail'] = True
    raise Wipe("quata %d, max %d" % (current, quota))

  _cx['current'] = current


def load_stat(wipe_stat_interval, _cx, **cx):
  t = time()
  statnum = int(t/wipe_stat_interval)
  statkey = "poststat-%d" % statnum

  poststat = memcache.get(statkey) or 0

  _cx.update({
    "statkey": statkey,
    "poststat": poststat,
    "time": t,
  })

def save_stat(statkey, wipe_stat_interval, poststat, **cx):
  memcache.set(statkey, poststat+1, time=wipe_stat_interval)

def save_db_stat(**cx):
  deferred.defer(_save_db_stat, **cx)

def _save_db_stat(time, **cx):
  stat_db = models.DailyStat.load(time)

  stat = stat_db.info or {}

  log = stat.get('log') or []
  log.append(cx)
  stat['log'] = log

  for x in [60, 60*10, 3600, 3600*3, 3600*12, 3600*24]:
    timeslot = int(time) / x
    timeslot *= x

    data = stat.get(( timeslot, x)) or []

    data.append(cx)

    stat[( timeslot, x)] = data


  stat_db.info = stat

  stat_db.put()


def more_interval(wipe_interval_ratio, wipe_quota_ratio, _cx, **cx):
  _cx['interval'] *= wipe_interval_ratio
  _cx['quota'] /= wipe_quota_ratio

def wipe_interval(wipe_huge_interval_ratio, _cx, **cx):
  _cx['interval'] *= wipe_huge_interval_ratio
  _cx['quota'] = 1


def calc_interval(poststat, quota_all, _cx, **cx):
  if poststat > (quota_all*10):
    return wipe_interval
  elif poststat > quota_all:
    return more_interval

def check(person, **cx):
  cx = cx.copy()
  cx.update(_config)
  cx.update(person)

  fchecks = checks[:]
  fchecks.reverse()

  ret = True
  f = fchecks.pop()
  frun = []
  while f:
    frun.append(f)
    logging.debug("wipe f: %r, cx: %r" % (f, cx))
    try:
      f = f(_cx=cx, **cx)
    except Wipe:
      ret = False
      f = None
      logging.info("oops")

    if not f and fchecks:
      f = fchecks.pop()

  logging.info("wipe info: %r %r" % (frun, cx))
  return ret

checks = [
    load_db_config,
    load_stat,
    calc_interval,
    ip_check,
    save_stat,
    save_db_stat,
]


load__config()
