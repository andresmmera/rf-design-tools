function StringToArray(str) {
  var arr = str.split(';');
  return arr;
}

// LO frequency
var f_LO = StringToArray(document.getElementById("IM_IF_Diagram").getAttribute("data-f_LO"));

// Image frequency data vs LO frequency
var f_IM = StringToArray(document.getElementById("IM_IF_Diagram").getAttribute("data-f_IM"));

// IF data vs LO frequency
var f_IF = StringToArray(document.getElementById("IM_IF_Diagram").getAttribute("data-f_IF"));

// Difference between the IF and the image frequency vs LO frequency
var delta_IM_IF = StringToArray(document.getElementById("IM_IF_Diagram").getAttribute("data-delta_IM_IF"));

// RF frequency - It's needed to the position of the low-side/high.side injection text
var f_RF = document.getElementById("IM_IF_Diagram").getAttribute("data-f_RF");

// Chart limits
var xmin = f_LO[0]
var xmax = f_LO[f_LO.length - 1]
var ymin = 0
var ymax = Math.round(f_IM[f_IM.length - 1])


// Put data in pairs (f_LO, fx) for the chart representation
f_IM_data = []; // IM frequency
f_IF_data = []; // IF frequency
delta_IM_IF_data = []; // Difference |f_IF - f_IM|


for (var t = 0; t < f_LO.length; t++) {
  f_IM_data.push({
      x: f_LO[t],
      y: f_IM[t]
    })

  f_IF_data.push({
      x: f_LO[t],
      y: f_IF[t]
    })

    delta_IM_IF_data.push({
      x: f_LO[t],
      y: delta_IM_IF[t]
    })
  }


  /* SEE https://www.chartjs.org/docs/latest/charts/line.html */
var chLine = document.getElementById("chLine");
var chartData = {
  labels: f_LO,
  datasets: [ 
              // Image frequency
              {
              label: "Image frequency",
              data: f_IM_data,
              backgroundColor: 'transparent',
              borderColor: '#0000FF',
              borderWidth: 2,
              pointBackgroundColor: '#0000FF',
              lineTension: 0
              },

              // IF frequency
               {
                label: "IF",
                data: f_IF_data,
                backgroundColor: 'transparent',
                borderColor: '#FF0000', // Red
                borderWidth: 2,
                pointBackgroundColor: '#FF0000',
                lineTension: 0
               },

              // Delta IM-IF
               {
                label: "|RF-IM|",
                data: delta_IM_IF_data,
                backgroundColor: 'transparent',
                borderColor: '#FF8000', // Orange
                borderWidth: 2,
                pointBackgroundColor: '#FF8000',
                lineTension: 0
               },
]
};


if (chLine) {
  options = 
  {
    type: 'line',
    data: chartData,
    options: {responsive: true,
      maintainAspectRatio:false,
                title: {
                  display: true,
                  text: 'Image Frequency Diagram for RF = ' + f_RF.toString() + ' MHz'
                },
                elements: {
                          point:{
                                  radius: 0
                                }
                          },
                scales: {
                          xAxes:  [{
                                  type: "linear",
                                  ticks:{
                                          min : xmin,
                                          max : xmax,
                                          stepSize : 50,
                                          callback: function(value, index, values) {
                                            return parseFloat(value).toFixed(1);
                                          },
                                        },
                                  scaleLabel: {
                                          display: true,
                                          labelString: 'LO frequency (MHz)'
                                        }
                                  }],
                  
                          yAxes:  [{
                                  ticks:{
                                          min : ymin,
                                          max : ymax,
                                          stepSize : 50,
                                        },
                                        scaleLabel: {
                                          display: true,
                                          labelString: 'frequency (MHz)'
                                        }
                                  }]
                        },
                  legend: {
                            display: true,
                            labels: {
                              filter: function(item, chart) 
                              {
                                  // Logic to remove a particular legend item goes here
                                  return !item.text.includes('IIPn') & !item.text.includes('CPo');
                              }
                            }
                          }
              }
    }
  new Chart(chLine, options);
}