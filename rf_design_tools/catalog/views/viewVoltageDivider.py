
from django.shortcuts import render


def VoltageDividerDocs(request):
    """View function for home page of site."""

    # Render the HTML template index.html with the data in the context variable
    return render(request, 'VoltageDivider/docs/VoltageDivider_doc.html')

def VoltageDividerView(request):
    return render(request, 'VoltageDivider/tool/VoltageDivider.html')