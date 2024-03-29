# Copyright 2020-2022 Andrés Martínez Mera - andresmartinezmera@gmail.com
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.http import HttpResponse
from django.template import loader

from catalog.models import Tool
from catalog.forms import MATCHING_NETWORK_STRUCTURES
from catalog.forms import MASK_TYPE

from .SPAR.LadderAnalysis import *


from django.views.decorators.csrf import csrf_exempt # Allow ajax

from .MatchingNetworkDesign.MatchingNetworkDesigner import *

from django.http import JsonResponse

import numpy as np

import matplotlib
matplotlib.use('Agg') # Set the backend here

# Import modules for file download
import mimetypes
import os
from django.http.response import HttpResponse

schematic_drawing = None # Global variable storing the schematic. By doing this, the schematic file is generated just when the user clicks download
design_global = None

def MatchingNetworkDesignDocs(request):
    return render(request, 'MatchingNetworkDesign/docs/MatchingNetworkDesign_doc.html')


@csrf_exempt
def MatchingNetworkDesignToolView(request):
    context = {} 
    if request.method == "POST":
        #Catch the input data
        index = request.POST.get('Structure', None)
        Structure = MATCHING_NETWORK_STRUCTURES[int(index)-1][1]
        print("Structure:", Structure)

        index = request.POST.get('Mask', None)
        Mask = MASK_TYPE[int(index)-1][1]
        print("Mask:", Mask)
                                       
        f0 = request.POST.get('f0', None)
        print("f0: ", f0, " MHz")
                    
        RS = request.POST.get('RS', None)
        print("RS = ", RS)

        XS = request.POST.get('XS', None)
        print("XS = ", XS)
        
        RL = request.POST.get('RL', None)
        print("RL = ", RL)

        XL = request.POST.get('XL', None)
        print("XL = ", XL)

        Q = request.POST.get('Q', None)
        print("Q = ", Q)

        N = request.POST.get('N', None)
        print("N = ", N)

        Ltap = request.POST.get('Ltap', None)
        print("Ltap = ", Ltap)

        PiTee_Mask = request.POST.get('PiTee_Mask', None)
        print("PiTee_Mask = ", PiTee_Mask)

        StubType = request.POST.get('StubType', None)
        print("StubType = ", StubType)

        Weighting = request.POST.get('Weighting', None)
        print("Weighting = ", Weighting)

        gamma_max = request.POST.get('gamma_max', None)
        print("gamma_max = ", gamma_max)
        
        f_start = request.POST.get('f_start', None)
        print(f_start)
        
        f_stop = request.POST.get('f_stop', None)
        print(f_stop)

        f0_span = request.POST.get('f0_span', None)        
        f_span = request.POST.get('f_span', None)
      
        sweep_mode = request.POST.get('sweep_mode', None)
        
        n_points = request.POST.get('n_points', None)
        print(n_points)

        # Matching Network Design
        designer = MatchingNetwork()
        designer.Structure = Structure
        designer.f0 = float(f0)
        designer.RS = float(RS)
        designer.XS = float(XS)
        designer.RL = float(RL)
        designer.XL = float(XL)
        designer.Q = float(Q)
        designer.Ltap = float(Ltap)
        designer.PiTee_NetworkMask = float(PiTee_Mask)
        designer.StubType = float(StubType)
        designer.f_start = float(f_start)
        designer.f_stop = float(f_stop)
        designer.n_points = int(n_points)
        designer.f0_span = float(f0_span)
        designer.f_span = float(f_span)
        designer.sweep_mode = int(sweep_mode)
        designer.Mask = Mask
        designer.Weighting = Weighting
        designer.N = int(N)
        designer.gamma_max = float(gamma_max)
        
        Schematic, Network_Type, comp_val = designer.synthesize()
        svgcode = Schematic.get_imagedata('svg')
        
        # The schematic drawing is stored in a global variable so that the file is generated when the user clicks the download button
        global schematic_drawing
        schematic_drawing = Schematic

        # The design object is stored as a local variable so that the Qucs schematic is generated just when the user clicks the download button
        global design_global
        design_global = designer


        # Calculate S-parameters
        [S11, S21] = NetworkResponse(Network_Type, comp_val)
        freq = Network_Type['freq']
        phase = (180/np.pi)*np.angle(S21)
        gd = -(1e9)*np.diff(np.angle(S21))/(2*np.pi*freq[:-1]); # Group delay [ns]
        
        
        S11 = np.where(S11 == 0, 1e-12, S11) # Prevent display errors in the JS side for having S11 = 0
        S11 = 20*np.log10(np.abs(S11))
        S21 = 20*np.log10(np.abs(S21))
        
        # Response
        title = Structure + " Matching Network"

        response_data = {}

        # Prepare objects for the html 
        response_data['freq'] =(freq*1e-6).tolist()
        response_data['S11'] = S11.tolist()
        response_data['S21'] = S21.tolist()
        response_data['title'] = title
        #response_data['warning'] = warning
        response_data['svg'] = svgcode.decode('utf-8')
        return JsonResponse(response_data)


    return render(request, 'MatchingNetworkDesign/tool/MatchingNetworkDesignTool.html', context)

# Source: https://linuxhint.com/download-the-file-in-django/
@csrf_exempt
def LTspiceMatchingNetworkDownload(request):
    # Create the LTspice schematic from the designer specs
    global design_global
    [LTspiceSchematic, filename] = design_global.getLTspiceSchematic()

    # Save schematic to file
    filepath = os.path.expanduser('~') + '/' + filename
    schematic_name = filepath
    schematic_file = open(schematic_name, "w+")
    n = schematic_file.write(LTspiceSchematic)
    schematic_file.close()

    # Open the file for reading content
    path = open(filepath, 'r')
    # Set the mime type
    mime_type, _ = mimetypes.guess_type(filepath)
    # Set the return value of the HttpResponse
    response = HttpResponse(path, content_type=mime_type)
    # Set the HTTP header for sending to browser
    response['Content-Disposition'] = "attachment; filename=%s" % filename
    # Return the response value
    return response

def NetworkResponse(Network_Type, comp_val):
    I = 1j
    pi = np.pi

    ZS = comp_val['ZS']
    ZL = comp_val['ZL']

    RL = np.real(ZL)
    XL = np.imag(ZL)
    
    freq = Network_Type['freq']

    if (Network_Type['Network'] == 'L-Section'):

        if((comp_val['topology'][0] == 'CP') and (comp_val['topology'][1] == 'LS')):
            C = comp_val['values_network'][0]
            L = comp_val['values_network'][1]
            
            S11 = -(4*pi**2*C*L*ZS*freq**2 + (-2*I*pi*C*ZL*ZS + 2*I*pi*L)*freq + ZL - ZS)/(4*pi**2*C*L*ZS*freq**2 + (-2*I*pi*C*ZL*ZS - 2*I*pi*L)*freq - ZL - ZS)
            S21 = -2*ZL*ZS/((4*pi**2*C*L*ZS*freq**2 + (-2*I*pi*C*ZL*ZS - 2*I*pi*L)*freq - ZL - ZS)*np.sqrt(ZL*ZS))

        elif((comp_val['topology'][0] == 'LP') and (comp_val['topology'][1] == 'CS')):
            L = comp_val['values_network'][0]
            C = comp_val['values_network'][1]

            S11 = (4*(pi**2*C*L*ZL - pi**2*C*L*ZS)*freq**2 - (-2*I*pi*C*ZL*ZS + 2*I*pi*L)*freq + ZS)/(4*(pi**2*C*L*ZL + pi**2*C*L*ZS)*freq**2 + (-2*I*pi*C*ZL*ZS - 2*I*pi*L)*freq - ZS)
            S21 = 8*pi**2*C*L*ZL*ZS*freq**2/((4*(pi**2*C*L*ZL + pi**2*C*L*ZS)*freq**2 + (-2*I*pi*C*ZL*ZS - 2*I*pi*L)*freq - ZS)*np.sqrt(ZL*ZS))

        elif((comp_val['topology'][0] == 'CS') and (comp_val['topology'][1] == 'LP')):
            C = comp_val['values_network'][0]
            L = comp_val['values_network'][1]

            S11 = (4*(pi**2*C*L*ZL - pi**2*C*L*ZS)*freq**2 - (-2*I*pi*C*ZL*ZS + 2*I*pi*L)*freq - ZL)/(4*(pi**2*C*L*ZL + pi**2*C*L*ZS)*freq**2 + (-2*I*pi*C*ZL*ZS - 2*I*pi*L)*freq - ZL)
            S21 = 8*pi**2*C*L*ZL*ZS*freq**2/((4*(pi**2*C*L*ZL + pi**2*C*L*ZS)*freq**2 + (-2*I*pi*C*ZL*ZS - 2*I*pi*L)*freq - ZL)*np.sqrt(ZL*ZS))

        elif((comp_val['topology'][0] == 'LS') and (comp_val['topology'][1] == 'CP')):
            L = comp_val['values_network'][0]
            C = comp_val['values_network'][1]

            S11 = (4*pi**2*C*L*ZL*freq**2 + (2*I*pi*C*ZL*ZS - 2*I*pi*L)*freq - ZL + ZS)/(4*pi**2*C*L*ZL*freq**2 + (-2*I*pi*C*ZL*ZS - 2*I*pi*L)*freq - ZL - ZS)
            S21 = -2*ZL*ZS/((4*pi**2*C*L*ZL*freq**2 + (-2*I*pi*C*ZL*ZS - 2*I*pi*L)*freq - ZL - ZS)*np.sqrt(ZL*ZS))

        elif((comp_val['topology'][0] == 'CS') and (comp_val['topology'][1] == 'CP')):
            CS = comp_val['values_network'][0]
            CP = comp_val['values_network'][1]

            S11 = (4*pi**2*CP*CS*ZL*freq**2 + (2*I*pi*CP*ZL*ZS - 2*I*pi*CS)*freq - ZL + ZS)/(4*pi**2*CP*CS*ZL*freq**2 + (-2*I*pi*CP*ZL*ZS - 2*I*pi*CS)*freq - ZL - ZS)
            S21 = -2*ZL*ZS/((4*pi**2*CP*CS*ZL*freq**2 + (-2*I*pi*CP*ZL*ZS - 2*I*pi*CS)*freq - ZL - ZS)*np.sqrt(ZL*ZS))

        elif((comp_val['topology'][0] == 'CP') and (comp_val['topology'][1] == 'CS')):
            CP = comp_val['values_network'][0]
            CS = comp_val['values_network'][1]

            S11 = (4*pi**2*CP*CS*ZL*freq**2 + (2*I*pi*CS*ZL*ZS - 2*I*pi*CP)*freq - ZL + ZS)/(4*pi**2*CP*CS*ZL*freq**2 + (-2*I*pi*CS*ZL*ZS - 2*I*pi*CP)*freq - ZL - ZS)
            S21 = -2*ZL*ZS/((4*pi**2*CP*CS*ZL*freq**2 + (-2*I*pi*CS*ZL*ZS - 2*I*pi*CP)*freq - ZL - ZS)*np.sqrt(ZL*ZS))

        elif((comp_val['topology'][0] == 'LS') and (comp_val['topology'][1] == 'LP')):
            LS = comp_val['values_network'][0]
            LP = comp_val['values_network'][1]

            S11 = (4*pi**2*LP*LS*ZL*freq**2 + (2*I*pi*LS*ZL*ZS - 2*I*pi*LP)*freq - ZL + ZS)/(4*pi**2*LP*LS*ZL*freq**2 + (-2*I*pi*LS*ZL*ZS - 2*I*pi*LP)*freq - ZL - ZS)
            S21 = -2*ZL*ZS/((4*pi**2*LP*LS*ZL*freq**2 + (-2*I*pi*LS*ZL*ZS - 2*I*pi*LP)*freq - ZL - ZS)*np.sqrt(ZL*ZS))
        
        elif((comp_val['topology'][0] == 'LP') and (comp_val['topology'][1] == 'LS')):
            LP = comp_val['values_network'][0]
            LS = comp_val['values_network'][1]

            S11 = -(4*pi**2*LP*LS*ZS*freq**2 + (-2*I*pi*LS*ZL*ZS + 2*I*pi*LP)*freq + ZL - ZS)/(4*pi**2*LP*LS*ZS*freq**2 + (-2*I*pi*LS*ZL*ZS - 2*I*pi*LP)*freq - ZL - ZS)
            S21 = -2*ZL*ZS/((4*pi**2*LP*LS*ZS*freq**2 + (-2*I*pi*LS*ZL*ZS - 2*I*pi*LP)*freq - ZL - ZS)*np.sqrt(ZL*ZS))

    elif (Network_Type['Network'] == 'Pi'):
        S = get_SPAR([ZS], [ZL], comp_val['topology'], comp_val['values'], freq)
        S11 = S[:, 0,0]
        S21 = S[:, 1,0]

    elif (Network_Type['Network'] == 'SingleStub1'): # Short Circuit Stub
        Z0 = comp_val['TL_Z0']
        E1 = (np.pi/180)*comp_val['SC_ang']
        E2 = (np.pi/180)*comp_val['TL_ang']
        f0 = comp_val['f0']

        S11 = -((-1.0*I*ZL*np.cos(E1*freq/f0) + (Z0 - ZL)*np.sin(E1*freq/f0))*np.cos(E2*freq/f0) + (1.0*Z0*np.cos(E1*freq/f0) + (-I*Z0 + I*ZL)*np.sin(E1*freq/f0))*np.sin(E2*freq/f0))/((-1.0*I*ZL*np.cos(E1*freq/f0) + (Z0 + ZL)*np.sin(E1*freq/f0))*np.cos(E2*freq/f0) + (1.0*Z0*np.cos(E1*freq/f0) + (I*Z0 + I*ZL)*np.sin(E1*freq/f0))*np.sin(E2*freq/f0))
        S21 = 2*Z0*ZL*np.sin(E1*freq/f0)/(np.sqrt(Z0*ZL)*((-1.0*I*ZL*np.cos(E1*freq/f0) + (Z0 + ZL)*np.sin(E1*freq/f0))*np.cos(E2*freq/f0) + (1.0*Z0*np.cos(E1*freq/f0) + (I*Z0 + I*ZL)*np.sin(E1*freq/f0))*np.sin(E2*freq/f0)))

    elif (Network_Type['Network'] == 'SingleStub2'): # Open Circuit Stub
        Z0 = comp_val['TL_Z0']
        E1 = (np.pi/180)*comp_val['OC_ang']
        E2 = (np.pi/180)*comp_val['TL_ang']
        f0 = comp_val['f0']
        
        S11 = -(((Z0 - ZL)*np.cos(E1*freq/f0) + I*ZL*np.sin(E1*freq/f0))*np.cos(E2*freq/f0) - ((I*Z0 - I*ZL)*np.cos(E1*freq/f0) + Z0*np.sin(E1*freq/f0))*np.sin(E2*freq/f0))/(((Z0 + ZL)*np.cos(E1*freq/f0) + I*ZL*np.sin(E1*freq/f0))*np.cos(E2*freq/f0) - ((-I*Z0 - I*ZL)*np.cos(E1*freq/f0) + Z0*np.sin(E1*freq/f0))*np.sin(E2*freq/f0))
        S21 = 2*Z0*ZL*np.cos(E1*freq/f0)/(np.sqrt(Z0*ZL)*(((Z0 + ZL)*np.cos(E1*freq/f0) + I*ZL*np.sin(E1*freq/f0))*np.cos(E2*freq/f0) - ((-I*Z0 - I*ZL)*np.cos(E1*freq/f0) + Z0*np.sin(E1*freq/f0))*np.sin(E2*freq/f0)))

    elif (Network_Type['Network'] == 'DoubleStub1'): # Short Circuit Stub
        Z0 = comp_val['TL_Z0']
        E1 = (np.pi/180)*comp_val['SC1_ang']
        E2 = (3*np.pi/4)
        E3 = (np.pi/180)*comp_val['SC2_ang']
        f0 = comp_val['f0']

        S11 = -((-1.0*I*ZL*np.cos(E1*freq/f0)*np.sin(2.356194490192345*freq/f0) + (-1.0*I*ZL*np.cos(2.356194490192345*freq/f0) - 1.0*ZL*np.sin(2.356194490192345*freq/f0))*np.sin(E1*freq/f0))*np.cos(E3*freq/f0) + ((-1.0*I*ZL*np.cos(2.356194490192345*freq/f0) + 1.0*Z0*np.sin(2.356194490192345*freq/f0))*np.cos(E1*freq/f0) + ((Z0 - ZL)*np.cos(2.356194490192345*freq/f0) + (-I*Z0 + I*ZL)*np.sin(2.356194490192345*freq/f0))*np.sin(E1*freq/f0))*np.sin(E3*freq/f0))/((-1.0*I*ZL*np.cos(E1*freq/f0)*np.sin(2.356194490192345*freq/f0) + (-1.0*I*ZL*np.cos(2.356194490192345*freq/f0) + 1.0*ZL*np.sin(2.356194490192345*freq/f0))*np.sin(E1*freq/f0))*np.cos(E3*freq/f0) + ((-1.0*I*ZL*np.cos(2.356194490192345*freq/f0) + 1.0*Z0*np.sin(2.356194490192345*freq/f0))*np.cos(E1*freq/f0) + ((Z0 + ZL)*np.cos(2.356194490192345*freq/f0) + (I*Z0 + I*ZL)*np.sin(2.356194490192345*freq/f0))*np.sin(E1*freq/f0))*np.sin(E3*freq/f0))
        S21 = 2*Z0*ZL*np.sin(E1*freq/f0)*np.sin(E3*freq/f0)/(np.sqrt(Z0*ZL)*((-1.0*I*ZL*np.cos(E1*freq/f0)*np.sin(2.356194490192345*freq/f0) + (-1.0*I*ZL*np.cos(2.356194490192345*freq/f0) + 1.0*ZL*np.sin(2.356194490192345*freq/f0))*np.sin(E1*freq/f0))*np.cos(E3*freq/f0) + ((-1.0*I*ZL*np.cos(2.356194490192345*freq/f0) + 1.0*Z0*np.sin(2.356194490192345*freq/f0))*np.cos(E1*freq/f0) + ((Z0 + ZL)*np.cos(2.356194490192345*freq/f0) + (I*Z0 + I*ZL)*np.sin(2.356194490192345*freq/f0))*np.sin(E1*freq/f0))*np.sin(E3*freq/f0)))

    elif (Network_Type['Network'] == 'DoubleStub2'): # Open Circuit Stub
        Z0 = comp_val['TL_Z0']
        E1 = (np.pi/180)*comp_val['OC1_ang']
        E2 = (np.pi/4) # lambda/8
        E3 = (np.pi/180)*comp_val['OC2_ang']
        f0 = comp_val['f0']

        S11 = -((((Z0 - ZL)*np.cos(0.7853981633974483*freq/f0) - (I*Z0 - I*ZL)*np.sin(0.7853981633974483*freq/f0))*np.cos(E1*freq/f0) - (-I*ZL*np.cos(0.7853981633974483*freq/f0) + Z0*np.sin(0.7853981633974483*freq/f0))*np.sin(E1*freq/f0))*np.cos(E3*freq/f0) - (I*ZL*np.sin(E1*freq/f0)*np.sin(0.7853981633974483*freq/f0) + (-I*ZL*np.cos(0.7853981633974483*freq/f0) - ZL*np.sin(0.7853981633974483*freq/f0))*np.cos(E1*freq/f0))*np.sin(E3*freq/f0))/((((Z0 + ZL)*np.cos(0.7853981633974483*freq/f0) - (-I*Z0 - I*ZL)*np.sin(0.7853981633974483*freq/f0))*np.cos(E1*freq/f0) - (-I*ZL*np.cos(0.7853981633974483*freq/f0) + Z0*np.sin(0.7853981633974483*freq/f0))*np.sin(E1*freq/f0))*np.cos(E3*freq/f0) - (I*ZL*np.sin(E1*freq/f0)*np.sin(0.7853981633974483*freq/f0) + (-I*ZL*np.cos(0.7853981633974483*freq/f0) + ZL*np.sin(0.7853981633974483*freq/f0))*np.cos(E1*freq/f0))*np.sin(E3*freq/f0))
        S21 = 2*Z0*ZL*np.cos(E1*freq/f0)*np.cos(E3*freq/f0)/(np.sqrt(Z0*ZL)*((((Z0 + ZL)*np.cos(0.7853981633974483*freq/f0) - (-I*Z0 - I*ZL)*np.sin(0.7853981633974483*freq/f0))*np.cos(E1*freq/f0) - (-I*ZL*np.cos(0.7853981633974483*freq/f0) + Z0*np.sin(0.7853981633974483*freq/f0))*np.sin(E1*freq/f0))*np.cos(E3*freq/f0) - (I*ZL*np.sin(E1*freq/f0)*np.sin(0.7853981633974483*freq/f0) + (-I*ZL*np.cos(0.7853981633974483*freq/f0) + ZL*np.sin(0.7853981633974483*freq/f0))*np.cos(E1*freq/f0))*np.sin(E3*freq/f0)))

    elif (Network_Type['Network'] == 'L4'):
        Z0 = comp_val['ZS']
        Zm = comp_val['Zm']
        f0 = comp_val['f0']

        E1 = (np.pi/2) # lambda/4

        S11 = -((Z0 - ZL)*Zm*np.cos(E1*freq/f0) - (-I*Z0*ZL + I*Zm**2)*np.sin(E1*freq/f0))/((Z0 + ZL)*Zm*np.cos(E1*freq/f0) + (I*Z0*ZL + I*Zm**2)*np.sin(E1*freq/f0))
        S21 = 2*Z0*ZL*Zm/(((Z0 + ZL)*Zm*np.cos(E1*freq/f0) + (I*Z0*ZL + I*Zm**2)*np.sin(E1*freq/f0))*np.sqrt(Z0*ZL))
    
    elif (Network_Type['Network'] == 'L4L8'):
        Z0 = comp_val['ZS']
        Zm = comp_val['Zm']
        Zm_ = comp_val['Zm_']
        f0 = comp_val['f0']

        E1 = (np.pi/2) # lambda/4
        E2 = (np.pi/4) # lambda/8

        S11 = -(((Z0 - ZL)*Zm*Zm_*np.cos(E1*freq/f0) - (-I*Z0*ZL + I*Zm**2)*Zm_*np.sin(E1*freq/f0))*np.cos(E2*freq/f0) - ((-I*Z0*ZL*Zm + I*Zm*Zm_**2)*np.cos(E1*freq/f0) - (ZL*Zm**2 - Z0*Zm_**2)*np.sin(E1*freq/f0))*np.sin(E2*freq/f0))/(((Z0 + ZL)*Zm*Zm_*np.cos(E1*freq/f0) - (-I*Z0*ZL - I*Zm**2)*Zm_*np.sin(E1*freq/f0))*np.cos(E2*freq/f0) - ((-I*Z0*ZL*Zm - I*Zm*Zm_**2)*np.cos(E1*freq/f0) + (ZL*Zm**2 + Z0*Zm_**2)*np.sin(E1*freq/f0))*np.sin(E2*freq/f0))
        S21 = 2*Z0*ZL*Zm*Zm_/(np.sqrt(Z0*ZL)*(((Z0 + ZL)*Zm*Zm_*np.cos(E1*freq/f0) - (-I*Z0*ZL - I*Zm**2)*Zm_*np.sin(E1*freq/f0))*np.cos(E2*freq/f0) - ((-I*Z0*ZL*Zm - I*Zm*Zm_**2)*np.cos(E1*freq/f0) + (ZL*Zm**2 + Z0*Zm_**2)*np.sin(E1*freq/f0))*np.sin(E2*freq/f0)))

    elif (Network_Type['Network'] == 'SST'):
        Z0 = comp_val['ZS']
        Zm = comp_val['Zm']
        E1 = (np.pi/180)*comp_val['theta']
        f0 = comp_val['f0']
        
        S11 = ((RL + 1.0*I*XL - Z0)*Zm*np.cos(E1*freq/f0) + ((-I*RL + 1.0*XL)*Z0 + I*Zm**2)*np.sin(E1*freq/f0))/((RL + 1.0*I*XL + Z0)*Zm*np.cos(E1*freq/f0) + ((I*RL - 1.0*XL)*Z0 + I*Zm**2)*np.sin(E1*freq/f0))
        S21 = 2*RL*Z0*Zm/(((RL + 1.0*I*XL + Z0)*Zm*np.cos(E1*freq/f0) + ((I*RL - 1.0*XL)*Z0 + I*Zm**2)*np.sin(E1*freq/f0))*np.sqrt(RL*Z0))

    elif (Network_Type['Network'] == 'TL_Transformer'):
        N = comp_val['N']
        f0 = comp_val['f0']
        x = []
        code = []

        for i in range(1, N+1):
            x.append([comp_val['Z' + str(i)], 90/(2*np.pi*f0)])
            code.append('CASTL')

        print (code)
        print (x)
        S = get_SPAR([ZS], [ZL], code, x, freq)
        S11 = S[:, 0,0]
        S21 = S[:, 1,0]

    elif (Network_Type['Network'] == 'Tapped-C'):
        L = comp_val['L']
        C1 = comp_val['C1']
        C2 = comp_val['C2']
        RS = ZS

        if (RS < RL):
            S11 = -((-8*I*pi**3*C1*C2*L*RL*RS + 8.0*pi**3*C1*C2*L*RS*XL)*freq**3 + (4*pi**2*C1*L*RL + 4.0*I*pi**2*C1*L*XL - 4*(pi**2*C1 + pi**2*C2)*L*RS)*freq**2 + (2*(I*pi*C1 + I*pi*C2)*RL*RS - (2.0*pi*C1 + 2.0*pi*C2)*RS*XL - 2*I*pi*L)*freq - RL - 1.0*I*XL)/((-8*I*pi**3*C1*C2*L*RL*RS + 8.0*pi**3*C1*C2*L*RS*XL)*freq**3 - (4*pi**2*C1*L*RL + 4.0*I*pi**2*C1*L*XL + 4*(pi**2*C1 + pi**2*C2)*L*RS)*freq**2 + (2*(I*pi*C1 + I*pi*C2)*RL*RS - (2.0*pi*C1 + 2.0*pi*C2)*RS*XL + 2*I*pi*L)*freq + RL + 1.0*I*XL)
            S21 = -8*pi**2*C1*L*RL*RS*freq**2/(((-8*I*pi**3*C1*C2*L*RL*RS + 8.0*pi**3*C1*C2*L*RS*XL)*freq**3 - (4*pi**2*C1*L*RL + 4.0*I*pi**2*C1*L*XL + 4*(pi**2*C1 + pi**2*C2)*L*RS)*freq**2 + (2*(I*pi*C1 + I*pi*C2)*RL*RS - (2.0*pi*C1 + 2.0*pi*C2)*RS*XL + 2*I*pi*L)*freq + RL + 1.0*I*XL)*np.sqrt(RL*RS))
        else:
            S11 = -((-8*I*pi**3*C1*C2*L*RL*RS + 8.0*pi**3*C1*C2*L*RS*XL)*freq**3 - (4*pi**2*C1*L*RS - 4*(pi**2*C1 + pi**2*C2)*L*RL + (-4.0*I*pi**2*C1 - 4.0*I*pi**2*C2)*L*XL)*freq**2 + (2*(I*pi*C1 + I*pi*C2)*RL*RS - (2.0*pi*C1 + 2.0*pi*C2)*RS*XL - 2*I*pi*L)*freq + RS)/((-8*I*pi**3*C1*C2*L*RL*RS + 8.0*pi**3*C1*C2*L*RS*XL)*freq**3 - (4*pi**2*C1*L*RS + 4*(pi**2*C1 + pi**2*C2)*L*RL + (4.0*I*pi**2*C1 + 4.0*I*pi**2*C2)*L*XL)*freq**2 + (2*(I*pi*C1 + I*pi*C2)*RL*RS - (2.0*pi*C1 + 2.0*pi*C2)*RS*XL + 2*I*pi*L)*freq + RS)
            S21 = -8*pi**2*C1*L*RL*RS*freq**2/(((-8*I*pi**3*C1*C2*L*RL*RS + 8.0*pi**3*C1*C2*L*RS*XL)*freq**3 - (4*pi**2*C1*L*RS + 4*(pi**2*C1 + pi**2*C2)*L*RL + (4.0*I*pi**2*C1 + 4.0*I*pi**2*C2)*L*XL)*freq**2 + (2*(I*pi*C1 + I*pi*C2)*RL*RS - (2.0*pi*C1 + 2.0*pi*C2)*RS*XL + 2*I*pi*L)*freq + RS)*np.sqrt(RL*RS))
            
    elif (Network_Type['Network'] == 'Tapped-L'):
        C = comp_val['C']
        L1 = comp_val['L1']
        L2 = comp_val['L2']
        RS = ZS

        if (RL < RS):
            S11 = -(8*pi**3*C*L1*L2*RS*freq**3 + (4*I*pi**2*L1*L2 + 4*(-I*pi**2*C*L1 - I*pi**2*C*L2)*RL*RS + (4.0*pi**2*C*L1 + 4.0*pi**2*C*L2)*RS*XL)*freq**2 + I*RL*RS - 1.0*RS*XL - (2*pi*L2*RS - 2*(pi*L1 + pi*L2)*RL + (-2.0*I*pi*L1 - 2.0*I*pi*L2)*XL)*freq)/(8*pi**3*C*L1*L2*RS*freq**3 + (-4*I*pi**2*L1*L2 + 4*(-I*pi**2*C*L1 - I*pi**2*C*L2)*RL*RS + (4.0*pi**2*C*L1 + 4.0*pi**2*C*L2)*RS*XL)*freq**2 + I*RL*RS - 1.0*RS*XL - (2*pi*L2*RS + 2*(pi*L1 + pi*L2)*RL + (2.0*I*pi*L1 + 2.0*I*pi*L2)*XL)*freq)
            S21 = -4*pi*L2*RL*RS*freq/((8*pi**3*C*L1*L2*RS*freq**3 + (-4*I*pi**2*L1*L2 + 4*(-I*pi**2*C*L1 - I*pi**2*C*L2)*RL*RS + (4.0*pi**2*C*L1 + 4.0*pi**2*C*L2)*RS*XL)*freq**2 + I*RL*RS - 1.0*RS*XL - (2*pi*L2*RS + 2*(pi*L1 + pi*L2)*RL + (2.0*I*pi*L1 + 2.0*I*pi*L2)*XL)*freq)*np.sqrt(RL*RS))
        else:
            S11 = ((8*pi**3*C*L1*L2*RL + 8.0*I*pi**3*C*L1*L2*XL)*freq**3 + (-4*I*pi**2*L1*L2 + 4*(I*pi**2*C*L1 + I*pi**2*C*L2)*RL*RS + (-4.0*pi**2*C*L1 - 4.0*pi**2*C*L2)*RS*XL)*freq**2 - I*RL*RS + 1.0*RS*XL - (2*pi*L2*RL + 2.0*I*pi*L2*XL - 2*(pi*L1 + pi*L2)*RS)*freq)/((8*pi**3*C*L1*L2*RL + 8.0*I*pi**3*C*L1*L2*XL)*freq**3 + (-4*I*pi**2*L1*L2 + 4*(-I*pi**2*C*L1 - I*pi**2*C*L2)*RL*RS + (4.0*pi**2*C*L1 + 4.0*pi**2*C*L2)*RS*XL)*freq**2 + I*RL*RS - 1.0*RS*XL - (2*pi*L2*RL + 2.0*I*pi*L2*XL + 2*(pi*L1 + pi*L2)*RS)*freq)
            S21 = -4*pi*L2*RL*RS*freq/(((8*pi**3*C*L1*L2*RL + 8.0*I*pi**3*C*L1*L2*XL)*freq**3 + (-4*I*pi**2*L1*L2 + 4*(-I*pi**2*C*L1 - I*pi**2*C*L2)*RL*RS + (4.0*pi**2*C*L1 + 4.0*pi**2*C*L2)*RS*XL)*freq**2 + I*RL*RS - 1.0*RS*XL - (2*pi*L2*RL + 2.0*I*pi*L2*XL + 2*(pi*L1 + pi*L2)*RS)*freq)*np.sqrt(RL*RS))
    
    elif (Network_Type['Network'] == 'DoubleTappedResonator'):
        LP = comp_val['LP']
        LS = comp_val['LS']
        CS = comp_val['CS']
        CP = comp_val['CP']
        RS = ZS

        S11 = ((16*pi**4*CP*CS*LP*LS*RL + 16.0*I*pi**4*CP*CS*LP*LS*XL)*freq**4 + (-8*I*pi**3*CS*LP*LS + 8*(I*pi**3*CP*CS*LP + I*pi**3*CP*CS*LS)*RL*RS + (-8.0*pi**3*CP*CS*LP - 8.0*pi**3*CP*CS*LS)*RS*XL)*freq**3 - (4*(pi**2*CP + pi**2*CS)*LP*RL + (4.0*I*pi**2*CP + 4.0*I*pi**2*CS)*LP*XL - 4*(pi**2*CS*LP + pi**2*CS*LS)*RS)*freq**2 + (2*(-I*pi*CP - I*pi*CS)*RL*RS - (-2.0*pi*CP - 2.0*pi*CS)*RS*XL + 2*I*pi*LP)*freq - RS)/((16*pi**4*CP*CS*LP*LS*RL + 16.0*I*pi**4*CP*CS*LP*LS*XL)*freq**4 + (-8*I*pi**3*CS*LP*LS + 8*(-I*pi**3*CP*CS*LP - I*pi**3*CP*CS*LS)*RL*RS + (8.0*pi**3*CP*CS*LP + 8.0*pi**3*CP*CS*LS)*RS*XL)*freq**3 - (4*(pi**2*CP + pi**2*CS)*LP*RL + (4.0*I*pi**2*CP + 4.0*I*pi**2*CS)*LP*XL + 4*(pi**2*CS*LP + pi**2*CS*LS)*RS)*freq**2 + (2*(I*pi*CP + I*pi*CS)*RL*RS - (2.0*pi*CP + 2.0*pi*CS)*RS*XL + 2*I*pi*LP)*freq + RS)
        S21 = -8*pi**2*CS*LP*RL*RS*freq**2/(((16*pi**4*CP*CS*LP*LS*RL + 16.0*I*pi**4*CP*CS*LP*LS*XL)*freq**4 + (-8*I*pi**3*CS*LP*LS + 8*(-I*pi**3*CP*CS*LP - I*pi**3*CP*CS*LS)*RL*RS + (8.0*pi**3*CP*CS*LP + 8.0*pi**3*CP*CS*LS)*RS*XL)*freq**3 - (4*(pi**2*CP + pi**2*CS)*LP*RL + (4.0*I*pi**2*CP + 4.0*I*pi**2*CS)*LP*XL + 4*(pi**2*CS*LP + pi**2*CS*LS)*RS)*freq**2 + (2*(I*pi*CP + I*pi*CS)*RL*RS - (2.0*pi*CP + 2.0*pi*CS)*RS*XL + 2*I*pi*LP)*freq + RS)*np.sqrt(RL*RS))    
    return np.ones(len(freq))*S11, np.ones(len(freq))*S21