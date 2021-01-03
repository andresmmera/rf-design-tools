function StringToArray(str) {
  var arr = str.split(';');
  return arr;
}


// Input power and output power (fundamental and IMn)
var Pin = StringToArray(document.getElementById("InterceptDiagram").getAttribute("data-Pin"));
var Pout = StringToArray(document.getElementById("InterceptDiagram").getAttribute("data-Pout"));
var IMn = StringToArray(document.getElementById("InterceptDiagram").getAttribute("data-IMn"));

// Noise floor
var Noise_Floor = StringToArray(document.getElementById("InterceptDiagram").getAttribute("data-Noise_Floor"));

// Intercept point
var IIPn = document.getElementById("InterceptDiagram").getAttribute("data-IIPn");
var OIPn = document.getElementById("InterceptDiagram").getAttribute("data-OIPn");
var n = document.getElementById("InterceptDiagram").getAttribute("data-n");

// Compression point
var CPi = document.getElementById("InterceptDiagram").getAttribute("data-CPi");
var CPo = document.getElementById("InterceptDiagram").getAttribute("data-CPo");

// Minimum S/I
var Pin_Upper_Limit = document.getElementById("InterceptDiagram").getAttribute("data-Pin_Upper_Limit");
var Pout_Upper_Limit = document.getElementById("InterceptDiagram").getAttribute("data-Pout_Upper_Limit");
var SI = document.getElementById("InterceptDiagram").getAttribute("data-SI");


var xmin = Pin[0]
var xmax = Pin[Pin.length - 1]

var ymin = Noise_Floor[0] 
ymin = Math.floor(ymin / 5) * 5 - 10// Round to 5dB

var ymax = Math.max(Pin[Pin.length - 1], IMn[IMn.length - 1])
ymax = Math.ceil(ymax / 5) * 5 // Round to 5dB


// Put data in pairs (Pin, Pout) for the chart representation
Pout_data = []; // Fundamental output power
IMn_data = []; // IMn output power
NF_data = []; // Noise floor data
IIPn_data = []; // Input intercept point line
OIPn_data = []; // Output intercept point line
ICP = [];  // 1dB compression point at the input
OCP = [];  // 1dB compression
SImin = []; // Minimum S/I required line

for (var t = 0; t < Pin.length; t++) {
    Pout_data.push({
      x: Pin[t],
      y: Pout[t]
    })

    IMn_data.push({
      x: Pin[t],
      y: IMn[t]
    })

    NF_data.push({
      x: Pin[t],
      y: Noise_Floor[t]
    })
    
    // Intercept point (input)
    IIPn_data.push({
      x: IIPn,
      y : ymin + t*(OIPn-ymin)/(Pin.length-1)
    })
    
    // Intercept point (output)
    OIPn_data.push({
      x: 1.*xmin + t*(IIPn-xmin)/(Pin.length-1),
      y : OIPn
    })
    
    // Compression point (input)
    ICP.push({
      x: CPi,
      y : 1.*ymin + t*(CPo-ymin)/(Pin.length-1)
    })
    
    // Compression point (output)
    OCP.push({
      x: 1.*xmin + t*(CPi-xmin)/(Pin.length-1),
      y : CPo
    })

    // Minimum S/I
    SImin.push({
      x: Pin_Upper_Limit,
      y : 1.*(Pout_Upper_Limit-SI) + t*(Pout_Upper_Limit-(Pout_Upper_Limit-SI))/(Pin.length-1)
    })

  }

/* SEE https://www.chartjs.org/docs/latest/charts/line.html */
var chLine = document.getElementById("chLine");
var chartData = {
  labels: Pin,
  datasets: [ 
              // Fundamental
              {
              label: "Pout",
              data: Pout_data,
              backgroundColor: 'transparent',
              borderColor: '#0000FF',
              borderWidth: 2,
              pointBackgroundColor: '#0000FF',
              },

              // IMn
               {
                label: "IM3",
                data: IMn_data,
                backgroundColor: 'transparent',
                borderColor: '#FF0000', // Red
                borderWidth: 2,
                pointBackgroundColor: '#FF0000'
               },

              // Noise Floor
               {
                label: "Noise floor",
                data: NF_data,
                backgroundColor: 'transparent',
                borderColor: '#FF8000', // Orange
                borderWidth: 2,
                pointBackgroundColor: '#FF8000'
               },

              // IIPn
              {
                label: "IIPn",
                data: IIPn_data,
                backgroundColor: 'transparent',
                borderColor: '#000000', // Black
                borderWidth: 2,
                pointBackgroundColor: '#000000',
                borderDash: [5]
               },

              // OIPn
              {
                label: "IP".concat(n.toString()),
                data: OIPn_data,
                backgroundColor: 'transparent',
                borderColor: '#000000', // Black
                borderWidth: 2,
                pointBackgroundColor: '#000000',
                borderDash: [5]
               },

              // CPi
              {
                label: "P1dB",
                data: ICP,
                backgroundColor: 'transparent',
                borderColor: '#006B3C', // Cadmium Green
                borderWidth: 2,
                pointBackgroundColor: '#006B3C',
                borderDash: [5]
               },

              // CPo
              {
                label: "CPo",
                data: OCP,
                backgroundColor: 'transparent',
                borderColor: '#006B3C', // Cadmium Green
                borderWidth: 2,
                pointBackgroundColor: '#006B3C',
                borderDash: [5]
               },

              // SI min
              {
                label: ('S/I = ').concat(SI.concat(' dB')),
                data: SImin,
                backgroundColor: 'transparent',
                borderColor: '#4B0082', // Indigo
                borderWidth: 2,
                pointBackgroundColor: '#4B0082',
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
                                          stepSize : 5,
                                          callback: function(value, index, values) {
                                            return parseFloat(value).toFixed(1);
                                          },
                                        },
                                  scaleLabel: {
                                          display: true,
                                          labelString: 'Input Power (dBm)'
                                        }
                                  }],
                  
                          yAxes:  [{
                                  ticks:{
                                          min : ymin,
                                          max : ymax,
                                          stepSize : 5,
                                        },
                                        scaleLabel: {
                                          display: true,
                                          labelString: 'Output Power (dBm)'
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