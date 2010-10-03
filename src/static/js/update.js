function listen_updates(token) {
  console.log("list token " + token);

  updates = new goog.appengine.Channel(token);
  var socket = updates.open();
  socket.onopen = function() {
    console.log("socket connected");
  };
  socket.onmessage = function(evt) {
    o = JSON.parse(evt.data);

    if (o.evt == "newpost") {
      var np = $(o.html);
      var container = $(".thread");
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
