socket = new Object();

try {
 ls = window['localStorage'];
} catch(err) {
 ls = new Object();
}

th_key = _board + "/" + thread;


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

    message(evt.data);

  }
}

function message(data) {

    o = JSON.parse(data);

    if (o.evt == "newpost") {

      if(thread != '') {
        var container = $(".thread");
      } else {
        var container = $("#postarea");
      }

      if(notify) {
        thread_name = "/" + o.board + "/" + o.thread;
        notify.show("thread " + thread_name + " updated");
      }

      if( (o.thread != thread) || (o.board != _board)) {
          var msg = 'new post in <a href="/' + o.board + "/"+  o.thread + '/">>>/'+o.board+'/'+o.thread+'</a>';
          var warn = $('<p class="warn">' + msg + '</p>');

          container.append(warn);

          ls[o.board+'/'+o.thread] = data;

          return;
      }

      if ($("#post-" + o.last).length > 0) {
        return;
      }


      if ($(".tablepost").length != (o.count-2)) {
        var warn = $('<p class="warn">hmmm...</p>');
        container.append(warn);
      }

      var np = $(o.html);
      container.append(np);
      setup_post(np);

      
      refresh_online(refresh_online.last_online);

    }  else if (o.evt == "online") {

        refresh_online(o.rb);
        refresh_online.last_online = o.rb;

    }
}

try {
  thread;
} catch (e) {
  thread = "";
}

refresh_online = function(online) {
  for (x in online) {
    $('.rainbow-'+online[x]).addClass('rainbow-online');
  }

  $('.rainbow-online').each(function() {
      for(x in online) {
          if ($(this).hasClass('rainbow-'+online[x])) {
              return;
          }
      }

      $(this).removeClass('rainbow-online');
    }
  )
};

refresh_online.last_online = [];

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

sendupdate = function() {

  var date = new Date();

  if(ls['open'] > date.getTime() - 2000) {
    return;
  }

  ls['open'] = date.getTime() + 10000;

  $.ajax(
      {
        url: "update",
        dataType: 'json',
        type: "POST",
        success: function(data) {
          console.log(data.token);
          if(data.token) {
            listen_updates(data.token);
          } else {
            console.log("dont listen");
          }
          post_quota(data.post_quota);
        }
      }
  )

}

sendupdate();

inthread = new Object();

sendform = function(e) {
  var button = $("#post_submit");

  try {
    _gaq.push(['_trackPageview', "/post/"]);
    _gaq.push(['_trackPageview', "/"+_board+"/post" ]);

  } catch(err) {
    console.err("gaq fail " + err);
  }

  if(uploading) {
    uploading = false;
    e.preventDefault();
    button.attr("disabled", "disabled");

    return;
  }
  try {
    if(socket.readyState != 1) 
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
    if (inp_f == undefined || !inp_f.value || inp_f.value=="") {
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
    $("#postarea").removeClass("sending");

    $("#upload_img").show();
    $("#view_img").hide();

  }

  button.attr("disabled", "disabled");
  $("#postarea").addClass("sending");
  $.post( "post/ajax", data, unlock)

  e.preventDefault();
  sendupdate();
}

function ls_loop() {
    var date = new Date();

    if(socket.readyState == 1) {
        ls['open'] = date.getTime();
    } else {
        if(ls['open']  < (date.getTime() - 3427)) {
          sendupdate();
        }
    }

    var data = ls.getItem(th_key);

    if(data) {
        message(data);

        ls.removeItem(th_key);
    }

    setTimeout(ls_loop, 100);
}

ls_loop();

$("form").submit(sendform);

markup_preview = function(data) {
  $("#testpost").html(data.html);

};

testpost = function() {
  $.ajax( 
    {
      url: "/api/markup",
      dataType : "json",
      type : "POST",
      success : markup_preview,
      data : {
        "text" : $("#id_text").val()
      }
    }
  );
}

$("#post_preview").click(testpost);
$("#id_text").blur(testpost);
