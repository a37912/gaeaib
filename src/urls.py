from tipfy import Rule


def get_rules():
  return [
    Rule( 
      "/", 
      endpoint="index", 
      handler="aib.views.Index"
    ),
    Rule( 
      "/<board>/", 
      endpoint = "board",
      handler = "aib.views.Board"
    ),
    Rule( 
      "/<board>/post/", 
      endpoint = "board:post",
      handler = "aib.views.Post",
      defaults = {"thread" : "new" }
    ),
    Rule( 
      "/<board>/<int:thread>/", 
      endpoint = "board",
      handler = "aib.views.Thread"
    ),
    Rule( 
      "/<board>/<int:thread>/post/", 
      endpoint = "board",
      handler = "aib.views.Post"
    ),
    Rule(
      "/post_url",
      endpoint = "posturl",
      handler = "aib.views.PostUrl",
    ),

    Rule(
      "/post_img",
      endpoint = "postimg",
      handler = "aib.views.PostImage",
    ),
    Rule(
      "/post_img/<img>",
      endpoint = "postimg",
      handler = "aib.views.PostImage",
    ),
    Rule(
      "/img/<img>",
      endpoint = "img",
      handler = "aib.views.ViewImage",
    ),


  ]
