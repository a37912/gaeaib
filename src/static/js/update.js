function listen_updates(token) {
  console.log("list token " + token);

  updates = new goog.appengine.Channel(token);
  socket = updates.open();
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


    }
    
    //np.slideUp(0).slideDown(300);


  }
}

try {
  thread;
} catch (e) {
  thread = "";
}

if (thread != "") {
  $.ajax(
    {
      url: "update",
      dataType: 'json',
      type: "POST",
      success: function(data) {
        console.log(data.token);
        listen_updates(data.token);
      }
    }
  )
}

sendform = function(e) {
  var button = $("#post_submit");

  if(uploading) {
    uploading = false;
    e.preventDefault();
    button.attr("disabled", "disabled");

    return;
  }
  try {
    socket;
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

  }

  button.attr("disabled", "disabled");
  $.post( "post/", data, unlock)

  e.preventDefault();
}

$("form").submit(sendform);
