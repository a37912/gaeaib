c = function(key, val) {
  $.cookie(key, val, {path:"/", expires: 356});
}

function DrawRainbow(colors, elementId, face){
  var canvas = document.getElementById(elementId);
  if (canvas.getContext){  
    var c = canvas.getContext('2d');
    var s = 20
    var x = s/2;
    var y = s/2;
    var r = s;
    var d = 0.05; //delta to remove stitch between sections  
    var startAngle = 0;
    for(var j=0;j<6;j++){
      var endAngle = Math.PI*(j*0.33-0.1);
      c.beginPath();
      c.moveTo(x, y);
      c.fillStyle = colors[j];
      c.arc(x, y, r, startAngle, endAngle, false);
      startAngle = endAngle-d;
      c.moveTo(x, y);
      c.closePath();
      c.fill();
    }
    if (face != null){
      c.drawImage(face,2,2,face.width,face.height);
    }
  } else {  
    // canvas-unsupported code here
    //
    //
    var oldrainbow = '';
    for(var j=0;j<5;j++){
      oldrainbow += "<span style='background: none repeat scroll"+ 
       colors[j] + "'>&nbsp;&nbsp;</span>"
    }
    canvas.innerHTML(oldrainbow);
  }
}

rainbow_draw_span = function() 
{

  var rainbow = $(this).attr("rainbow");
  var canvas_id = $(this).attr("cid");
  var hex = [];
  for(i=0;i<rainbow.length;i=i+3){
    hex.push("#"+rainbow.substring(i,i+3));
  }
  if (typeof overlay=="undefined"){ //XXX: global variable, yes its should be fixed 
    DrawRainbow(hex, "rc-"+canvas_id);
  } else {
    DrawRainbow(hex, "rc-"+canvas_id, overlay || null);
  }
}
set_postref_preview =function() {
  console.log("set reflink")
  var postid = $(this).attr("postid");
  var board=$(this).attr("board") || _board;

  $(this).mouseover( function(e) {handle_preview(postid, board, e)} );

}
set_reflink_handler = function() {
  $(this).click( function(e) {
    var postid = $(this).attr("postid");

    insertlink(postid);

    if (!_reply) {
      e.preventDefault();
    }

  });
}

setup_post = function(ct) {
  ct.find("a.postref").each(set_postref_preview);
  ct.find("span.rainbow").each(rainbow_draw_span); 
  ct.find("a.reflink").each(set_reflink_handler);
  ct.find("a.fullimg").prettyPhoto(
      {
        theme:'dark_rounded',
        overlay_gallery: false

      }
  );
  
  var format = function(date)
  {
      return date.toLocaleString();
  };

  switch( $.cookie("clock") ) {
    case "easy":
      ct.find("time.posttime").easydate({
        units:units,
        uneasy_format: format  });
      break;
    case "":
    case undefined:
    case "local":
      ct.find("time.posttime").easydate({
        units:[],
        uneasy_format: format
      });
      break;
  } ;
};

set_style = function(name) {
  if (!name) {
    return;
  }


  if(typeof(name) != "string") {
    name = $(this).attr("set");
  }

  $("link.style[rel|=stylesheet]").each(function() {
    $(this).attr(
      "href", 
      "/static/css/"+name+".css?"+$(this).attr("ver")
    );
    }
  );

  c("style", name);

  return true;
};

if($.cookie) {
  set_style($.cookie("style"));
}

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
 
  show_preview = function(np, post, e) {

    console.log(np);
    np.removeAttr("id");
    np.addClass("preview");
    np.addClass("preview_"+post);
    np.css("position", "absolute");
    np.css("left", 0);
    np.css("top",  e.pageY+"px");
    np.find(".doubledash").remove();

    np.find("canvas").attr("id", "rc-"+post+"-preview");
    np.find("span.rainbow").attr("cid", post+"-preview");

    np.find(".post-replies canvas").attr("id", "rc-"+post+"r-preview");
    np.find(".post-replies span.rainbow").attr("cid", post+"r-preview");



    console.log("show");

    $('.previewstat').remove();
    $('body').append(np);
    setup_post(np);
    console.log("show!");

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
  handle_preview = function(postid, board, e) {
        if (no_preview) {
          return;
        }
        no_preview = true;
        no_preview_hide = true;

        var copy = $("#post-"+postid);

        if(board==_board && copy.length!=0) {
          console.log("copy");
          copy = copy.clone();
          return show_preview(copy, postid, e);
        }

        var key = board+"/"+postid;
        var cache = preview_cache[key];
        if (cache) {
          return preview(e,cache, "ok");
        }

        // move out
        var stat = $("<div/>");
        stat.addClass("previewstat nothumb");
        stat.text("...");

        stat.css("position", "absolute");

        stat.css("top", e.pageY+"px");
        stat.css("left", e.pageX+"px");

        $("body").append(stat);



        var url = "/api/post/"+board+"/"+postid;

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
            error: function(d,s) {
              no_preview = false;

              stat.text("error");

              setTimeout(function() {
                stat.remove();
                }, 3000
              );

            }
          }
        );

        }
  setup_post($("body"));

  if(typeof(boardbump) != "undefined") {
    for(boardcode in boardbump) {
      boardcode = boardbump[boardcode];
      var blink = $("<a></a>");
      var name =  "/" + boardcode;
      blink.attr("href", name+"/");
      blink.text(name.substr(0, 4)+"/");
      console.log("name " + name)
      console.log("code " + boardcode)

      var menulen = $("#topmenu a").length

      $("#topmenu a").slice(-2,-1).after("<b> | </b>")
      $("#topmenu b").last().after(blink)
    }
  }

  $("a.setstyle").click ( set_style );

}); // end doc ready

$.easydate.locales.ruRU = {
  "future_format": "%s %t",
  "past_format": "%t %s",
  "second": ["секунду", "секунды", "секунд"],
  "minute": ["минуту", "минуты", "минут"],
  "hour": ["час", "часа", "часов"],
  "day": ["день", "дня", "дней"],
  "week": ["неделю", "недели", "недель"],
  "month": ["месяц", "месяца", "месяцев"],
  "year": ["год", "года", "лет"],
  "yesterday": "вчера",
  "tomorrow": "завтра",
  "now": "сейчас",
  "ago": "назад",
  "in": "в"
};
$.easydate.__ = function(str, n, settings) {
  if(isNaN(n)) {
    return $.easydate.locales.ruRU[str];
  }

  var plural=-1;

  if(n%10==1 && n%100!=11) {
   plural =  0 
  } else {
    if(n%10>=2 && n%10<=4 && (n%100<10 || n%100>=20)) {
      plural = 1;
    } else {
      plural = 2
    }
  }


  ret= $.easydate.locales.ruRU[str][plural];

  return ret;
}
units = [
    { name: "now", limit: 5 },
    { name: "second", limit: 60, in_seconds: 1 },
    { name: "minute", limit: 3600, in_seconds: 60 },
    { name: "hour", limit: 3600*3, in_seconds: 3600  },
]; 


