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
          return;
        }

        $("#upload_img").val("");
        $("#upload_img").change(do_up);

        $("#upload_key").val(data.img);
        var img = $("#view_img");
        img.attr("src", "/img/"+data.img);
        $("#view_img_msg").hide();
        img.show();
        if (! uploading ) {
          $("form").submit();
        }
        uploading = false;
      },
      error: function (data, status, e) 
      {
        $("#upload_img").show();
        $("#upload_img").change(do_up);
        alert(status + " err " + e);
        uploading = false;
      }
    }
  )
}

do_up = function() {
  uploading = true;
  $("#upload_img").hide();

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
$("#upload_img").show();
$("#view_img_nojs").hide();

uploading = false;
