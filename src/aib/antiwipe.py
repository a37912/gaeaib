from google.appengine.api import memcache
from time import time
import logging
from const import *


def check(ip):

  statnum = int(time()/WIPE_STAT_INTERVAL)
  statkey = "poststat-%d" % statnum

  poststat = memcache.get(statkey) or 0
  logging.info("wipe stat: %d" % poststat)

  interval = POST_INERVAL
  maxquota = POST_QUOTA

  if poststat > POST_QUOTA_ALL:
    interval *= WIPE_INTERVAL_RATIO
    maxquota /= WIPE_QUOTA_RATIO
    logging.info("looks like wipe, increase interval: %d" %  interval)
  elif poststat > (POST_QUOTA_ALL*10):
    logging.info("increase limit even more!")
    interval *= (WIPE_INTERVAL_RATIO * 10)
    maxquota = 1

  memcache.set(statkey, poststat+1, time=WIPE_STAT_INTERVAL)
  qkey = "ip-%s" % ip
  quota = memcache.get(qkey) or 0
  quota += 1
  memcache.set(qkey, quota, time=interval)

  if quota > maxquota:
    return False


  return True
