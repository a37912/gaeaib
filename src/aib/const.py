# -*- coding: utf-8 -*-
# temporary here is list of boards
boardlist_order = (
   ( 'b', 'Beating heart'),
   ( 'a', 'Anime',),
   ( 's', 'School days',),
   ( 'ne', 'Nekospot'),
   ( 'g', '/g/ is for Games'),
   ( 'mod' , 'Dating with Winry',),
   
#   ( 'ped' , 'Church of Pedaliq Scripts',),
#   ( 'wh' , 'Imperium', ),
)
boardlist = dict(boardlist_order)
THREAD_PER_PAGE = 10
BOARD_PAGES = 5
REPLIES_MAIN = 5

POST_QUOTA = 6
POST_QUOTA_ALL = 20
POST_INERVAL = 100
POST_IMG_INERVAL = 20
POST_IMG_QUOTA = 3

WIPE_INTERVAL_RATIO = 5
WIPE_QUOTA_RATIO = 3
WIPE_STAT_INTERVAL = 120

WATCHER_TIME = 20*60
WATCHERS_MAX = 20

MOD_NAME = 'Winry'

board_options = {
    's': ['useragent'],
    'b': ['saem'],
    'mod' : [ 'modsign'],
}

board_overlay = ['s', 'g', 'ne']
