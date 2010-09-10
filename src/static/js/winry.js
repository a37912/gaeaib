function winry_mode() {
  $("a.reflink").each(
    function() {
      $(this).click( function(e) {
        var postid = $(this).attr("postid");
        var thread = $(this).attr("threadid");

        var url = "/winry/delete/"+_board+"/"+thread+"/"+postid;

        $.ajax(
          {
            url: url,
            type: 'POST',
          }
        );
      }
      )
    }

  )
  $("a.reply").each(
    function() {
      var url = $(this).attr("href");
      $(this).attr("href", url+"?winry");
    }
  )
}
var loc = window.location.toString();

if ( loc.indexOf("?winry") != -1) {
  $(document).ready(winry_mode);
}
