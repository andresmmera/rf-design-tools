# Copyright 2020-2022 Andrés Martínez Mera - andresmartinezmera@gmail.com
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.http import HttpResponse


from django.views.decorators.csrf import csrf_exempt

import numpy as np

# Import modules for file download
import mimetypes
import os
from django.http.response import HttpResponse

schematic_drawing = None # Global variable storing the schematic. By doing this, the schematic file is generated just when the user clicks download
design_global = None

def S_parameter_Viewer_View(request):
    return render(request, 'SparameterViewer/tool/SparViewer.html')
