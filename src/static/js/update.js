updates = new goog.appengine.Channel(token);
var socket = updates.open();
socket.onopen = function() {
  console.log("socket connected");
};
socket.onmessage = function(evt) {
  o = JSON.parse(evt.data);
  console.log(o.text);
  var np =  $("#post_template").clone();
  var container = $(".thread");

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

  container.append(np);

  np.show();


}

