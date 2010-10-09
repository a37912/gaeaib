import re
from jinja2 import contextfilter, Markup
from cgi import escape


POST_LINK = (
    "&gt;&gt;([0-9]+)",
    r'<a frmpostid="##postid##" postid="\1" class="postref" href="/##board##/p\1">&gt;&gt;\1</a>',
)

BOLD1 = (
    "\*\*([^\*_]+)\*\*",
    r"<b>\1</b>",
)

BOLD2 = (
    "__([^\*_]+)__",
    r"<b>\1</b>",
)

ITALIC = (
    "\*([^\*_]+)\*",
    r"<i>\1</i>",
)

PRE_SPAN = (
    "```(.*)```",
    r"<pre>\1</pre>",
)

SPOILER = (
    "\%\%(.*)\%\%",
    r'<span class="spoiler">\1</span>',
)

AHREF = (
    r"(http:\/\/[^ <]*)",
    r'<a href="http://hiderefer.com/?\1">\1</a>' ,
)

FULL = 0
PRE = 1
QUOTE = 2
LIST = 3

states = {
    FULL : {
      "fmt" : [
        POST_LINK,
        BOLD1,
        BOLD2,
        ITALIC,
        PRE_SPAN,
        SPOILER,
        AHREF,
      ],
      "change" : [
        PRE,
        QUOTE,
        LIST,
      ],
      "line" : (r"^(.*)$", r"\1<br/>"),
    },
    PRE : {
      "match" : r"^    ",
      "start" : "<pre>",
      "end" : "</pre>",
      "fmt" : [],
      "change" : [ ],
    },
    QUOTE : {
      "match" : r"^&gt;[^&]",
      "start" : '<p class="unkfunc">',
      "end" : '</p>',
      "fmt" : [
        POST_LINK,
        SPOILER,
        BOLD1,
        BOLD2,
        ITALIC,
      ],
      "change" : [],
    },
    LIST : {
      "match" : r" -",
      "start" : "<ul>",
      "end" : "</ul>",
      "line" : (r"^ -(.*)$", r"<li>\1</li>"),
      "change" : [],
      "fmt" : [
        POST_LINK,
        SPOILER,
        BOLD1,
        BOLD2,
        ITALIC,
      ],
    },
}

for state in states.values():
  for ind,fmt in enumerate(state['fmt']):
    fmt = list(fmt)
    fmt[0] = re.compile(fmt[0])
    state['fmt'][ind] = fmt

  if 'match' in state:
    state['match'] = re.compile(state['match'])

def markup(data, **kw):
  
  state = states.get(FULL)

  lines = data.split("\n")

  skip = False
  for ind, line in enumerate(lines):

    if skip:
      skip = False
      continue

    for ns_id in state['change']:
      ns = states.get(ns_id)

      if re.match(ns['match'], line):
        state = ns
        lines.insert(ind, ns['start'])
        ind += 1
        skip = True
        break
    else:
      if 'match' in state and not re.match(state['match'], line):
        lines.insert(ind, ns['end'])
        ind += 1
        skip = True
        state = states.get(FULL)


    for pattern, sub in state['fmt']:
      line = re.sub(pattern, sub, line)


    if 'line' in state:
      pattern, sub = state['line']
      line = re.sub(pattern, sub, line)

    lines[ind] = line

  if 'end' in state:
    lines[ind] += state['end']

  data = str.join("\n", lines)

  import logging
  logging.info("kw: %r" % kw)
  assert 'board' in kw
  assert kw.get('board')

  data = data.replace("##board##", kw.get("board"))
  data = data.replace("##postid##", str(kw.get("postid")))

  return data


@contextfilter
def jinja2(ctx, post):
  kw = {
      "postid" : post.get("post"),
      "board" : ctx.get("board"),
      "data" : escape(post.get("text")),
  }
  return markup(**kw)

def install_jinja2():
  from tipfy.ext.jinja2 import get_env
  environment = get_env()
  environment.filters['wakaba'] = jinja2


if __name__ == '__main__':
  inp = """&gt;&gt;13 yoba
   *italic*
   %%spoiler%%
   %%*spoiler*%%
   %%&gt;&gt;13%%
   ```yoba neko```
      1
      2

  http://kde.org/**1**
  http://kde.org/1/

  &gt;gtfo!

   - 1
   - 2
   - *3*

  """

  ctx = {
      "board" : "b",
      "postid" : 12
  }
  ref = re.findall("&gt;&gt;([0-9]+)", inp)

  if ref:
    print ref

  print markup(inp, **ctx)
