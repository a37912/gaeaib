from tipfy import Rule


def get_rules():
  return [
    Rule(
      "/_ah/warmup",
      handler="warmup.Do"
    ),
    Rule( 
      "/", 
      endpoint="index", 
      handler="aib.ib.Index",
      defaults = {"tpl" : "index.html" }
    ),
    Rule( 
      "/api", 
      endpoint="index", 
      handler="aib.ib.Index",
      defaults = {"tpl" : "api.html" }
    ),
    Rule( 
      "/faq", 
      endpoint="index", 
      handler="aib.ib.Index",
      defaults = {"tpl" : "faq.html" }
    ),
    Rule( 
      "/contacts", 
      endpoint="index", 
      handler="aib.ib.Index",
      defaults = {"tpl" : "contacts.html" }
    ),
    Rule( 
      "/about", 
      endpoint="index", 
      handler="aib.ib.Index",
      defaults = {"tpl" : "about.html" }
    ),
    Rule(
      "/xmpp",
      endpoint="index",
      handler="aib.ib.Index",
      defaults = {"tpl" : "xmpp.html" }
    ),

    Rule( 
      "/boardlist", 
      endpoint="list", 
      handler="aib.ib.Boardlist",
    ),
    Rule( 
      "/<board>/", 
      endpoint = "board",
      handler = "aib.ib.Board"
    ),
    Rule( 
      "/<board>/page<int:page>", 
      endpoint = "board",
      handler = "aib.ib.Board"
    ),
    Rule( 
      "/<board>/p<int:post>/", 
      endpoint = "board:postredirect",
      handler = "aib.ib.PostRedirect",
    ),
    Rule( 
      "/<board>/post/", 
      endpoint = "board:post",
      handler = "aib.ib.Post",
      defaults = {"thread" : "new" }
    ),
    Rule( 
      "/<board>/<int:thread>/", 
      endpoint = "board",
      handler = "aib.ib.Thread"
    ),
    Rule( 
      "/<board>/<int:thread>/post/", 
      endpoint = "board",
      handler = "aib.ib.Post"
    ),
    Rule( 
      "/<board>/<int:thread>/post/ajax", 
      endpoint = "board",
      handler = "aib.ib.AjaxPost",
    ),
    Rule( 
      "/<board>/<int:thread>/update", 
      endpoint = "board:update",
      handler = "aib.api.UpdateToken",
    ),
    Rule( 
      "/<board>/<int:thread>/rss", 
      endpoint = "board:update",
      handler = "aib.rss.ViewThread",
    ),
    Rule(
      "/delete/<board>/<int:thread>/<int:post>",
      endpoint = "board",
      handler = "aib.ib.DeletePost",
    ),
    Rule(
      "/post_url",
      endpoint = "posturl",
      handler = "aib.upload.PostUrl",
    ),

    Rule(
      "/post_img",
      endpoint = "postimg",
      handler = "aib.upload.PostImage",
    ),
    Rule(
      "/post_img/<img>",
      endpoint = "postimg",
      handler = "aib.upload.PostImage",
    ),
    Rule(
      "/img/<img>",
      endpoint = "img",
      handler = "aib.upload.ViewImage",
    ),
    Rule(
      "/api/board/<board>",
      endpoint = "api:board",
      handler = "aib.api.ApiBoard",
    ),
    Rule(
      "/api/boardlist",
      endpoint = "api:boardlist",
      handler = "aib.api.ApiBoardList",
    ),
    Rule(
      "/api/boardbump",
      handler = "aib.api.ApiBoardBumped",
    ),
    Rule(
      "/api/post/<board>/<int:num>",
      endpoint = "api:post",  
      handler = "aib.api.ApiPost",
    ),

    Rule(
      "/api/thread/<board>/<int:num>",
      endpoint = "api:threadlist",
      handler = "aib.api.ApiThread",
    ),
    Rule(
      "/api/lastpost/<board>",
      endpoint = "api:lastpost",
       handler = "aib.api.ApiLastPost",
    ),
    Rule(
      "/api/threadlist/<board>",
      endpoint = "api",
       handler = "aib.api.ApiThreadList",
    ),
    Rule(
      "/api/lastblob",
      handler = "aib.api.ApiLastImage",
    ),
    Rule(
      "/api/markup",
      handler = "aib.api.ApiMarkup",
    ),
    Rule(
      "/winry/delete/<board>/<int:thread>/<int:post>",
      endpoint = "admin:delete",
      handler = "aib.api.Delete",
    ),
    Rule(
     "/winry/unban/<ip>",
      endpoint = "admin:delete",
      handler = "aib.api.Unban",
    ),
    Rule(
      "/winry/clean_blob",
      endpoint = "cron:clean",
      handler = "aib.clean.CleanBlob"
    ),
    Rule(
      "/winry/clean_thread",
      endpoint = "cron:clean:thread",
      handler = "aib.clean.CleanThread"
    ),
    Rule(
      "/winry/clean_cache",
      handler = "aib.clean.CleanCache"
    ),
    Rule(
      "/winry/clean_board",
      handler = "aib.clean.CleanBoard"
    ),
    Rule(
      "/winry/render_cache",
      handler = "aib.rerender.RenderCache"
    ),
    Rule(
      '/_ah/queue/deferred',
      endpoint = 'tasks/deferred',
      handler = 'tipfy.ext.taskqueue:DeferredHandler'
    ),
    Rule(
      '/_ah/prospective_search',
      handler = 'aib.matcher.Handle',
    ),

    Rule(
      '/_ah/channel/<any(connected,disconnected):mode>/',
      handler = 'aib.ib.ClientHandler',
    ),
    Rule(
      "/_ah/xmpp/subscription/subscribe/",
      handler = 'xmppib.handlers.SubRequest',
    ),
    Rule(
      "/_ah/xmpp/message/chat/",
       handler = 'xmppib.handlers.Post',
    ),
    
  ]
