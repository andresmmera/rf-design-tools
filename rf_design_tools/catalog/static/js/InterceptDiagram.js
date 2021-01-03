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
var IIP3 = document.getElementById("InterceptDiagram").getAttribute("data-IIPn");
var OIP3 = document.getElementById("InterceptDiagram").getAttribute("data-OIPn");

// Compression point
var CPi = document.getElementById("InterceptDiagram").getAttribute("data-CPi");
var CPo = document.getElementById("InterceptDiagram").getAttribute("data-CPo");

// Minimum S/I
var Pin_Upper_Limit = document.getElementById("InterceptDiagram").getAttribute("data-Pin_Upper_Limit");
var Pout_Upper_Limit = document.getElementById("InterceptDiagram").getAttribute("data-Pout_Upper_Limit");
var SI = document.getElementById("InterceptDiagram").getAttribute("data-SI");

//////////////////////////////////////////////////////////////////////////////////////////
// Check if there's input data available, otherwise generate default data
if (Pin.length <= 1) {
  Pin = [-20.0,-17.0,-14.0,-11.0,-8.0,-6.0,-3.0,0.0,3.0,6.0,9.0,12.0,15.0,18.0,21.0,23.0,26.0,29.0,32.0,35.0];
  Pout = [-4.0,-1.0,2.0,5.0,8.0,10.0,13.0,16.0,19.0,22.0,25.0,28.0,31.0,34.0,37.0,39.0,42.0,45.0,48.0,51.0];
  IMn = [-92.0,-83.0,-74.0,-65.0,-56.0,-50.0,-41.0,-32.0,-23.0,-14.0,-5.0,4.0,13.0,22.0,31.0,37.0,46.0,55.0,64.0,73.0];
  Noise_Floor = [-69.14,-69.14,-69.14,-69.14,-69.14,-69.14,-69.14,-69.14,-69.14,-69.14,-69.14,-69.14,-69.14,-69.14,-69.14,-69.14,-69.14,-69.14,-69.14,-69.14];
  IIP3 = 24.0;
  OIP3 = 40;
  CPi = 4;
  CPo = 22;
  Pin_Upper_Limit = 6.5;
  Pout_Upper_Limit = 22.5;
  SI = 35;
}  
//////////////////////////////////////////////////////////////////////////////////////////


var xmin = Pin[0]
var xmax = Pin[Pin.length - 1]

var ymin = Noise_Floor[0] 
ymin = Math.floor(ymin / 5) * 5 - 10// Round to 5dB

var ymax = Math.max(Pin[Pin.length - 1], IMn[IMn.length - 1])
ymax = Math.ceil(ymax / 5) * 5 // Round to 5dB


// Put data in pairs (Pin, Pout) for the chart representation
Pout_data = [];
IMn_data = [];
NF_data = [];
IIPn = [];
OIPn = [];
ICP = [];
OCP = [];
SImin = [];

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
    IIPn.push({
      x: IIP3,
      y : ymin + t*(OIP3-ymin)/(Pin.length-1)
    })
    
    // Intercept point (output)
    OIPn.push({
      x: 1.*xmin + t*(IIP3-xmin)/(Pin.length-1),
      y : OIP3
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
                label: "IIP3",
                data: IIPn,
                backgroundColor: 'transparent',
                borderColor: '#000000', // Black
                borderWidth: 2,
                pointBackgroundColor: '#000000',
                borderDash: [5]
               },

              // OIPn
              {
                label: "IP3",
                data: OIPn,
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
                                  return !item.text.includes('IIP3') & !item.text.includes('CPo');
                              }
                            }
                          }
              }
    }
  new Chart(chLine, options);
}