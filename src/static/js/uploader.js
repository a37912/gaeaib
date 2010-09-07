function upload_to(url) {
  $.ajaxFileUpload(
    {
      url: url,
      secureuri:false,
      fileElementId:'upload_img',
      dataType: 'json',
      success: function (data, status) 
      {
        if (data.err) {
          alert(data.err);
          $("#upload_img").change(do_up);
          return;
        }
        $("#upload_img").remove();
        $("#upload_key").val(data.img);
        var img = $("#view_img");
        img.attr("src", "/img/"+data.img);
        $("#view_img_msg").hide();
        img.show();
      },
      error: function (data, status, e) 
      {
        $("#upload_img").change(do_up);
        alert(data);
        alert(status + " err " + e);
      }
    }
  )
}

do_up = function() {
  $("#view_img_msg").show();
  $.ajax(
    {
      url: "/post_url",
      success: function(data) {
        upload_to(data)
      }
    }
  )
}

$("#upload_img").change(do_up);

