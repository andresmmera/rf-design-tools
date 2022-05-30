from django.shortcuts import render

def ReflectionCoefficientDocs(request):
    return render(request, 'Reflection_Coefficient/docs/reflection_coeff_docs.html')

def ReflectionToolsCatalogView(request):
    return render(request, 'Reflection_Coefficient/tool/reflection_coeff_catalog.html')


def GammaToZView(request):
    return render(request, 'Reflection_Coefficient/tool/gamma_to_Z.html')


def ZToGammaView(request):
    return render(request, 'Reflection_Coefficient/tool/Z_to_gamma.html')


def SWRtoRView(request):
    return render(request, 'Reflection_Coefficient/tool/SWR_to_gamma.html')
