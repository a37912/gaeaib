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
    alert(1);
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

  $(this).mouseover( function(e) {handle_preview(postid, e)} );

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



    console.log("show");

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
  setup_post($("body"));
}); // end doc ready

