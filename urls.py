from tipfy import Rule


def get_rules():
  return [
    Rule( 
      "/$", 
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

  ]
