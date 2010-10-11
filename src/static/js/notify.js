function delegate( that, thatMethod ) { return function() { return thatMethod.call(that); } }

function Notify() {
  this.focus = null; // hmmm
  this.notifier = null;
  this.msg = null;
  this.title_back = document.title;
  this.n = window.webkitNotifications;

  __obj = this;

  $(window)
    .bind("blur", function() { 
        __obj.focus = false;
    } )
    .bind("focus", function() {
        __obj.focusin();
    } 
    ) 

  this.prototype = this.__proto__;

  this.prototype.blem = function () {
    document.title = __obj.title_back;

    if(this.focus == true) {
          console.log("focus, ret");
          return;
    }

    setTimeout(delegate(this,this.blom), 1000);

  }
  this.prototype.blom = function () {

    if(this.focus == true) {
          console.log("focus, ret");
          return;
    }

    document.title = "#! " + __obj.title_back;

    setTimeout(delegate(this,this.blem), 1000);

  }


  this.prototype.show = function(msg) {
    
    /* // hmmm
    if (this.focus) {
      return;
    } */

    console.log(this.title_back);
    document.title = "#! " + __obj.title_back;

    setTimeout(delegate(this,this.blem), 1000);
        
    this.msg = msg;

    if(! this.n) {
      console.log("fuck the notify");
      return;
    }

    if( this.n.checkPermission() == 0) {
      this.show_notify()
    } else {
      console.log("req perm");
      this.req();
    }

  }

  this.prototype.req = function(msg) {
    this.n.requestPermission( delegate(this, this.show_notify))
  }

  this.prototype.show_notify = function(msg) {
    if( this.n.checkPermission() != 0) {
      return;
    }

    if(! this.msg) {
      return;
    }
    this.notifier = this.n.createNotification("", this.title_back, this.msg);
    this.notifier.show();
  }

  this.prototype.focusin = function() {
    this.focus = true;

    if (this.notifier) {
      this.notifier.cancel();
      this.notifier = null;
    }

    document.title = this.title_back;

  }

}

notify = new Notify();
