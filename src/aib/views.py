import logging
from md5 import md5
from datetime import datetime
from django.utils.simplejson import dumps

from google.appengine.api import memcache
from google.appengine.ext import db
from google.appengine.api import images
from google.appengine.ext import blobstore
from google.appengine.api import channel

from tipfy import RequestHandler, redirect, Response, NotFound
from tipfy.ext.jinja2 import render_response
from tipfy.ext.blobstore import BlobstoreDownloadMixin, BlobstoreUploadMixin

from wtforms import Form
from wtforms.fields import TextField, BooleanField

from traceback import format_exc

import rainbow


# TODO: move out
# New post or thread form
class PostForm(Form):

  name = TextField()
  sage = BooleanField()
  text = TextField()
  key = TextField()


# temporary here is list of boards
boardlist = {
    'a' : 'Anime',
    'b' : 'Beating heart',
    's' : 'School days',
    'mod' : 'Dating with Winry',
}
THREAD_PER_PAGE = 10
REPLIES_MAIN = 5

## View: Main page - board list
#
class Index(RequestHandler):
  def get(self):
    return render_response("index.html", boards = boardlist)

## Helper: functon to grab last thread list for board
#
# @param board - string board name
def get_threads(board):

  threads = memcache.get("threadlist-%s" % board) or []

  # map list of thread ids to fetch
  ids = map(str,threads)

  # grab data from cache
  data =  memcache.get_multi(ids, "posts-%s-" % board)
  logging.info("grabbed ids %s, prefix %s, got %s" %(
    str(ids),
    "posts-%s-" % board,
    str(data.keys()),
    )
  )

  ret = []
  for thread in threads:
    content = data.get(str(thread))

    if not content:
      continue

    if len(content) > REPLIES_MAIN+1:
      end = content[-REPLIES_MAIN:]
      omitt = len(content) - REPLIES_MAIN - 1
    else:
      end = content[1:]
      omitt = 0
      

    thread_data = {
        'op' : content[0],
        'posts' : end,
        'id' : thread,
        "skipmsg" : "%d omitted" % omitt if omitt else None,
      }

    ret.append( thread_data )

  return ret

## View: board page is a list of threads
#
# @param board - string board name
class Board(RequestHandler):
  def get(self, board):

    data = {}
    data['post_form'] = PostForm() # new post form
    data['board_name'] = board # board name
    data['threads'] = get_threads(board) # last threads
    data['show_captcha'] = True
    data['reply'] = True
    data['board'] = boardlist.get(board, 'WHooo??')
    
    logging.info("board %s %s" % (board, str(memcache.get("thread"))))

    return render_response("thread.html", **data)

POST_QUOTA = 3
POST_INERVAL = 3 * 60

## View: saves new post
#
# @param board - string board name
# @param thread - thread id where to post or "new"
class Post(RequestHandler):
  def post(self, board, thread):
    logging.info("post called")

    ip = self.request.remote_addr

    qkey = "ip-%s" % ip
    quota = memcache.get(qkey) or 0
    quota += 1
    memcache.set(qkey, quota, time=POST_INERVAL*quota)

    logging.info("ip: %s, quota: %d" % (ip, quota))

    if quota >= POST_QUOTA:
      return redirect("/%s" % board)

    # validate post form
    form = PostForm(self.request.form)

    if not form.validate:
      return redirect("/%s" % board)


    # if ok, save
    logging.info("data valid %r" %( form.data,))
    try:
      save_post(form.data, board, thread, ip)
    except:
      logging.error(
         format_exc() 
      )
      raise
    finally:
      logging.info("after save")

    # TODO: redirect to thread or to board
    return redirect("/%s" % board)

## Helper: calculates 5 colors for post
def make_rainbow(ip, board, thread):
  secret = 'YOBA'# FIXME
  key = "%s-%s-%s-%s" %(secret, ip, board, thread)

  codes = [[]]
  for x in md5(key).digest()[:15]:
    codes[-1].append(ord(x))

    if len(codes[-1]) == 3:
      codes.append([])

  logging.info("code: %s" % str(codes))

  return codes[:-1]

## Helper: saves post to thread
#
# @param data - valid cleaned data from form
# @param board - string board name
# @param thread - thread id where to post or "new"
def save_post(data, board, thread, ip):

  # create new thread
  if thread == 'new':
    thread = memcache.incr("posts-%s" % board, initial_value=0)
    thread_clean(board)
    new = True
  else:
    thread = int(thread)
    new = False

  # FIXME: dont allow to post to nonexstand thread
  posts = memcache.get("posts-%s-%d" % (board, thread))
  if not posts:
    posts = []

  if not new and not posts:
    raise NotFound()

  rb = make_rainbow(ip, board, thread)
  data['rainbow'] = rb
  data['rainbow_html'] = rainbow.rainbow(rb)

  # FIXME: move to field
  data['name'] = data.get("name") or "Anonymous"

  if new:
    newpost = thread
  else:
    newpost = memcache.incr("posts-%s" % board, initial_value=0)

  # save thread and post number
  data['post'] = newpost
  data['thread'] = thread
  now = datetime.now()
  data['time'] = now.strftime("%Y-%m-%d, %H:%M")
  data['timestamp'] = int(now.strftime("%s"))

  img_key = data.get("key")

  if img_key:
    blob_key = blobstore.BlobKey(img_key)
    blob_info = blobstore.BlobInfo.get(blob_key)

    data['image'] = {
        "size" : blob_info.size,
        "content_type" : blob_info.content_type,
        "full" : images.get_serving_url(img_key),
        "thumb" : images.get_serving_url(img_key, 200),
    }

  posts.append(data)

  # save to cache
  memcache.set("posts-%s-%d" % (board, thread), posts)
  memcache.set("post-%s-%d" % (board,newpost), data)

  # debug
  key = "posts-%s-%d" % (board, thread)

  logging.info("saved %s" % key)

  if new or not data.get("sage"):
    thread_bump(board, thread)

  #key = "update-thread-%s-%d" % (board, thread)
  #if not new:
  #  channel.send_message(key, dumps(data))

## Helper: bumps thread to the top
#
# @param board - string board name
# @param thread - thread id
#
# @note - can be called at thread creat time
def thread_bump(board, thread):
  threads = memcache.get("threadlist-%s" % board) or []

  if thread in threads:
    threads.remove(thread)

  threads.insert(0, thread)

  memcache.set("threadlist-%s" % board, threads)

## Helper: deletes old threads
#
# @param board - string board nam
# 
# @note called before creating new thread
def thread_clean(board):
  threads = memcache.get("threadlist-%s" % board) or []

  if len(threads) < THREAD_PER_PAGE:
    return

  to_remove = map(str, threads[THREAD_PER_PAGE-1:])
  #memcache.delete_multi(to_remove, key_prefix="posts-%s-" % board)

  memcache.set("threadlist-%s" % board, threads[:THREAD_PER_PAGE-1])


## View: show all posts in thread
#
# @param board - string board name
# @Param thread - thread id where
class Thread(RequestHandler):
  def get(self, board, thread):

    content = memcache.get("posts-%s-%d" % (board, thread))

    if not content:
      raise NotFound

    thread_data = {
      'op' : content[0],
      'posts' : content[1:],
      'id' : thread,
    }

    data = {}
    data['threads'] = (thread_data,)
    data['post_form'] = PostForm()
    data['upload_url'] = blobstore.create_upload_url(
        "/%s/%d/post/" % (board, thread),
    )
    data['board_name'] = boardlist.get(board, "Woooo???")
    data['board'] = board
    key = "update-thread-%s-%d" % (board, thread)
    #data['thread_token'] = channel.create_channel(key)

    return render_response("thread.html", **data)

# TODO: move out of django
## View load image
#
# @param image_hash - requested image hash
def image(request, image_key):
  blobinfo = blobstore.BlobInfo(blobstore.BlobKey(image_key))

  logging.info("requested %s got %s" % (
    str(image_key),
    str(blobinfo)
    )
  )
  
  return send_blob(request, blobinfo)

def thumb(request, thumb_key):
  thumb = db.get(db.Key(thumb_key))

  return HttpResponse(thumb.data, mimetype="image")

class PostUrl(RequestHandler):
  def get(self):
    return Response( 
      blobstore.create_upload_url("/post_img")
    )


class PostImage(RequestHandler, BlobstoreUploadMixin):
  def get(self, img):
    return Response( '{"img":"%s"}' % img )

  def post(self):
    upload_files = self.get_uploads('image')
    blob_info = upload_files[0]

    key = str(blob_info.key())

    return Response(
      status = 302,
      headers = { "Location" : "/post_img/%s" % key }
    )

class ViewImage(RequestHandler, BlobstoreDownloadMixin):
  def get(self, img):
    key = blobstore.BlobKey(img)

    url = images.get_serving_url(img, 48)
    url = url.replace("0.0.0.0", self.request.host.split(":")[0])

    return Response(
      status = 302,
      headers = { "Location" : str(url) },
    )
 
class ApiPost(RequestHandler):
  TPL = {
      "thread" : "posts-%(board)s-%(num)d",
      "post" : "post-%(board)s-%(num)d",
      "lastpost" : "posts-%(board)s",
      "threadlist" : "threadlist-%(board)s"
  }
  def get(self, mode, board, num=None):
    key = self.TPL.get(mode)
    posts = memcache.get(key % {"board":board, "num":num})

    return Response(
        dumps(posts),
        content_type="text/javascript",
    )

class Delete(RequestHandler):
  def post(self, board, thread, post):

    key = "posts-%s-%d" % (board, thread)

    if post == thread:
      memcache.delete(key)
      return Response("wipe")

    posts = memcache.get(key) or []

    for offset, data in enumerate(posts):
      if data.get('post') == post:
        posts.pop(offset)
        break
    else:
      return Response("no")

    memcache.set(key, posts)

    return Response("ok")

class Unban(RequestHandler):
  def get(self, ip):
    qkey = "ip-%s" % ip
    memcache.delete(qkey)

    return Response("free")

