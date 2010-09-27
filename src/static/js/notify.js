if (window.webkitNotifications) {
  console.log("Notifications are supported!");
}
else {
  console.log("Notifications are not supported for this Browser/OS version yet.");
}


var _title = document.title, waiting, notifier = null, notify = false;

$(window)
   .bind("blur", function() {waiting = true;})
   .bind("focus", function() { 
     waiting = false; 
     if (notifier) notifier.cancel(); 
     document.title = _title;
    });


if (window.webkitNotifications) {
  if (window.webkitNotifications.checkPermission() == 0 && notify) {
    if (notifier) notifier.cancel();
    notifier = window.webkitNotifications.createNotification("", _title, $(message).text());
    notifier.show();
  }
}

document.title = " ★ " + _title + " ★ ";