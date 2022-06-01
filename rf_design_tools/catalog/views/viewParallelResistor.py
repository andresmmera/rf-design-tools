from django.shortcuts import render

def RparallelDocs(request):
    """View function for home page of site."""

    # Render the HTML template index.html with the data in the context variable
    return render(request, 'Capacitor_Resistor_Calculators/ParallelResistor/docs/Rparallel_doc.html')

def RparallelView(request):
    return render(request, 'Capacitor_Resistor_Calculators/ParallelResistor/tool/Rparallel.html')