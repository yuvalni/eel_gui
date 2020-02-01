
eel.expose(get_RT_data);
function get_RT_data(T,R) {
  myChart.data.datasets[0].data.push({x:T,y:R})
  //myChart.options.scales.xAxes
  myChart.update()
  //var temp_cur = document.getElementById("temp_cur");
  //temp_cur.value = T
  //var temp_status = document.getElementById("temp_status");
  //temp_status.value = R
}
//var data_timer = setInterval(get_data, 1000);
function get_data(){
  $.get("/stream_temp_status", function(data, status){
  var temp_cur = document.getElementById("temp_cur");
  var temp_status = document.getElementById("temp_status");
  temp_cur.value = data["temp"]
  temp_status.value = data["status"]
});
};


function SubmitTempSet() {
var setpoint = $("#temp_setpoint").val();
var rate = $("#temp_rate").val();
var mode = $("#temp_mode").val()[0];
eel.set_temperature_settings(setpoint,rate,mode)
};

function startMeasure(){
  //eel.measure_rand();
  start_temp = document.getElementById("meas_start_temp").value
  end_temp = document.getElementById("meas_end_temp").value
  rate = document.getElementById("meas_rate").value
  current = document.getElementById("set_current").value
  voltage_comp = document.getElementById("voltage").value
  nplc_speed = document.getElementById("nplc").value
  eel.start_RT_sequence(start_temp,end_temp,rate,current,voltage_comp,nplc_speed,'test.csv')
};


eel.expose(toggle_start_measure);
function toggle_start_measure(){
  document.getElementById("start_measure").disabled = ! document.getElementById("start_measure").disabled
};
