socket = new Object();

function listen_updates(token) {

  try {
    console.log("rs: "+socket.readyState)
    console.log("id: " + socket.channelId_);
    if (socket.readyState == 1) {
      return;
    }

  } catch (err) {
    console.error("sock check err: "+err);
    // noting to do
    true;
  }

  console.log("list token " + token);

  updates = new goog.appengine.Channel(token);
  try {
    socket = updates.open();
  }  catch (err) {
    console.log("sock err " + err);
    return;
  }
  socket.onopen = function() {
    console.log("socket connected");
  };
  socket.onmessage = function(evt) {
    o = JSON.parse(evt.data);

    if (o.evt == "newpost") {

      if ($("#post-" + o.last).length > 0) {
        return;
      }

      var container = $(".thread");

      if ($(".tablepost").length != (o.count-2)) {
        var warn = $('<p class="warn">hmmm...</p>');
        container.append(warn);
      }

      var np = $(o.html);
      container.append(np);

      if(notify) {
        thread_name = "/" + _board + "/" + thread;
        notify.show("thread " + thread_name + " updated");
      }


    } else if(o.evt == "enter") {
      var now = new Date()
      inthread[o.rainbow] = now.getTime();
      refresh_inthread();
    }
    
    //np.slideUp(0).slideDown(300);


  }
}

try {
  thread;
} catch (e) {
  thread = "";
}

post_quota_level = "post_quota_ok";

post_quota = function(level) {
  if (level == undefined) {
    return;
  }

  console.log("set post level " + level);

  $("textarea#id_text").removeClass(post_quota_level);
  post_quota_level = "post_quota_"+level;

  $("textarea#id_text").addClass(post_quota_level);
}

WATCHER_TIME = 18*1000;

update_timer = null;
sendupdate = function() {
  if (thread != "") {
    $.ajax(
      {
        url: "update",
        dataType: 'json',
        type: "POST",
        success: function(data) {
          console.log(data.token);
          listen_updates(data.token);
          post_quota(data.post_quota);
          WATCHER_TIME = data.watcher_time * 1000;
        }
      }
    )
  }

  clearTimeout(update_timer);
  if(WATCHER_TIME) {
    setTimeout(sendupdate, WATCHER_TIME)
  }
  refresh_inthread();
}

inthread = new Object();

refresh_inthread = function() {
 var _inthread = new Array();
 $(".thread .watcher").remove();
 var now = new Date();
 now = now.getTime();
 for (rainbow in inthread) {
    var entertime = inthread[rainbow];

    if ((now - entertime) > WATCHER_TIME) {
      continue;
    }

    _inthread[rainbow] = entertime;
    
    var watcher_box = '<div class="watcher">'+rainbow+'</div>';
    $(".thread").append(watcher_box);


 }
 inthread = _inthread;
}

sendupdate();

sendform = function(e) {
  var button = $("#post_submit");

  if(uploading) {
    uploading = false;
    e.preventDefault();
    button.attr("disabled", "disabled");

    return;
  }
  try {
    if(socket) 
      return;
  } catch (err) {
    return;
  }


  var fields = [
    "id_name",
    "id_text",
    "id_subject",
    "upload_key"
  ]
  var data = {};

  for (var idx in fields) {
    var field = fields[idx];
    var inp_f = $("#" + field).get(0);
    if (inp_f == undefined) {
      continue
    }
    data[inp_f.name] = inp_f.value
  }

  if ($("#id_sage").attr("checked")) {
    data['sage'] = true;
  }

  unlock = function() {
    for (var idx in fields) {
      var field = fields[idx];
      var inp_f = $("#" + field).get(0);

      if (inp_f == undefined) {
        continue
      }

      inp_f.value = "";
    }
    button.removeAttr("disabled");

    $("#upload_img").show();
    $("#view_img").hide();

  }

  button.attr("disabled", "disabled");
  $.post( "post/", data, unlock)

  e.preventDefault();
  sendupdate();
}

$("form").submit(sendform);
