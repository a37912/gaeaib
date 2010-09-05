from tipfy import Rule


def get_rules():
  return [
    Rule( 
      "/", 
      endpoint="index", 
      handler="aib.ib.Index"
    ),
    Rule( 
      "/<board>/", 
      endpoint = "board",
      handler = "aib.ib.Board"
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
      "/api/<any(thread,post):mode>/<board>/<int:num>",
      endpoint = "api",
       handler = "aib.api.ApiCacheGeneric",
    ),
    Rule(
      "/api/<any(lastpost,threadlist):mode>/<board>",
      endpoint = "api",
       handler = "aib.api.ApiCacheGeneric",
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
