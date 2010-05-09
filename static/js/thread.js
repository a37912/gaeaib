$(document).ready(function() {
  $("a.reflink").each(
    function() {
      $(this).click( function(e) {
        var postid = $(this).attr("postid");
        var textarea = $("textarea#id_text").get(0);
        var text = ">>"+postid+" ";

        textarea.value+=text;
        textarea.focus();

        e.preventDefault();

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

