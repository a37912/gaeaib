import logging
import re
from models import Thread
from google.appengine.ext import db

def from_cache(cache):
  parent = cache.parent()

  if parent:
    if parent.posts and 'text' in parent.posts[0]:
      return

  th = Thread(key=cache.parent_key(), posts=[])
  thid = th.key().id()

  posts = [str(thid)]
  posts += re.findall('<table id="post-([0-9]+)"', cache.comp)

  texts = re.split("</blockquote>", cache.comp)
  texts = map(
      lambda s : re.search(
        r"<blockquote[^>]*postid=\"([0-9]+)\"[^>]*>(.*)",
        s,
        re.MULTILINE | re.S,
      ),
      texts
  )
  texts = [match.groups() for match in texts if match ]

  stamps = re.findall("(2010-[0-9]{2}-[0-9]{2}, [0-9]{2}:[0-9]{2})", cache.comp)
  names = re.findall('<span class="postername.*>(.*)</span>\n *(<span style="background:.*</span>|<b>.*</b>)', cache.comp)
  names += re.findall('commentpostername.*>(.*)</span>\n *<span class="rainbow">(.*)</span>', cache.comp) 
  images = re.findall('<img class="thumb" src="(.*)=s200"/>\n</a>\n<a class="erase-link" href="/delete/a/[0-9]*/([0-9]*)">', cache.comp)

  images += re.findall('src="(.*)=s200"/>\n</a>\n        \n        <blockquote class="postdata" postid="([0-9]*)"', cache.comp)

  logging.info("posts: %r" % posts)
  #logging.info("texts: %r" % texts)

  #logging.info("images: %r" % images)
  #logging.info("stamps: %r" % stamps)
  #logging.info("names: %d/%r" % (len(names), names))


  old = getattr(parent, "posts", [])

  logging.info("id: %r-%s, old: %r, new: %r" % (
    thid,
    th.parent_key().name(),
    len(old), 
    len(posts)
    )
  )

  if len(posts) < 5: # FIXME: magic number
    if parent:
      parent.delete()
    db.delete(cache)
    return

  num_index = {}
  for num, (name,rb), stamp in zip(posts, names, stamps):
    #logging.info("num: %r, idx %r" % (num, len(num_index)))
    num_index[num] = len(num_index)
    th.posts.append( 
        {
          "thread" : thid,
          "post" : int(num),
          "text_html" : "",
          "name" : name.decode("utf8"),
          "rainbow_html" : rb,
          "time" : stamp,
        }
    )

  logging.info("num index: %r" % num_index)


  for num, text in texts:
    idx = num_index[num]
    #logging.info("num: %r, idx: %r" % (num, idx))
    th.posts[idx]['text_html'] = text.decode("utf8")

  logging.info("index: %r" % num_index)

  for image, num in images:
    idx = num_index[num]
    th.posts[idx]['image'] = {
        "full" : image,
        "thumb" : image+"=s200",
      }

    
  th.put()
