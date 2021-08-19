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


def getCanonicalFilterNetwork(gi, N, ZS, ZL, fc, f1, f2, FirstElement, Mask, f_start, f_stop, n_points):              
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
    # circuit = rf.Circuit(connections)
    # d = circuit.network
    # a = network2.Network.from_ntwkv1(circuit.network)
    # S = a.s.val[:]
    # freq = a.frequency.f*1e-6
    # S11 = 20*np.log10(np.abs(S[:,1][:,1]))
    # S21 = 20*np.log10(np.abs(S[:,1][:,0]))
    # return freq, S11, S21

    return connections


def getCanonicalFilterSchematic(gi, N, ZS, ZL, fc, f1, f2, FirstElement, Mask, f_start, f_stop, n_points):
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