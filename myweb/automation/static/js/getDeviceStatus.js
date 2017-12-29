function getDeviceStatus() {
  $.get("/auto/getDeviceStatus", function(ret){
    $("#getMyDevice").html(ret)
  });
};

getDeviceStatus();
