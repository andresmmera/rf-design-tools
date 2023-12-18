# Copyright 2020-2021 Andrés Martínez Mera - andresmartinezmera@gmail.com
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.http import HttpResponse
from django.template import loader



def DocsView(request):
    return render(request, 'documentation_main.html')


