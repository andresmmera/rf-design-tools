from django.shortcuts import render


def IPn_DiagramDocs(request):
    return render(request, 'InterceptPoints/docs/InterceptPoints_doc.html')

def IPn_DiagramView(request):
    return render(request, 'InterceptPoints/tool/InterceptPoints.html')