$(document).ready(function() {
  $("a.reflink").each(
    function() {
      $(this).click( function() {
        var postid = $(this).attr("postid");
        $("textarea#id_text").append(">>"+postid+" ");
      });
    }
  ); // each
  
  $(".postdata").each(
    function() {
      var html = $(this).html();
      html = html.replace(/&gt;&gt;([0-9]+)/g, 
        '<a href="#p$1">&gt;&gt;$1</a>'
      );

      html = html.replace(/(http:\/\/[^ ]*)/g, 
        '<a href="http://hiderefer.com/?$1">$1</a>' 
      );

      html = html.replace(/\*\*([^\*_]+)\*\*/g, "<b>$1</b>");
      html = html.replace(/__([^\*_]+)__/g, "<b>$1</b>");

      html = html.replace(/\*([^\*_]+)\*/g, "<i>$1</i>");
      html = html.replace(/_([^\*_]+)_/g, "<i>$1</i>");

      html = html.replace(/    (.*)/g, "<pre>$1</pre>");

      html = html.replace(/^&gt;([^&].*)/mg, '<p class="unkfunc">&gt;$1</p>');

      html = html.replace(/\n\n/g, '<br/>');

      $(this).html(html);

    } // each func
  );// each

}); // end doc ready

