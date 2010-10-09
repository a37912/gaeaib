$(document).ready(function() {

  var loc = window.location.toString();
  // temp
  try {
    if(_board==undefined) {
      true;
    } 
  } catch (e) { 
    var st = loc.indexOf("/",7)+1;
    var ed = loc.indexOf("/", st);

    _board = loc.substring(st, ed);
  }

  insertlink = function(postnnum) {
    var _postnum = postnnum;
    var textarea = $("textarea#id_text").get(0);
    var text = ">>"+_postnum+" ";

    textarea.value+=text;
  }
  var dash = loc.indexOf("#");
  if (dash != -1) {
    var postnum = loc.substring(dash+2,loc.length);
    insertlink(postnum);
  }
  $("a.reflink").each(
    function() {
      $(this).click( function(e) {
        var postid = $(this).attr("postid");

        insertlink(postid);

        if (!_reply) {
          e.preventDefault();
        }

      });
    }
  ); // each
 
  show_preview = function(np, post, e) {

    console.log(np);
    np.removeAttr("id");
    np.addClass("preview");
    np.addClass("preview_"+post);
    np.css("position", "absolute");
    np.css("left", 0);
    np.css("top",  e.pageY+"px");
    np.find(".doubledash").remove();

    console.log("show");

    $('body').append(np);
    console.log("show!");

    console.log(np.show);
    //np.slideUp(0).slideDown(500);
    var _x ;
    if( (e.pageX + np.width()) > $(window).width()) {
      _x = $(window).width() - np.width() - 5;
    } else {
      _x = e.pageX+15;
    }

    np.css("left", _x+"px");
    np.css("opacity", 1);
    np.css("-webkit-box-shadow", "0 0 12px #999999");
    do_hide =  function() {
        preview_hide(post);
    }
    np.click(do_hide);
    np.mouseleave(do_hide);

    setTimeout(function() { 
      no_preview_hide = false;
      }, preview_hide_time * 3
    );

  }

  preview = function(e, data, status) {

    console.log("show");
    var np = $(data.full_html);

    show_preview(np, data.post, e);

  }

  preview_hide_time = 3*300;
  preview_hide = function(postid) {
    console.log("hide " + postid);

    $(".preview").css("opacity",0);

    setTimeout(function() { 
      $(".preview").remove();
      no_preview = false; 
    }, 1*1000
    ) ;
  }

  no_preview = false;
  no_preview_hide = false;
  preview_cache = new Object();
  handle_preview = function(postid, e) {
        if (no_preview) {
          return;
        }
        no_preview = true;
        no_preview_hide = true;

        var copy = $("#post-"+postid);

        if(copy.length!=0) {
          console.log("copy");
          copy = copy.clone();
          return show_preview(copy, postid, e);
        }

        var key = _board+"/"+postid;
        var cache = preview_cache[key];
        if (cache) {
          return preview(e,cache, "ok");
        }

        var url = "/api/post/"+_board+"/"+postid;

        $.ajax(
          {
            url : url,
            success: function(d,s) {
              console.log("set cache");
              preview_cache[key] = d;
              if(d) {
                preview(e,d,s);
              }
            },
            dataType: 'json',
          }
        );

        }
  $("a.postref").each(
    function() {
      var postid = $(this).attr("postid");

      $(this).mouseover( function(e) {handle_preview(postid, e)} );

    }
  );

 
}); // end doc ready

