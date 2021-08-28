# Copyright 2020-2021 Andrés Martínez Mera - andresmartinezmera@gmail.com
import numpy as np

# Schematic drawing
import schemdraw as schem
import schemdraw.elements as elm

# Get units with scale, etc.
from ..utilities import *

# standard imports
import skrf as rf
from skrf import network2

# Import for the generation of the Qucs schematic
from datetime import date


def getCanonicalFilterNetwork(params):
    # Unpack the dictionary
    gi = params['gi']
    N =  params['N']
    ZS = params['ZS']
    ZL = params['ZL']
    fc = params['fc']
    f1 = params['f1']
    f2 = params['f2']
    FirstElement = params['FirstElement']
    Mask = params['Mask']
    f_start = params['f_start']
    f_stop = params['f_stop']
    n_points = params['n_points']
    Response = params['Response']
    Ripple = params['Ripple']

    if (Mask =='Bandpass' or Mask =='Bandstop'):
        w1 = 2*np.pi*f1*1e6 # rad/s
        w2 = 2*np.pi*f2*1e6 # rad/s
        w0 = np.sqrt(w1*w2)
        Delta = w2-w1
    else:
        w0 = 2*np.pi*fc*1e6 # rad/s

    rf.stylely()
    freq = rf.Frequency(start=f_start, stop=f_stop, npoints=n_points, unit='MHz')
    line = rf.media.DefinedGammaZ0(frequency=freq)
    
    Port1 = rf.Circuit.Port(frequency=freq, name='port1', z0=ZS)
    Port2 = rf.Circuit.Port(frequency=freq, name='port2', z0=ZS*gi[-1])
    
    count_C = 0
    count_L = 0
    count_gnd = 0
    
    C = []
    L = []
    ground = []
    
    # Place components
    for i in range(0, N):
        if (((i % 2 == 0) and (FirstElement==1)) or ((i % 2 != 0) and (FirstElement!=1))):           
            if (Mask == 'Lowpass'):
                # Shunt capacitance
                count_C += 1
                C.append(line.capacitor(gi[i+1]/(ZS*w0), name='C' + str(count_C)))
                ground.append(rf.Circuit.Ground(frequency=freq, name='ground' + str(count_C), z0=ZS))
            elif (Mask == 'Highpass'):
                # Shunt inductance
                count_L += 1
                L.append(line.inductor(ZS/(w0*gi[i+1]), name='L' + str(count_L)))
                ground.append(rf.Circuit.Ground(frequency=freq, name='ground' + str(count_L), z0=ZS))
            elif (Mask == 'Bandpass'):
                # Shunt parallel resonator
                count_C += 1
                count_L += 1
                C.append(line.capacitor(gi[i+1]/(ZS*Delta), name='C' + str(count_C)))
                L.append(line.inductor(ZS*Delta/(gi[i+1]*w0*w0), name='L' + str(count_L)))
                count_gnd += 1
                ground.append(rf.Circuit.Ground(frequency=freq, name='ground' + str(count_gnd), z0=ZS))
                count_gnd += 1
                ground.append(rf.Circuit.Ground(frequency=freq, name='ground' + str(count_gnd), z0=ZS))
            elif (Mask == 'Bandstop'):
                # Shunt series resonator
                count_C += 1
                count_L += 1
                C.append(line.capacitor(gi[i+1]*Delta/(ZS*w0*w0), name='C' + str(count_C)))
                L.append(line.inductor(ZS/(gi[i+1]*Delta), name='L' + str(count_L)))
                count_gnd += 1
                ground.append(rf.Circuit.Ground(frequency=freq, name='ground' + str(count_gnd), z0=ZS))
            
        else:
            if (Mask == 'Lowpass'):
                # Series inductor
                count_L += 1
                L.append(line.inductor(ZS*gi[i+1]/w0, name='L' + str(count_L)))
            elif (Mask == 'Highpass'):
                # Series capacitor
                count_C += 1
                C.append(line.capacitor(1/(gi[i+1]*w0*ZS), name='C' + str(count_C)))
            elif (Mask == 'Bandpass'):
                # Shunt parallel resonator
                count_C += 1
                count_L += 1
                L.append(line.inductor(ZS*gi[i+1]/(Delta), name='L' + str(count_L)))
                C.append(line.capacitor(Delta/(ZS*w0*w0*gi[i+1]), name='C' + str(count_C)))
            elif (Mask == 'Bandstop'):
                # Series parallel resonator
                count_C += 1
                count_L += 1
                L.append(line.inductor(gi[i+1]*ZS*Delta/(w0*w0), name='L' + str(count_L)))
                C.append(line.capacitor(1/(ZS*Delta*gi[i+1]), name='C' + str(count_C)))
    
    # Make connections
    connections = []
    if (Mask == 'Lowpass'):
        if (FirstElement == 1): # First shunt
            connections.append([(Port1, 0), (C[0], 0), (L[0],0)])
            connections.append([(C[0], 1), (ground[0], 0)]) 
            for i in range(1, int(np.floor(N/2))):
                connections.append([(L[i-1], 1), (C[i], 0), (L[i], 0)])
                connections.append([(C[i], 1), (ground[i], 0)])

            if (N % 2 == 0): # Even order
                connections.append([(Port2, 0), (L[-1],1)])
            else: # Odd order
                connections.append([(Port2, 0), (C[-1], 0), (L[-1],1)])
                connections.append([(C[-1], 1), (ground[-1], 0)])

        else: # First series
            connections.append([(Port1, 0), (L[0],0)])
            for i in range(0, int(np.floor(N/2))):
                if (i == np.floor(N/2)-1):
                    if (N % 2 != 0): # Even
                        connections.append([(L[i], 1), (C[i], 0), (L[i+1], 0)])
                        connections.append([(C[i], 1), (ground[i], 0)])
                else:
                    connections.append([(L[i], 1), (C[i], 0), (L[i+1], 0)])
                    connections.append([(C[i], 1), (ground[i], 0)])


            if (N % 2 == 0): # Even order
                connections.append([(Port2, 0), (L[-1], 1), (C[-1], 0)])
                connections.append([(C[-1], 1), (ground[-1], 0)])
            else: # Odd order
                connections.append([(Port2, 0), (L[-1], 1)])
    elif (Mask == 'Highpass'):
        if (FirstElement == 1):
            connections.append([(Port1, 0), (L[0], 0), (C[0],0)])
            connections.append([(L[0], 1), (ground[0], 0)]) 
            for i in range(1, int(np.floor(N/2))):
                connections.append([(C[i-1], 1), (L[i], 0), (C[i], 0)])
                connections.append([(L[i], 1), (ground[i], 0)])

            if (N % 2 == 0): # Even order
                connections.append([(Port2, 0), (C[-1],1)])
            else: # Odd order
                connections.append([(Port2, 0), (L[-1], 0), (C[-1],1)])
                connections.append([(L[-1], 1), (ground[-1], 0)])

        else: # First series
            connections.append([(Port1, 0), (C[0],0)])
            for i in range(0, int(np.floor(N/2))):
                if (i == np.floor(N/2)-1):
                    if (N % 2 != 0): # Even
                        connections.append([(C[i], 1), (L[i], 0), (C[i+1], 0)])
                        connections.append([(L[i], 1), (ground[i], 0)])
                else:
                    connections.append([(C[i], 1), (L[i], 0), (C[i+1], 0)])
                    connections.append([(L[i], 1), (ground[i], 0)])


            if (N % 2 == 0): # Even order
                connections.append([(Port2, 0), (C[-1], 1), (L[-1], 0)])
                connections.append([(L[-1], 1), (ground[-1], 0)])
            else: # Odd order
                connections.append([(Port2, 0), (C[-1], 1)])
    elif (Mask == 'Bandpass'):
        if (FirstElement == 1):
            connections.append([(Port1, 0), (C[0], 0), (L[0],0), (L[1], 0)])
            connections.append([(L[1], 1), (C[1],0)])
            
            for i in range(2, N-1, 2):
                connections.append([(C[i-1], 1), (C[i], 0), (L[i], 0), (L[i+1], 0)])
                connections.append([(L[i+1], 1), (C[i+1], 0)])
                    
            if (N % 2 == 0): # Even order
                connections.append([(Port2, 0), (C[-1],1)])
            else: # Odd order
                connections.append([(Port2, 0), (C[-2], 1), (C[-1], 0), (L[-1],0)])
                
            for i in range(0, N, 2):
                connections.append([(C[i], 1), (ground[i], 0)])
                connections.append([(L[i], 1), (ground[i+1], 0)])

        else: # First series
            connections.append([(Port1, 0), (L[0],0)])
            connections.append([(L[0],1), (C[0], 0)])
            
            for i in range(1, N-1, 2):
                connections.append([(C[i-1], 1), (C[i], 0), (L[i], 0), (L[i+1], 0)])
                connections.append([(L[i+1], 1), (C[i+1], 0)])
                
            if (N % 2 == 0): # Even order
                connections.append([(Port2, 0), (C[-1],0), (L[-1],0), (C[-2],1)])
            else: # Odd order
                connections.append([(Port2, 0), (C[-1], 1)])
                
            for i in range(1, N, 2):
                connections.append([(C[i], 1), (ground[i-1], 0)])
                connections.append([(L[i], 1), (ground[i], 0)])
                
    elif (Mask == 'Bandstop'):
        if (FirstElement == 1):
            connections.append([(Port1, 0), (L[0],0), (L[1], 0), (C[1], 0)])
            connections.append([(L[0],1), (C[0], 0)])
            
            for i in range(2, N-1, 2):
                connections.append([(C[i-1], 1), (L[i-1], 1), (L[i], 0), (L[i+1], 0), (C[i+1], 0)])
                connections.append([(L[i], 1), (C[i], 0)])
                
            if (N % 2 == 0): # Even order
                connections.append([(Port2, 0), (C[-1],1), (L[-1],1)])
            else: # Odd order
                connections.append([(Port2, 0), (L[-2], 1), (C[-2], 1), (L[-1], 0)])
                connections.append([(L[-1], 1), (C[-1], 0)])
                
            for i in range(0, N, 2):
                connections.append([(C[i], 1), (ground[int((i+1)/2)], 0)])
        else: # Bandstop first series
            connections.append([(Port1, 0), (L[0],0), (C[0], 0)])
            
            for i in range(1, N-1, 2):
                connections.append([(C[i-1], 1), (L[i-1], 1), (L[i], 0), (L[i+1], 0), (C[i+1], 0)])
                connections.append([(L[i], 1), (C[i], 0)])
                
            if (N % 2 == 0): # Even order
                connections.append([(Port2, 0), (L[-2], 1), (C[-2], 1), (L[-1], 0)])
                connections.append([(L[-1], 1), (C[-1], 0)])
            else: # Odd order
                connections.append([(Port2, 0), (C[-1],1), (L[-1],1)])
                
            for i in range(1, N, 2):
                connections.append([(C[i], 1), (ground[int((i+1)/2)-1], 0)])
    return connections


def getCanonicalFilterSchematic(params):
    # Unpack the dictionary
    gi = params['gi']
    N =  params['N']
    ZS = params['ZS']
    fc = params['fc']
    f1 = params['f1']
    f2 = params['f2']
    FirstElement = params['FirstElement']
    Mask = params['Mask']

    if (Mask =='Bandpass' or Mask =='Bandstop'):
        w1 = 2*np.pi*f1*1e6 # rad/s
        w2 = 2*np.pi*f2*1e6 # rad/s
        w0 = np.sqrt(w1*w2)
        Delta = w2-w1
    else:
        w0 = 2*np.pi*fc*1e6 # rad/s

    print(gi)
    ##################################################
    # Draw circuit
    schem.use('svg')
    d = schem.Drawing(inches_per_unit = 0.3)
    _fontsize = 8
    
    # Draw the source port and the first line (if needed)
    d += elm.Line(color='white').length(2).linewidth(0)
    d += elm.Dot().label('ZS = ' + str(ZS) + " \u03A9", fontsize=_fontsize).linewidth(1)
    d += elm.Line().length(2).linewidth(1)
            
    # Draw the filter components
    for i in range(N):
        if (((i % 2 == 0) and (FirstElement==1)) or ((i % 2 != 0) and (FirstElement!=1))):
            d += elm.Dot()
            d.push() # Save the drawing point for later
            
            # Mask-type transformation
            if (Mask == 'Lowpass'):
                d += elm.Capacitor().down().label(getUnitsWithScale(gi[i+1]/(ZS*w0), 'Capacitance'), fontsize=_fontsize).linewidth(1)
                d += elm.Ground().linewidth(1)
            elif (Mask == 'Highpass'):
                d += elm.Inductor2(loops=2).down().label(getUnitsWithScale(ZS/(gi[i+1]*w0), 'Inductance'), fontsize=_fontsize).linewidth(1)
                d += elm.Ground().linewidth(1)
            elif (Mask == 'Bandpass'):
                d.push()
                d += elm.Line().down().length(2).linewidth(1)
                d += elm.Dot()
                d.push()
                d += elm.Line().left().length(1).linewidth(1)
                d += elm.Capacitor().down().label(getUnitsWithScale(gi[i+1]/(ZS*Delta), 'Capacitance'), fontsize=_fontsize).linewidth(1)
                d += elm.Ground().linewidth(1)
                d.pop()
                d += elm.Line().right().length(1).linewidth(1)
                d += elm.Inductor2(loops=2).down().label(getUnitsWithScale(ZS*Delta/(gi[i+1]*w0*w0), 'Inductance'), fontsize=_fontsize).linewidth(1)
                d += elm.Ground().linewidth(1)
                d.pop()
            elif (Mask == 'Bandstop'):
                d += elm.Dot()
                d.push()
                d += elm.Inductor2(loops=2).down().label(getUnitsWithScale(ZS/(gi[i+1]*Delta), 'Inductance'), fontsize=_fontsize).linewidth(1)
                d += elm.Capacitor().down().label(getUnitsWithScale(gi[i+1]*Delta/(ZS*w0*w0), 'Capacitance'), fontsize=_fontsize).linewidth(1)
                d += elm.Ground().linewidth(1)
                d.pop()
                
            d.pop() # Restore the drawing point
        else:
            # Mask-type transformation
            if (Mask == 'Lowpass'):
                d += elm.Inductor2(loops=2).label(getUnitsWithScale(ZS*gi[i+1]/w0, 'Inductance'), fontsize=_fontsize).linewidth(1)
            elif (Mask == 'Highpass'):
                d += elm.Capacitor().label(getUnitsWithScale(1/(gi[i+1]*w0*ZS), 'Capacitance'), fontsize=_fontsize).linewidth(1)
            elif (Mask == 'Bandpass'):
                d += elm.Inductor2(loops=2).label(getUnitsWithScale(ZS*gi[i+1]/(Delta), 'Inductance'), fontsize=_fontsize).linewidth(1)
                d += elm.Capacitor().label(getUnitsWithScale(Delta/(ZS*w0*w0*gi[i+1]), 'Capacitance'), fontsize=_fontsize).linewidth(1)
            elif (Mask == 'Bandstop'):
                d.push()
                d += elm.Inductor2(loops=2).right().label(getUnitsWithScale(gi[i+1]*ZS*Delta/(w0*w0), 'Inductance'), fontsize=_fontsize).linewidth(1)
                d.pop()
                d += elm.Line().up().length(2).linewidth(1)
                d += elm.Capacitor().right().label(getUnitsWithScale(1/(ZS*Delta*gi[i+1]), 'Capacitance'), fontsize=_fontsize).linewidth(1)
                d += elm.Line().down().length(2).linewidth(1)

    # Draw the last line (if needed) and the load port
    d += elm.Line().right().length(2).linewidth(1)

    d += elm.Dot().label('ZL = ' + str(float("{:.2f}".format(ZS*gi[-1]))) + " \u03A9", fontsize=_fontsize).linewidth(1)
    d += elm.Line(color='white').length(2).linewidth(0)
    
    return d

# This function exports the filter as a Qucs schematic
def getCanonicalFilterQucsSchematic(params):
    # Unpack the dictionary
    gi = params['gi']
    N =  params['N']
    ZS = params['ZS']
    fc = params['fc']
    f1 = params['f1']
    f2 = params['f2']
    FirstElement = params['FirstElement']
    Mask = params['Mask']
    f_start = params['f_start']
    f_stop = params['f_stop']
    n_points = params['n_points']
    Response = params['Response']
    Ripple = params['Ripple']


    if (Mask =='Bandpass' or Mask =='Bandstop'):
        w1 = 2*np.pi*f1*1e6 # rad/s
        w2 = 2*np.pi*f2*1e6 # rad/s
        w0 = np.sqrt(w1*w2)
        Delta = w2-w1
    else:
        w0 = 2*np.pi*fc*1e6 # rad/s

    count_L = 0
    count_C = 0

    # Set initial positions and text
    x = 60 # Current x-position in the schematic
    y = 150 # Current y-position in the schematic
    xtext = 17
    ytext = -26

    schematic = "<Qucs Schematic 0.0.20>\n"

    # Size of the frame
    frame_DIN = 3
    if (((Mask == 'Bandpass') or (Mask == 'Bandstop')) and (N > 5)):
        frame_DIN = 5

    # Frame
    datasetName = "sample.dat"
    title = Response + " " + Mask + " Order " + str(N) + " Filter"
    today = date.today()
    d = today.strftime("%B %d, %Y")
    schematic += ("<Properties>\n<View=0,-60,800,800,0.683014,0,0>\n<Grid=10,10,1>\n<DataSet=" 
                + datasetName
                + ">\n<DataDisplay=sample.dpl>\n<OpenDisplay=0>\n<Script=sample.m>\n<RunScript=0>\n<showFrame=" + str(frame_DIN) + ">\n"
                + "<FrameText0=" + title + ">\n<FrameText1=Drawn By: Andrés Martínez Mera>\n<FrameText2=Date: " 
                + d + ">\n<FrameText3=Revision:>\n</Properties>\n<Symbol>\n</Symbol>\n")

    components = "<Components>\n"
    wires = "<Wires>\n"

    # Source port
    x_padding = 0
    if ((Mask == 'Lowpass') or (Mask == 'Highpass')):
        x_step_LPF = 100 # Spacing
        if (FirstElement == 1): # First shunt - additional padding is needed because of the text of the first element
            x_padding = 60
        ys = y+30
    elif(Mask == 'Bandpass'):
        x_step_BPF = 100 # Spacing
        ys = y+60
        # To upper branch
        x1  = x; x2 = x; y1 = ys-30; y2 = y
        wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"
    else: # Bandstop
        x_step_BSF = 130 # Spacing
        ys = y+120
        # To upper branch
        x1  = x; x2 = x; y1 = ys-30; y2 = ys - 60
        wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"
        
    components += "<Pac P1 1 " + str(x) + " " + str(ys) + " " + str(xtext) + " " + str(ytext) + " 0 1 \"1\" 1 \"" + str(ZS) + " Ohm\" 1 \"0 dBm\" 0 \"1 GHz\" 0>\n"
    components += "<GND *1 5 " + str(x) + " " + str(ys+30) + " 0 0 0 0>\n"

    x += x_padding
    
    # Draw the filter components
    for i in range(N):

        if (((i % 2 == 0) and (FirstElement==1)) or ((i % 2 != 0) and (FirstElement!=1))):    
            # Mask-type transformation
            if (Mask == 'Lowpass'):
                x += x_step_LPF
                C = getUnitsWithScale(gi[i+1]/(ZS*w0), 'Capacitance')
                count_C += 1
                xtext = 17
                ytext = -26
                components += "<C C" + str(count_C) + " 1 " + str(x) + " " + str(y+30) + " " + str(xtext) + " " + str(ytext) + " 0 1 \"" + C + "\" 1 \"\" 0 \"neutral\" 0>\n"
                components += "<GND *1 5 " + str(x) + " " + str(y+60) + " 0 0 0 0>\n"


                x1  = x - (x_step_LPF - 30) # 30 = len(inductor)/2
                x2 = x
                y1 = y
                y2 = y

                if (i == 0):# The first element is shunt and some padding was added
                    if (FirstElement == 1):
                        x1 -= x_padding + 30

                wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"
            elif (Mask == 'Highpass'):
                x += x_step_LPF
                L = getUnitsWithScale(ZS/(gi[i+1]*w0), 'Inductance')
                count_L += 1
                xtext = 17
                ytext = -26
                components += "<L L" + str(count_L) + " 1 " + str(x) + " " + str(y+30) + " " + str(xtext) + " " + str(ytext) + " 0 1 \"" + L + "\" 1 \"\" 0 \"neutral\" 0>\n"
                components += "<GND *1 5 " + str(x) + " " + str(y+60) + " 0 0 0 0>\n"
                
                x1  = x - (x_step_LPF - 30) # 30 = len(inductor)/2
                x2 = x
                y1 = y
                y2 = y
                wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

            elif (Mask == 'Bandpass'):
                step = x_step_BPF
                if ((i == 0) and (FirstElement == 1)):
                    step += 60 # Additional spacing if the first element is shunt
                if (FirstElement == 2):
                    step += 100
                
                x += step
                x -= 30
                C = getUnitsWithScale(gi[i+1]/(ZS*Delta), 'Capacitance')
                count_C += 1
                xtext = -100
                ytext = -26
                components += "<C C" + str(count_C) + " 1 " + str(x) + " " + str(ys) + " " + str(xtext) + " " + str(ytext) + " 0 1 \"" + C + "\" 1 \"\" 0 \"neutral\" 0>\n"
                components += "<GND *1 5 " + str(x) + " " + str(ys+30) + " 0 0 0 0>\n"

                x += 60
                L = getUnitsWithScale(ZS*Delta/(gi[i+1]*w0*w0), 'Inductance')
                count_L += 1
                xtext = 17
                ytext = -26
                components += "<L L" + str(count_L) + " 1 " + str(x) + " " + str(y+60) + " " + str(xtext) + " " + str(ytext) + " 1 1 \"" + L + "\" 1 \"\" 0 \"neutral\" 0>\n"
                components += "<GND *1 5 " + str(x) + " " + str(y+90) + " 0 0 0 0>\n"

                # To the previous element
                if (i == 0):
                    x1  = x-step-30; x2 = x-30; y1 = y; y2 = y # +100 because x is at the center of the series resonator
                else:
                    x1  = x-step+100; x2 = x-30; y1 = y; y2 = y # +100 because x is at the center of the series resonator
                wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

                # Vertical line
                x1  = x-30; x2 = x-30; y1 = y; y2 = ys-30
                wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

                # To the left
                x1  = x-30; x2 = x-60; y1 = ys-30; y2 = ys-30
                wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

                # To the right
                x1  = x-30; x2 = x; y1 = ys-30; y2 = ys-30
                wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

                # To the right (upper)
                x1  = x-30; x2 = x; y1 = y; y2 = y
                wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

            elif (Mask == 'Bandstop'):
                x += x_step_BSF
                L = getUnitsWithScale(ZS/(gi[i+1]*Delta), 'Inductance')
                count_L += 1
                xtext = 17
                ytext = -26
                components += "<L L" + str(count_L) + " 1 " + str(x) + " " + str(ys) + " " + str(xtext) + " " + str(ytext) + " 1 1 \"" + L + "\" 1 \"\" 0 \"neutral\" 0>\n"
                
                C = getUnitsWithScale(gi[i+1]*Delta/(ZS*w0*w0), 'Capacitance')
                count_C += 1
                ytext = -26
                components += "<C C" + str(count_C) + " 1 " + str(x) + " " + str(ys+90) + " " + str(xtext) + " " + str(ytext) + " 1 1 \"" + C + "\" 1 \"\" 0 \"neutral\" 0>\n"
                components += "<GND *1 5 " + str(x) + " " + str(ys+120) + " 0 0 0 0>\n"

                # Inductor to the mainline
                x1  = x; x2 = x; y1 = ys-30; y2 = ys-60
                wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

                # Between capacitor and inductor
                x1  = x; x2 = x; y1 = ys+30; y2 = ys+60
                wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

                # To the previous element
                if (i == 0):
                    x1  = x-x_step_BSF; x2 = x; y1 = y+60; y2 = y+60
                else:
                    x1  = x-x_step_BSF+30; x2 = x; y1 = y+60; y2 = y+60
                wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

                
        else:
            # Mask-type transformation
            if (Mask == 'Lowpass'):
                x += x_step_LPF
                L = getUnitsWithScale(ZS*gi[i+1]/w0, 'Inductance')
                count_L += 1
                xtext = -40
                ytext = -60
                components += "<L L"+ str(count_L) + " 1 " + str(x) + " " + str(y) + " " + str(xtext) + " " + str(ytext) + " 0 0 \"" + L + "\" 1 \"\" 0 \"neutral\" 0>\n"

                x1  = x - x_step_LPF
                x2 = x - 30 # len(inductor)/2
                y1 = y
                y2 = y
                wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

            elif (Mask == 'Highpass'):
                x += x_step_LPF
                C = getUnitsWithScale(1/(gi[i+1]*w0*ZS), 'Capacitance')
                count_C += 1
                xtext = -40
                ytext = -60
                components += "<C C"+ str(count_C) + " 1 " + str(x) + " " + str(y) + " " + str(xtext) + " " + str(ytext) + " 0 0 \"" + C + "\" 1 \"\" 0 \"neutral\" 0>\n"

                x1  = x - x_step_LPF
                x2 = x - 30 # len(inductor)/2
                y1 = y
                y2 = y
                wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

            elif (Mask == 'Bandpass'):
                x += x_step_BPF

                C = getUnitsWithScale(Delta/(ZS*w0*w0*gi[i+1]), 'Capacitance')
                count_C += 1
                xtext = -40
                ytext = -60
                components += "<C C"+ str(count_C) + " 1 " + str(x) + " " + str(y) + " " + str(xtext) + " " + str(ytext) + " 0 0 \"" + C + "\" 1 \"\" 0 \"neutral\" 0>\n"

                L = getUnitsWithScale(ZS*gi[i+1]/(Delta), 'Inductance')
                count_L += 1
                xtext = -40
                ytext = -60
                components += "<L L"+ str(count_L) + " 1 " + str(x+100) + " " + str(y) + " " + str(xtext) + " " + str(ytext) + " 0 0 \"" + L + "\" 1 \"\" 0 \"neutral\" 0>\n"

                # To the previous section
                x1  = x-x_step_BPF; x2 = x-30; y1 = y; y2 = y
                wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

                # Between inductor and capacitor
                x1  = x+30; x2 = x+70; y1 = y; y2 = y
                wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

            elif (Mask == 'Bandstop'):
                x += x_step_BSF
                L = getUnitsWithScale(gi[i+1]*ZS*Delta/(w0*w0), 'Inductance')
                count_L += 1
                xtext = -30; ytext = 10
                components += "<L L" + str(count_L) + " 1 " + str(x) + " " + str(y+60) + " " + str(xtext) + " " + str(ytext) + " 0 0 \"" + L + "\" 1 \"\" 0 \"neutral\" 0>\n"

                C = getUnitsWithScale(1/(ZS*Delta*gi[i+1]), 'Capacitance')
                count_C += 1
                ytext = -60
                components += "<C C"+ str(count_C) + " 1 " + str(x) + " " + str(y) + " " + str(xtext) + " " + str(ytext) + " 0 0 \"" + C + "\" 1 \"\" 0 \"neutral\" 0>\n"

                # Between first node and inductor
                x1  = x-60; x2 = x-30; y1 = y+60; y2 = y+60
                wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

                # Between first node and capacitor
                x1  = x-60; x2 = x-30; y1 = y; y2 = y
                wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

                # First node
                x1  = x-60; x2 = x-60; y1 = y; y2 = y+60
                wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

                # Between second node and inductor
                x1  = x+60; x2 = x+30; y1 = y+60; y2 = y+60
                wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

                # Between second node and capacitor
                x1  = x+60; x2 = x+30; y1 = y; y2 = y
                wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

                # Second node
                x1  = x+60; x2 = x+60; y1 = y; y2 = y+60
                wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

                # To the previous element
                x1  = x-x_step_BSF; x2 = x-60; y1 = y+60; y2 = y+60
                wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

    # Load port
    if ((Mask == 'Lowpass') or (Mask == 'Highpass')):
        x_last = 100 # Additional padding
        x1 = x 
        if (((FirstElement == 2) and (N % 2 == 1)) or ((FirstElement == 1) and (N % 2 == 0))):
            x1 += 30
        else:
            x_last += 30 # Extra padding is needed for the text of the last element

        x += x_last # Position of the port

        x2 = x
        y1 = y
        y2 = y
        wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

    elif (Mask == 'Bandpass'):
        x_last = 200
        if (((FirstElement == 1) and (N % 2 == 1)) or ((FirstElement == 2) and (N % 2 == 0))):
            x1 = x
            x_last -= 50
        else:
            x1  = x+130
        
        # To the load port
        x2 = x+x_last; y1 = y; y2 = y
        wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"
        
        x += x_last
        # To upper branch
        x1  = x; x2 = x; y1 = ys-30; y2 = y
        wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"
    else: # Bandstop
        x_last = x_step_BSF
        if (((FirstElement == 1) and (N % 2 == 1)) or ((FirstElement == 2) and (N % 2 == 0))):
            x1 = x
            x_last += 30
        else:
            x1  = x+60
        
        # To the load port
        x2 = x+x_last; y1 = y+60; y2 = y+60
        wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"
        
        x += x_last
        # To upper branch
        x1  = x; x2 = x; y1 = ys-30; y2 = ys-60
        wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

    xtext = 17
    ytext = -26
    RL = round(ZS*gi[-1], 2)
    components += "<Pac P2 1 " + str(x) + " " + str(ys) + " " + str(xtext) + " " + str(ytext) + " 0 1 \"2\" 1 \"" + str(RL) + " Ohm\" 1 \"0 dBm\" 0 \"1 GHz\" 0>\n"
    components += "<GND *1 5 " + str(x) + " " + str(ys+30) + " 0 0 0 0>\n"


    # S-parameter simulation block
    x_block = 60
    y_block = ys + 150
    components += "<.SP SP1 1 " + str(x_block) + " " + str(y_block) + " 0 67 0 0 \"lin\" 1 \"" + str(f_start) + " MHz \" 1 \"" + str(f_stop) + " MHz \" 1 \"" + str(n_points) + "\" 1 \"no\" 0 \"1\" 0 \"2\" 0>\n"
    components += "<Eqn Eqn1 1 " + str(x_block + 200) + " " + str(y_block) + " -28 15 0 0 \"S21_dB=dB(S[2,1])\" 1 \"S11_dB=dB(S[1,1])\" 1 \"S22_dB=dB(S[2,2])\" 1 \"yes\" 0>\n"
    components += "<Eqn Eqn2 1 " + str(x_block + 400) + " " + str(y_block) + " -28 15 0 0 \"gd=groupdelay(S,2,1)\" 1 \"phase=(180/pi)*angle(S[2,1])\" 1 \"yes\" 0>\n"

    # Close components and wire blocks
    components += "</Components>\n"
    wires += "</Wires>\n"

    # Text
    y_title = str(50)
    paintings = "<Paintings>\n"

    copyright = " - Copyright \u00A9 2020-" + str(today.year) + " Andrés Martínez Mera - GNU Public License Version 3"
    if ((Response == 'Chebyshev')):
        paintings += ("<Text 50" + " " + y_title + " 15 #000000 0 \"" + Response + " Order " + str(N) + " " + Mask + " Filter, Ripple " + str(Ripple) + " dB "
                + str(fc) + " MHz, Z_0 = " + str(ZS) + " Ohm" + copyright + "\">\n")
    else:
        paintings += ("<Text 50" + " " + y_title + " 15 #000000 0 \"" + Response + " Order " + str(N) + " " + Mask + " Filter, "
                + str(fc) + " MHz, Z_0 = " + str(ZS) + " Ohm" + copyright + "\">\n")
    

    # Diagrams
    x_size = 400
    y_size = 300
    x_pos = 170
    y_pos = ys + 650
    diagrams = "<Diagrams>\n"
    # Response
    paintings += ("<Text " + str(x_pos + round(x_size/2) - 50) + " " + str(y_pos - y_size - 40) + " 18 #000000 0 \"" + "Response\">\n")
    diagrams += ("<Rect " + str(x_pos) + " " + str(y_pos) +" " + str(x_size) + " " + str(y_size) + " 3 #c0c0c0 1 00 1 0 0.2 1 0 -50 5 5 1 -0.1 0.5 1.1 315 0 225 \"\" \"\" \"\" \"\">\n")
    diagrams += str("<\"S21_dB\" #ff0000 0 3 0 0 0>\n")
    diagrams += str("<\"S11_dB\" #0000ff 0 3 0 0 0>\n")
    diagrams += "</Rect>\n"
    
    # Group Delay and phase
    paintings += ("<Text " + str(x_pos + x_size + 100 + round(x_size/2) - 120) + " " + str(y_pos - y_size - 40) + " 18 #000000 0 \"" + "Group Delay and Phase\">\n")
    diagrams += ("<Rect " + str(x_pos + x_size + 100 ) + " " + str(y_pos) +" " + str(x_size) + " " + str(y_size) + " 3 #c0c0c0 1 00 1 0 0.2 1 1 -4 1 4 0 -180 90 180 315 0 225 \"\" \"\" \"\" \"\">\n")
    diagrams += str("<\"gd\" #0000ff 0 3 0 0 0>\n")
    diagrams += str("<\"phase\" #00aa00 0 3 0 0 1>\n")
    diagrams += "</Rect>\n"

    diagrams += "</Diagrams>\n"
    paintings += "</Paintings>\n"

    schematic += components
    schematic += wires
    schematic += paintings
    schematic += diagrams
    
    return schematic