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
 
  $(".postdata").each(
    function() {
      var html = $(this).html();
      html = html.replace(/&gt;&gt;([0-9]+)/g, 
        '<a postid="$1" class="postref" href="/'+_board+'/p$1">&gt;&gt;$1</a>'
      );



      html = html.replace(/\*\*([^\*_]+)\*\*/g, "<b>$1</b>");
      html = html.replace(/__([^\*_]+)__/g, "<b>$1</b>");

      html = html.replace(/\*([^\*_]+)\*/g, "<i>$1</i>");

      html = html.replace(/    (.*)/g, "<pre>$1</pre>");
      html = html.replace(/\%\%(.*)\%\%/g, '<span class="spoiler">$1</span>');

      html = html.replace(/^&gt;([^&].*)/mg, '<p class="unkfunc">&gt;$1</p>');

      html = html.replace(/\n/g, '<br/>');

      html = html.replace(/(http:\/\/[^ <\n]*)/g, 
        '<a href="http://hiderefer.com/?$1">$1</a>' 
      );
      $(this).html(html);

    } // each func
  );// each

  show_preview = function(np, post, e) {

    np.addClass("preview");
    np.addClass("preview_"+post);
    np.css("position", "absolute");
    np.css("left", (e.pageX+15)+"px");
    np.css("top",  e.pageY+"px");
    np.find(".doubledash").remove();

    console.log("show");

    $('body').append(np);
    //np.slideUp(0).slideDown(500);
    np.show();
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
    var np = make_post(data);

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

  make_post = function(o) {
    var np =  $("#post_template").clone();

    np.find(".postdata").text(o.text);
    np.find(".commentpostername").text(o.name);
    np.find(".rb").html(o.rainbow_html);
    np.find(".time").text(o.time);

    var ref = np.find("a.reflink");
    ref.text("#"+o.post);
    ref.attr("name", "p"+o.post);
    ref.attr("href", "#p"+o.post);


    if (! o.sage ) {
      np.find(".sg").remove();
    }

    console.log("img: " + o.image);

    if (o.image) {
      console.log("got img");
      np.find(".filesize").text("Image " + o.image.content_type  + ": " + o.image.size  );
      np.find("a.thumb").attr("href", o.image.full);
      np.find("img.thumb").attr("src", o.image.thumb);
      console.log("set img");

    } else {
      console.log("no img, remove");

      np.find(".filesize").remove();
      np.find(".thumb").remove();
      np.find("#imgbr").remove();

    }

    return np;

  }
  no_preview = false;
  no_preview_hide = false;
  preview_cache = new Object();

  $("a.postref").each(
    function() {
      var postid = $(this).attr("postid");

      $(this).mouseover( function(e) {
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
              preview(e,d,s);
            },
            dataType: 'json',
          }
        );

        }
      )

    }
  );

 
}); // end doc ready

