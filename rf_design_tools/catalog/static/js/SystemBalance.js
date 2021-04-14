$(document).ready(function(){
    $('#submit_button').click(function(){
        var count = $(":input[id^='add_stop_sale_to_date']").length;
        for(var x=1;x<=count;x++){
            var from_date = $('#add_stop_sale_from_date'+x).val();
            var to_date = $('#add_stop_sale_to_date'+x).val();
            if(from_date=="" || from_date==null){
                alert("Select From Date");
                $('#add_stop_sale_from_date'+x).focus();
                return false;
            }if(to_date=="" || to_date==null){
                alert("Select To Date");
                $('#add_stop_sale_to_date'+x).focus();
                return false;
            }
        }
    alert("Form Will be Submitted");
        return true;
     });
        var maxField = 10;
        var x = 0;
        const gainArray = [], stagesArray = [], nfArray = [], oip3Array = []
        const system_gain = []

        if(x==0){
            $('#remove_button').hide();
        }
        $('#add_button').click(function(){
            if(x>=1){
                $('#remove_button').show();
            }

            // Get data
            x++;
            stagesArray.push(x)
                
            var type = document.getElementById("block_type").value;
            if (type == 'Active'){
                    $("#system_table_"+(x-1)).closest( "tr" ).after('<tr style="text-align: center; vertical-align: middle;" id="system_table_'+x+'"><td>'+x+'</td><td> Active </td></td><td>'+ document.getElementById("gain_input").value + '</td><td>'+ document.getElementById("nf_input").value+ '</td><td>'+ document.getElementById("oip3_input").value+ '</td></tr>');
                    if(x==1) $("#system_table_0").closest( "tr" ).remove();
                    gainArray.push(parseFloat(document.getElementById("gain_input").value))
            } else {
                    $("#system_table_"+(x-1)).closest( "tr" ).after('<tr style="text-align: center; vertical-align: middle;" id="system_table_'+x+'"><td>'+x+'</td><td>Passive </td><td> -'+ document.getElementById("gain_input").value + '</td><td>'+ document.getElementById("gain_input").value+ '</td><td> &#8734; </td></tr>');
                    if(x==1) $("#system_table_0").closest( "tr" ).remove();
                    gainArray.push(-parseFloat(document.getElementById("gain_input").value))
            }
            nfArray.push(parseFloat(document.getElementById("nf_input").value))
            oip3Array.push(parseFloat(document.getElementById("oip3_input").value))

            // Calculate system gain
            var i;
            system_gain.length=0;
            for (i = 0; i < gainArray.length; i++) {
                if (i == 0){
                    system_gain.push(gainArray[0])
                }
                else{
                    system_gain.push(gainArray[i] + system_gain[i-1])
                    }
            }

            source.data.x = stagesArray
            source.data.y = system_gain
            source.change.emit()
        });
        $('#remove_button').click(function(){
            if (x==1) {
              $("#system_table_1").closest( "tr" ).before('<tr style="text-align: center; vertical-align: middle; height: 20px" id="system_table_0"><td></td><td></td></td><td></td><td></td><td></td></tr>');
              $('#system_table_1').remove();
            }else{
              $('#system_table_'+x+'').remove();
            }
            
            x--;
            if(x == 0){
                $('#remove_button').hide();
            }
        });
    
        $('#block_type').click(function(){
            
            var type = document.getElementById("block_type").value;
            if (type == 'Passive'){
                document.getElementById("gain_label").innerHTML = 'Loss (dB)';
                document.getElementById("nf_label").style.display = 'none';
                document.getElementById("nf_input").style.display = 'none';
                document.getElementById("oip3_label").style.display = 'none';
                document.getElementById("oip3_input").style.display = 'none';
            }else{
                document.getElementById("gain_label").innerHTML = 'Gain (dB)';
                document.getElementById("nf_label").style.display = 'block';
                document.getElementById("nf_input").style.display = 'block';
                document.getElementById("oip3_label").style.display = 'block';
                document.getElementById("oip3_input").style.display = 'block';
            }
    
        });
    
    });        


// create a data source to hold data
var source = new Bokeh.ColumnDataSource({
    data: { x: [], y: [] }
});

// make a plot with some tools
var plot = Bokeh.Plotting.figure({
    title: 'System Balance',
    tools: "pan,wheel_zoom,box_zoom,reset,save",
    height: 400,
    width: 600
});

// add a line with data from the source
plot.line({ field: "x" }, { field: "y" }, {
    source: source,
    line_width: 2
});

// show the plot, appending it to the end of the current section
Bokeh.Plotting.show(plot, '#bokeh_plot');