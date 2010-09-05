from tipfy import Rule


def get_rules():
  return [
    Rule( 
      "/main/", 
      endpoint="index", 
      handler="aib.ib.Index",
      defaults = {"tpl" : "index.html" }
    ),
    Rule( 
      "/list/", 
      endpoint="list", 
      handler="aib.ib.Index",
      defaults = {"tpl" : "list.html" }
    ),
    Rule( 
      "/<board>/", 
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
      "/winry/delete/<board>/<int:thread>/<int:post>",
      endpoint = "admin:delete",
      handler = "aib.api.Delete",
    ),
    Rule(
     "/winry/unban/<ip>",
      endpoint = "admin:delete",
      handler = "aib.api.Unban",
    ),


  ]
