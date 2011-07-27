from google.appengine.api import memcache
from time import time
import logging
from tipfy import get_config

def check(ip, person):

  stat_interval = get_config('aib.antiwipe', "wipe_stat_interval")

  statnum = int(time()/stat_interval)
  statkey = "poststat-%d" % statnum

  poststat = memcache.get(statkey) or 0
  logging.info("wipe stat: %d" % poststat)

  interval = get_config('aib.antiwipe', "interval")
  maxquota = get_config('aib.antiwipe', "quota")
  maxquota_all = get_config('aib.antiwipe', "quota_all")

  if poststat > maxquota_all:
    interval *= get_config('aib.antiwipe', "wipe_interval_ratio")
    maxquota /= get_config('aib.antiwipe', "wipe_quota_ratio")
    logging.info("looks like wipe, increase interval: %d" %  interval)
  elif poststat > (maxquota_all*10):
    logging.info("increase limit even more!")
    interval *= get_config('aib.antiwipe', "wipe_huge_interval_ratio")
    maxquota = 1

  memcache.set(statkey, poststat+1, time=stat_interval)
  qkey = "ip-%s" % ip
  quota = memcache.get(qkey) or 0
  quota += 1
  memcache.set(qkey, quota, time=interval)

  if quota > maxquota:
    return False


  return True
