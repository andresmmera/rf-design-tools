from django.shortcuts import render

def CseriesDocs(request):
    """View function for home page of site."""

    # Render the HTML template index.html with the data in the context variable
    return render(request, 'Capacitor_Resistor_Calculators/SeriesCapacitor/docs/Cseries_doc.html')

def CseriesView(request):
    return render(request, 'Capacitor_Resistor_Calculators/SeriesCapacitor/tool/Cseries.html')