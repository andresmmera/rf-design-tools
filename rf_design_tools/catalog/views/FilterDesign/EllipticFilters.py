# Copyright 2020-2021 Andrés Martínez Mera - andresmartinezmera@gmail.com
import numpy as np

# Schematic drawing
import schemdraw as schem
import schemdraw.elements as elm
from skrf.mathFunctions import find_closest

# Get units with scale, etc.
from ..utilities import *

# standard imports
import skrf as rf
from skrf import network2

# Import for the generation of the Qucs schematic
from datetime import date

# Reference:
# [1] "Elliptic Approximation and Elliptic Filter Design on Small Computers",
# Pierre Amstutz, IEEE Transactions on Circuits and Systems, vol. CAS-25, No 12, December 1978

# as: Stopband attenuation
# ap: in-band attenuation
# M: Number of peaks
# RS: Source impedance

def Sn(u, z):
    x = np.tanh(z)
    for j in range (1, 9):
        x = x * (np.tanh(j * u - z) * np.tanh(j * u + z));
    return x

# [1] "Elliptic Approximation and Elliptic Filter Design on Small Computers", Pierre Amstutz, IEEE Transactions on Circuits and Systems, vol. CAS-25, No 12, December 1978
def EllipticTypeS_Coefficients(a_s, a_p, N):

    dbn = 0.23025851; # dB -> Np conversion

    M = 2 * N + 1;
    u = (np.pi * np.pi) / (np.log(16 * (np.exp(a_s * dbn) - 1) / (np.exp(a_p * dbn) - 1)));
    w = (u / (2 * np.pi)) * np.log((np.exp(a_p * dbn / 2) + 1) / (np.exp(a_p * dbn / 2) - 1));
    # Resize elliptic network parameters
    E = np.empty(N, dtype=float)
    F = np.empty(M-1, dtype=float) 
    E[N - 1] = np.tan(w);
    a0 = 1 / np.tan(u * (a_s + np.log(2)) / np.pi);
    

    # Calculation of the natural frequencies = Sn(M*u, j*u) j \in [1, M-1]
    for j in range(1, M):
        F[j - 1] = Sn(M * u, j * u);

    # Calculation of a0 Eqn (4.34)
    K = 1;
    j = 1;
    delta = 1
    while (delta > 1e-6):
        Kaux = K * (np.power(np.tan(w), 2) + np.power(np.tanh(j * M * u), 2)) / (1 + np.power(np.tan(w) * np.tanh(j * M * u), 2));
        delta = np.abs(K - Kaux);
        K = Kaux;
        j += 1
  
    a0 = np.tan(w) * K;
    E[N - 1] = a0;
    

    Cseries = np.empty(N, dtype=float)
    Lseries = np.empty(N+1, dtype=float)
    Cshunt = np.empty(N+1, dtype=float)
    
    # Delay group at the natural frequencies
    for j in range(0, N):
        Cseries[j] = F[2 * j + 1] * (1 - np.power(F[j], 4)) / F[j]; # Eqn 5.7
        

    C = np.empty(N, dtype=float)
    C[0] = (1 / (a0 * F[N])); # Starting value for dB/dw calculation
    
  
    for j in range (1, N):
        C[j] = (C[j - 1] - a0 * F[N - j - 1]) / (1 + C[j - 1] * a0 * F[N - j - 1]);
        E[N - j - 1] =  E[N - j] + E[N - 1] * Cseries[j - 1] / (1 + np.power(a0 * F[j - 1], 2)); # Ej=(Dj/Fj)*dB/dw(1/Fj)

    for j in range (0, N):
        Lseries[j] = ((1 + np.power(C[j], 2)) * E[j] / Cseries[j] - C[j] / F[j]) / 2.;
        Cshunt[j] = C[j] * F[j];

    Lseries[N] = Lseries[N - 1];
    Cshunt[N] = Cshunt[N - 1];

    # Permutations method Eqn (3.6)
    for l in range(0, 2):
        for k in range(l+2, N+1, 2):
            for j in range(l, k-1, 2):
                U = Cshunt[j] - Cshunt[k]
                V = 1 / (U / ((F[k] * F[k] - F[j] * F[j]) * Lseries[j]) - 1);
                Cshunt[k] = U * V;
                Lseries[k] = (V * V) * Lseries[k] - (np.power(V + 1, 2)) * Lseries[j];

    # Impedance and frequency scaling
    for j in range(0, N):
        Cseries[j] = Lseries[j] * F[j] * F[j];
        Lseries[j] = 1 / Lseries[j];

    Lseries = Lseries[:-1].copy()
    return Lseries, Cseries, Cshunt

def SynthesizeEllipticFilter(Lseries, Cseries, Cshunt, Elliptic_Type, FilterType, FirstShunt, RS, RL, fc, bw, fstart, fstop, npoints):
    N = len(Lseries)
    
    # Draw circuit
    schem.use('svg')
    d = schem.Drawing(inches_per_unit = 0.3)
    _fontsize = 8
    
    # Network
    rf.stylely()
    freq = rf.Frequency(start=fstart, stop=fstop, npoints=npoints, unit='MHz')
    line = rf.media.DefinedGammaZ0(frequency=freq)
    
    # Component counter
    count_C = 0
    count_L = 0
    count_gnd = 0

    # Array of components
    C = []
    L = []
    ground = []
    
    # Source port
    # Drawing: Source port and the first line
    d += elm.Line(color='white').length(2).linewidth(0)
    d += elm.Dot().label('ZS = ' + str(RS) + " \u03A9", fontsize=_fontsize).linewidth(1)
    d += elm.Line().length(2).linewidth(1)

    # Network: Port 1
    Port1 = rf.Circuit.Port(frequency=freq, name='port1', z0=RS)

    connections = [] # Network connections

    # LOWPASS - FIRST SHUNT
    if (FilterType == "Lowpass" and FirstShunt == 1):  
        # Filter components
        for i in range(N):
            
            ## Shunt capacitor
            # Drawing
            d.push() # Save the drawing point for later
            Cshunt_ = Cshunt[i] / (2 * np.pi * fc * RS)
            d += elm.Capacitor().down().label(getUnitsWithScale(Cshunt_, 'Capacitance'), fontsize=_fontsize).linewidth(1)
            d += elm.Ground().linewidth(1)
            
            # Network
            count_C += 1
            C.append(line.capacitor(Cshunt_, name='C' + str(count_C)))
            count_gnd += 1
            ground.append(rf.Circuit.Ground(frequency=freq, name='ground' + str(count_gnd), z0=RS))
            
            ## Series inductor
            # Drawing
            d.pop()
            d.push()
            Lseries_ = Lseries[i] * RS / (2 * np.pi * fc);
            d += elm.Inductor2(loops=2).right().label(getUnitsWithScale(Lseries_, 'Inductance'), fontsize=_fontsize).linewidth(1)
            
            # Network
            count_L += 1
            L.append(line.inductor(Lseries_, name='L' + str(count_L)))
            
            
            ## Series capacitor
            if (Elliptic_Type == 'Type A' or Elliptic_Type == 'Type S' or ((i < N-1) and (Elliptic_Type == 'Type B' or Elliptic_Type == 'Type C'))):
                # Drawing
                d.pop()
                d += elm.Line().up().length(2).linewidth(1)
                d += elm.Line().right().length(0).linewidth(1)
                Cseries_ = Cseries[i] / (2 * np.pi * fc * RS)
                d += elm.Capacitor().right().label(getUnitsWithScale(Cseries_, 'Capacitance'), fontsize=_fontsize).linewidth(1)
                d += elm.Line().right().length(0).linewidth(1)
                d += elm.Line().down().length(2).linewidth(1)
                d += elm.Dot()
                
                # Network
                count_C += 1
                C.append(line.capacitor(Cseries_, name='C' + str(count_C)))
                          
            
            
            if ((i == N-1) and (Elliptic_Type == 'Type A' or Elliptic_Type == 'Type S')):
                d.push()
                
            # Make connections
            if (i < N): # The last connection must be done after the load port instantiation
                if (i == 0): # The first node must include the source port
                    connections.append([(Port1, 0), (C[0], 0), (C[1], 0), (L[0],0)])
                    connections.append([(C[0], 1), (ground[0], 0)])
                elif (i < N-1): # The other nodes must connect the current component with the ones from the last iteration
                    connections.append([(C[2*i-1], 1), (L[i-1],1), (C[2*i], 0), (L[i],0), (C[2*i+1], 0)])
                    connections.append([(C[2*i], 1), (ground[i], 0)])
                else:
                    if(Elliptic_Type == 'Type A' or Elliptic_Type == 'Type S'):# Types A and S have a resonator in the last position. In this sense, these lines are the same as above
                        connections.append([(C[2*i-1], 1), (L[i-1],1), (C[2*i], 0), (L[i],0), (C[2*i+1], 0)])
                        connections.append([(C[2*i], 1), (ground[i], 0)])
                    else:# Types B and C
                        connections.append([(C[2*i-1], 1), (L[i-1],1), (C[2*i], 0), (L[i],0)])
                        connections.append([(C[2*i], 1), (ground[i], 0)])
            
        
        if (Elliptic_Type == 'Type A' or Elliptic_Type == 'Type S'):
            # Drawing
            Cshunt_ = Cshunt[-1]/ (2 * np.pi * fc * RS)
            d += elm.Capacitor().down().label(getUnitsWithScale(Cshunt_, 'Capacitance'), fontsize=_fontsize).linewidth(1)
            d += elm.Ground().linewidth(1)
            d.pop()
            
            # Network
            count_C += 1
            C.append(line.capacitor(Cshunt_, name='C' + str(count_C)))
            count_gnd += 1
            ground.append(rf.Circuit.Ground(frequency=freq, name='ground' + str(count_gnd), z0=RS))
            
        # Load port
        # Drawing
        d += elm.Line().right().length(2).linewidth(1)
        d += elm.Dot().label('ZL = ' + str(float("{:.2f}".format(RL))) + " \u03A9", fontsize=_fontsize).linewidth(1)
        d += elm.Line(color='white').length(2).linewidth(0)
        
        # Network
        Port2 = rf.Circuit.Port(frequency=freq, name='port2', z0=RL)
        if (Elliptic_Type == 'Type A' or Elliptic_Type == 'Type S'):
            connections.append([(Port2, 0), (C[-2], 1), (C[-1], 0), (L[-1] , 1)])
            connections.append([(C[-1], 1), (ground[-1] , 0)])
        else:
            connections.append([(Port2, 0), (L[-1] , 1)])
            
    # LOWPASS - FIRST SERIES
    if (FilterType == "Lowpass" and FirstShunt == 2):  
        # Filter components
        count_L = 0
        for i in range(N):
            
            ## Series inductor
            # Drawing
            Lseries_ = RS / (2 * np.pi * fc) * Cshunt[i]
            d += elm.Inductor2(loops=2).right().label(getUnitsWithScale(Lseries_, 'Inductance'), fontsize=_fontsize).linewidth(1)
            
            # Network
            count_L += 1
            L.append(line.inductor(Lseries_, name='L' + str(count_L)))      
            
            
            ## Shunt capacitor
            d.push() # Save the drawing point for later
            Cshunt_ = 1 / (2 * np.pi * fc * RS) * Lseries[i];
            d += elm.Capacitor().down().label(getUnitsWithScale(Cshunt_, 'Capacitance'), fontsize=_fontsize).linewidth(1)
            
            # Network
            count_C += 1
            C.append(line.capacitor(Cshunt_, name='C' + str(count_C)))
            
            if (Elliptic_Type == 'Type A' or Elliptic_Type == 'Type S' or ((i < N-1) and (Elliptic_Type == 'Type B' or Elliptic_Type == 'Type C'))):
                ## Shunt inductor
                # Drawing
                Lshunt_ = RS / (2 * np.pi * fc) * Cseries[i];
                d += elm.Inductor2(loops=2).down().label(getUnitsWithScale(Lshunt_, 'Inductance'), fontsize=_fontsize).linewidth(1)
                d += elm.Ground().linewidth(1)

                # Network
                count_L += 1
                L.append(line.inductor(Lshunt_, name='L' + str(count_L)))
                count_gnd += 1
                ground.append(rf.Circuit.Ground(frequency=freq, name='ground' + str(count_gnd), z0=RS))
            else:
                d += elm.Ground().linewidth(1)
                count_gnd += 1
                ground.append(rf.Circuit.Ground(frequency=freq, name='ground' + str(count_gnd), z0=RS))
            
            d.pop()
                
            # Make connections
            if (i == 0): # The first node must include the source port
                connections.append([(Port1, 0), (L[0],0)])
            elif (i < N): # The other nodes must connect the current component with the ones from the last iteration
                connections.append([(L[2*i-2],1), (L[2*i],0), (C[i-1], 0)])
                connections.append([(L[2*i-1], 0), (C[i-1], 1)])
                connections.append([(L[2*i-1], 1), (ground[i-1], 0)])
            
        if (Elliptic_Type == 'Type A' or Elliptic_Type == 'Type S'):
            # Drawing
            Lseries_ = RS / (2 * np.pi * fc) * Cshunt[-1]
            d += elm.Inductor2(loops=2).right().label(getUnitsWithScale(Lseries_, 'Inductance'), fontsize=_fontsize).linewidth(1)

            # Network
            count_L += 1
            L.append(line.inductor(Lseries_, name='L' + str(count_L)))

        if(Elliptic_Type == 'Type A' or Elliptic_Type == 'Type S'):# Types A and S have a resonator in the last position. In this sense, these lines are the same as above
            connections.append([(L[-3],1), (L[-1],0), (C[-1], 0)])
            connections.append([(L[-2], 0), (C[-1], 1)])
            connections.append([(L[-2], 1), (ground[-1], 0)])
        else:# Types B and C
            connections.append([(C[-1], 1), (ground[-1], 0)])
        
        # Load port
        if ((Elliptic_Type != 'Type S') and (Elliptic_Type != 'Type C')):
            RL = RS*RS/RL
            
        # Drawing
        d += elm.Line().right().length(2).linewidth(1)
        d += elm.Dot().label('ZL = ' + str(float("{:.2f}".format(RL))) + " \u03A9", fontsize=_fontsize).linewidth(1)
        d += elm.Line(color='white').length(2).linewidth(0)

        # Network
        Port2 = rf.Circuit.Port(frequency=freq, name='port2', z0=RL)
        if (Elliptic_Type == 'Type A' or Elliptic_Type == 'Type S'):
            connections.append([(Port2, 0), (L[-1] , 1)])
        else:
            connections.append([(Port2, 0), (C[-1] , 0), (L[-1], 1)])
            
      
    # HIGHPASS - FIRST SERIES
    if (FilterType == "Highpass" and FirstShunt == 2):  
        # Filter components
        count_L = 0
        for i in range(N):
            
            ## Series capacitor
            # Drawing
            Cseries_ = 1 / (2 * np.pi * fc * RS * Cshunt[i])
            d += elm.Capacitor().right().label(getUnitsWithScale(Cseries_, 'Capacitance'), fontsize=_fontsize).linewidth(1)
            
            # Network
            count_C += 1
            C.append(line.capacitor(Cseries_, name='C' + str(count_C)))      
            
            
            ## Shunt inductor
            d.push() # Save the drawing point for later
            Lshunt_ = RS / (2 * np.pi * fc * Lseries[i]);
            d += elm.Inductor2(loops=2).down().label(getUnitsWithScale(Lshunt_, 'Inductance'), fontsize=_fontsize).linewidth(1)
            
            # Network
            count_L += 1
            L.append(line.inductor(Lshunt_, name='L' + str(count_L)))
            
            if (Elliptic_Type == 'Type A' or Elliptic_Type == 'Type S' or ((i < N-1) and (Elliptic_Type == 'Type B' or Elliptic_Type == 'Type C'))):
                ## Shunt capacitor
                # Drawing
                Cshunt_ = 1 / (2 * np.pi * fc * RS * Cseries[i]);
                d += elm.Capacitor().down().label(getUnitsWithScale(Cshunt_, 'Capacitance'), fontsize=_fontsize).linewidth(1)
                d += elm.Ground().linewidth(1)

                # Network
                count_C += 1
                C.append(line.capacitor(Cshunt_, name='C' + str(count_C)))
                count_gnd += 1
                ground.append(rf.Circuit.Ground(frequency=freq, name='ground' + str(count_gnd), z0=RS))
            else:
                d += elm.Ground().linewidth(1)
                count_gnd += 1
                ground.append(rf.Circuit.Ground(frequency=freq, name='ground' + str(count_gnd), z0=RS))
            
            d.pop()
                
            # Make connections
            if (i == 0): # The first node must include the source port
                connections.append([(Port1, 0), (C[0],0)])
            elif (i < N): # The other nodes must connect the current component with the ones from the last iteration
                connections.append([(C[2*i-2],1), (C[2*i],0), (L[i-1], 0)])
                connections.append([(C[2*i-1], 0), (L[i-1], 1)])
                connections.append([(C[2*i-1], 1), (ground[i-1], 0)])
            
        if (Elliptic_Type == 'Type A' or Elliptic_Type == 'Type S'):
            # Drawing
            Cseries_ = 1 / (2 * np.pi * fc * RS * Cshunt[-1])
            d += elm.Capacitor().right().label(getUnitsWithScale(Cseries_, 'Capacitance'), fontsize=_fontsize).linewidth(1)

            # Network
            count_C += 1
            C.append(line.capacitor(Cseries_, name='C' + str(count_C)))

        if(Elliptic_Type == 'Type A' or Elliptic_Type == 'Type S'):# Types A and S have a resonator in the last position. In this sense, these lines are the same as above
            connections.append([(C[-3], 1), (C[-1],0), (L[-1], 0)])
            connections.append([(C[-2], 0), (L[-1], 1)])
            connections.append([(C[-2], 1), (ground[-1], 0)])
        else:# Types B and C
            connections.append([(L[-1], 1), (ground[-1], 0)])

    
        # Load port
        if ((Elliptic_Type != 'Type S') and (Elliptic_Type != 'Type C')):
            RL = RS*RS/RL
        
        # Drawing
        d += elm.Line().right().length(2).linewidth(1)
        d += elm.Dot().label('ZL = ' + str(float("{:.2f}".format(RL))) + " \u03A9", fontsize=_fontsize).linewidth(1)
        d += elm.Line(color='white').length(2).linewidth(0)

        # Network
        Port2 = rf.Circuit.Port(frequency=freq, name='port2', z0=RL)
        if (Elliptic_Type == 'Type A' or Elliptic_Type == 'Type S'):
            connections.append([(Port2, 0), (C[-1] , 1)])
        else:
            connections.append([(Port2, 0), (L[-1] , 0), (C[-1], 1)])

    # HIGHPASS - FIRST SHUNT
    if (FilterType == "Highpass" and FirstShunt == 1):  
        # Filter components
        for i in range(N):
            
            ## Shunt inductor
            # Drawing
            d.push() # Save the drawing point for later
            Lshunt_ = RS / (2 * np.pi * fc * Cshunt[i]);
            d += elm.Inductor2(loops=2).down().label(getUnitsWithScale(Lshunt_, 'Inductance'), fontsize=_fontsize).linewidth(1)
            d += elm.Ground().linewidth(1)
            
            # Network
            count_L += 1
            L.append(line.inductor(Lshunt_, name='L' + str(count_L)))
            count_gnd += 1
            ground.append(rf.Circuit.Ground(frequency=freq, name='ground' + str(count_gnd), z0=RS))
            
            ## Series capacitor
            # Drawing
            d.pop()
            d.push()
            Cseries_ = 1 / (2 * np.pi * fc * RS * Lseries[i]);
            d += elm.Capacitor().right().label(getUnitsWithScale(Cseries_, 'Capacitance'), fontsize=_fontsize).linewidth(1)
            
            # Network
            count_C += 1
            C.append(line.capacitor(Cseries_, name='C' + str(count_C)))
            
            
            ## Series inductor
            if (Elliptic_Type == 'Type A' or Elliptic_Type == 'Type S' or ((i < N-1) and (Elliptic_Type == 'Type B' or Elliptic_Type == 'Type C'))):
                # Drawing
                d.pop()
                d += elm.Line().up().length(2).linewidth(1)
                d += elm.Line().right().length(0).linewidth(1)
                Lseries_ = RS / (2 * np.pi * fc * Cseries[i])
                d += elm.Inductor2(loops=2).right().label(getUnitsWithScale(Lseries_, 'Inductance'), fontsize=_fontsize).linewidth(1)
                d += elm.Line().right().length(0).linewidth(1)
                d += elm.Line().down().length(2).linewidth(1)
                d += elm.Dot()
                
                # Network
                count_L += 1
                L.append(line.inductor(Lseries_, name='L' + str(count_L)))
                          
            
            
            if ((i == N-1) and (Elliptic_Type == 'Type A' or Elliptic_Type == 'Type S')):
                d.push()
                
            # Make connections
            if (i < N): # The last connection must be done after the load port instantiation
                if (i == 0): # The first node must include the source port
                    connections.append([(Port1, 0), (L[0], 0), (L[1], 0), (C[0],0)])
                    connections.append([(L[0], 1), (ground[0], 0)])
                elif (i < N-1): # The other nodes must connect the current component with the ones from the last iteration
                    connections.append([(L[2*i-1], 1), (C[i-1],1), (L[2*i], 0), (C[i],0), (L[2*i+1], 0)])
                    connections.append([(L[2*i], 1), (ground[i], 0)])
                else:
                    if(Elliptic_Type == 'Type A' or Elliptic_Type == 'Type S'):# Types A and S have a resonator in the last position. In this sense, these lines are the same as above
                        connections.append([(L[2*i-1], 1), (C[i-1],1), (L[2*i], 0), (C[i],0), (L[2*i+1], 0)])
                        connections.append([(L[2*i], 1), (ground[i], 0)])
                    else:# Types B and C
                        connections.append([(L[2*i-1], 1), (C[i-1],1), (L[2*i], 0), (C[i],0)])
                        connections.append([(L[2*i], 1), (ground[i], 0)])
            
        
        if (Elliptic_Type == 'Type A' or Elliptic_Type == 'Type S'):
            # Drawing
            Lshunt_ = RS / (2 * np.pi * fc * Cshunt[-1])
            d += elm.Inductor2(loops=2).down().label(getUnitsWithScale(Lshunt_, 'Inductance'), fontsize=_fontsize).linewidth(1)
            d += elm.Ground().linewidth(1)
            d.pop()
            
            # Network
            count_L += 1
            L.append(line.inductor(Lshunt_, name='L' + str(count_L)))
            count_gnd += 1
            ground.append(rf.Circuit.Ground(frequency=freq, name='ground' + str(count_gnd), z0=RS))
            
        # Load port
        # Drawing
        d += elm.Line().right().length(2).linewidth(1)
        d += elm.Dot().label('ZL = ' + str(float("{:.2f}".format(RL))) + " \u03A9", fontsize=_fontsize).linewidth(1)
        d += elm.Line(color='white').length(2).linewidth(0)
        
        # Network
        Port2 = rf.Circuit.Port(frequency=freq, name='port2', z0=RL)
        if (Elliptic_Type == 'Type A' or Elliptic_Type == 'Type S'):
            connections.append([(L[-1], 1), (ground[-1] , 0)])
            connections.append([(Port2, 0), (L[-2], 1), (L[-1], 0), (C[-1] , 1)])
        else:
            connections.append([(Port2, 0), (C[-1] , 1)])

    # BANDPASS - FIRST SHUNT
    if (FilterType == "Bandpass" and FirstShunt == 1):
        Kl = RS / (2 * np.pi * fc);
        Kc = 1 / (RS  * 2 * np.pi * fc)
        delta = bw / fc;
        # Filter components
        for i in range(N):
            
            ## Shunt parallel resonator
            # Drawing
            d.push() # Save the drawing point for later
            Cshunt_ = Cshunt[i] * Kc / delta
            d += elm.Line().down().length(1).linewidth(1)
            d += elm.Line().left().length(1).linewidth(1)
            d += elm.Line().down().length(1).linewidth(1)
            d += elm.Capacitor().down().label(getUnitsWithScale(Cshunt_, 'Capacitance'), fontsize=_fontsize).linewidth(1)
            d += elm.Ground().linewidth(1)
            
            d.pop()
            d.push()
            Lshunt_ =  Kl * delta / (Cshunt[i]);
            d += elm.Line().down().length(1).linewidth(1)
            d += elm.Line().right().length(1).linewidth(1)
            d += elm.Line().down().length(1).linewidth(1)
            d += elm.Inductor2(loops=2).down().label(getUnitsWithScale(Lshunt_, 'Inductance'), fontsize=_fontsize).linewidth(1)
            d += elm.Ground().linewidth(1)
            
            # Network
            count_C += 1
            C.append(line.capacitor(Cshunt_, name='C' + str(count_C)))
            count_gnd += 1
            ground.append(rf.Circuit.Ground(frequency=freq, name='ground' + str(count_gnd), z0=RS))
            
            count_L += 1
            L.append(line.inductor(Lshunt_, name='L' + str(count_L)))
            count_gnd += 1
            ground.append(rf.Circuit.Ground(frequency=freq, name='ground' + str(count_gnd), z0=RS))
            
            ## Upper-branch series resonator
            # Drawing
            d.pop()
            d.push()
            Lseries_ = Kl * Lseries[i] / delta;
            d += elm.Inductor2(loops=2).right().label(getUnitsWithScale(Lseries_, 'Inductance'), fontsize=_fontsize).linewidth(1)
            Cseries_ = Kc * delta / Lseries[i];
            d += elm.Capacitor().right().label(getUnitsWithScale(Cseries_, 'Capacitance'), fontsize=_fontsize).linewidth(1)

            
            # Network
            count_L += 1
            L.append(line.inductor(Lseries_, name='L' + str(count_L)))
            count_C += 1
            C.append(line.capacitor(Cseries_, name='C' + str(count_C)))
            
            
            ## Upper-branch parallel resonator
            if (Elliptic_Type == 'Type A' or Elliptic_Type == 'Type S' or ((i < N-1) and (Elliptic_Type == 'Type B' or Elliptic_Type == 'Type C'))):
                # Drawing
                d.pop()
                d.push()
                d += elm.Line().up().length(2).linewidth(1)
                d += elm.Line().right().length(1.5).linewidth(1)
                Cseries_ = Kc * Cseries[i] / delta
                d += elm.Capacitor().right().label(getUnitsWithScale(Cseries_, 'Capacitance'), fontsize=_fontsize).linewidth(1)
                d += elm.Line().right().length(1.5).linewidth(1)
                d += elm.Line().down().length(2).linewidth(1)
                
                d.pop()
                d += elm.Line().up().length(2).linewidth(1)
                d += elm.Line().up().length(2).linewidth(1)
                d += elm.Line().right().length(1.5).linewidth(1)
                Lseries_ = Kl * delta / Cseries[i];
                d += elm.Inductor2(loops=2).right().label(getUnitsWithScale(Lseries_, 'Inductance'), fontsize=_fontsize).linewidth(1)
                d += elm.Line().right().length(1.5).linewidth(1)
                d += elm.Line().down().length(2).linewidth(1)
                d += elm.Line().down().length(2).linewidth(1)
                d += elm.Dot()
                
                # Network
                count_C += 1
                C.append(line.capacitor(Cseries_, name='C' + str(count_C)))
                count_L += 1
                L.append(line.inductor(Lseries_, name='L' + str(count_L)))
                          
            
            
            if ((i == N-1) and (Elliptic_Type == 'Type A' or Elliptic_Type == 'Type S')):
                d.push()
                
            # Make connections
            if (i < N): # The last connection must be done after the load port instantiation
                if (i == 0): # The first node must include the source port
                    connections.append([(Port1, 0), (C[0], 0), (L[0], 0), (C[2], 0), (L[1],0), (L[2],0)])
                    connections.append([(L[1], 1), (C[1], 0)])
                    connections.append([(C[0], 1), (ground[0], 0)])
                    connections.append([(L[0], 1), (ground[1], 0)])
                elif (i < N-1): # The other nodes must connect the current component with the ones from the last iteration
                    connections.append([(C[3*i-1], 1), (L[3*i-1], 1), (C[3*i-2], 1), (L[3*i], 0), (C[3*i], 0), (C[3*i + 2], 0), (L[3*i+2], 0), (L[3*i+1], 0)])
                    connections.append([(L[3*i+1], 1), (C[3*i+1], 0)])
                    connections.append([(C[3*i], 1), (ground[2*i], 0)])
                    connections.append([(L[3*i], 1), (ground[2*i+1], 0)])
                else:
                    if(Elliptic_Type == 'Type A' or Elliptic_Type == 'Type S'):# Types A and S have a resonator in the last position. In this sense, these lines are the same as above
                        connections.append([(C[3*i-1], 1), (L[3*i-1], 1), (C[3*i-2], 1), (L[3*i], 0), (C[3*i], 0), (C[3*i + 2], 0), (L[3*i+2], 0), (L[3*i+1], 0)])
                        connections.append([(L[3*i+1], 1), (C[3*i+1], 0)])
                        connections.append([(C[3*i], 1), (ground[2*i], 0)])
                        connections.append([(L[3*i], 1), (ground[2*i+1], 0)])
                    else:# Types B and C
                        connections.append([(C[3*i-1], 1), (L[3*i-1], 1), (C[3*i-2], 1), (L[3*i], 0), (C[3*i], 0), (L[3*i+1], 0)])
                        connections.append([(L[3*i+1], 1), (C[3*i+1], 0)])
                        connections.append([(C[3*i], 1), (ground[2*i], 0)])
                        connections.append([(L[3*i], 1), (ground[2*i+1], 0)])
            
        
        if (Elliptic_Type == 'Type A' or Elliptic_Type == 'Type S'):
            # Lower-branch shunt resonator
            # Drawing
            d.push()
            Cshunt_ = Kc * Cshunt[-1] / delta;
            d += elm.Line().down().length(1).linewidth(1)
            d += elm.Line().left().length(1).linewidth(1)
            d += elm.Line().down().length(1).linewidth(1)
            d += elm.Capacitor().down().label(getUnitsWithScale(Cshunt_, 'Capacitance'), fontsize=_fontsize).linewidth(1)
            d += elm.Ground().linewidth(1)
            
            d.pop()
            Lshunt_ = Kl * delta / Cshunt[-1];
            d += elm.Line().down().length(1).linewidth(1)
            d += elm.Line().right().length(1).linewidth(1)
            d += elm.Line().down().length(1).linewidth(1)
            d += elm.Inductor2(loops=2).down().label(getUnitsWithScale(Lshunt_, 'Inductance'), fontsize=_fontsize).linewidth(1)
            d += elm.Ground().linewidth(1)
            d.pop()
            
            # Network
            count_C += 1
            C.append(line.capacitor(Cshunt_, name='C' + str(count_C)))
            count_gnd += 1
            ground.append(rf.Circuit.Ground(frequency=freq, name='ground' + str(count_gnd), z0=RS))
            
            count_L += 1
            L.append(line.inductor(Lshunt_, name='L' + str(count_L)))
            count_gnd += 1
            ground.append(rf.Circuit.Ground(frequency=freq, name='ground' + str(count_gnd), z0=RS))
            
        # Load port
        # Drawing
        d += elm.Line().right().length(2).linewidth(1)
        d += elm.Dot().label('ZL = ' + str(float("{:.2f}".format(RL))) + " \u03A9", fontsize=_fontsize).linewidth(1)
        d += elm.Line(color='white').length(2).linewidth(0)
        
        # Network
        Port2 = rf.Circuit.Port(frequency=freq, name='port2', z0=RL)
        if (Elliptic_Type == 'Type A' or Elliptic_Type == 'Type S'):
            connections.append([(Port2, 0), (C[-1], 0), (C[-2], 1), (C[-3], 1), (L[-1] , 0), (L[-2], 1)])
            connections.append([(L[-1], 1), (ground[-2], 0)])
            connections.append([(C[-1], 1), (ground[-1], 0)])
        else:
            connections.append([(Port2, 0), (C[-1], 1)])

    # BANDPASS - FIRST SERIES
    if (FilterType == "Bandpass" and FirstShunt == 2):  
        # Filter components
        count_L = 0
        Kl = RS / (2 * np.pi * fc);
        Kc = 1 / (2 * np.pi * fc * RS);
        delta = bw / fc;
        for i in range(N):
            
            ## Upper-branch series resonator
            # Drawing
            Lseries_ = Kl * Cshunt[i] / delta
            d += elm.Inductor2(loops=2).right().label(getUnitsWithScale(Lseries_, 'Inductance'), fontsize=_fontsize).linewidth(1)
            
            Cseries_ = Kc * delta / Cshunt[i]
            d += elm.Capacitor().right().label(getUnitsWithScale(Cseries_, 'Capacitance'), fontsize=_fontsize).linewidth(1)
            
            # Network
            count_L += 1
            L.append(line.inductor(Lseries_, name='L' + str(count_L)))
            count_C += 1
            C.append(line.capacitor(Cseries_, name='C' + str(count_C)))
                     
            
            ## Lower-branch parallel resonator
            d.push() # Save the drawing point for later
            d += elm.Line().down().length(1).linewidth(1)
            d += elm.Line().left().length(1).linewidth(1)
            Cshunt_ = Kc * Lseries[i] / delta
            d += elm.Capacitor().down().label(getUnitsWithScale(Cshunt_, 'Capacitance'), fontsize=_fontsize).linewidth(1)
            d += elm.Line().right().length(1).linewidth(1)
            
            d.pop()
            d.push()
            d += elm.Line().down().length(1).linewidth(1)
            d += elm.Line().right().length(1).linewidth(1)
            Lshunt_ = Kl * delta / Lseries[i]
            d += elm.Inductor2(loops=2).down().label(getUnitsWithScale(Lshunt_, 'Inductance'), fontsize=_fontsize, loc='bottom').linewidth(1)
            d += elm.Line().left().length(1).linewidth(1)
            
            # Network
            count_C += 1
            C.append(line.capacitor(Cshunt_, name='C' + str(count_C)))
            
            count_L += 1
            L.append(line.inductor(Lshunt_, name='L' + str(count_L)))
            
            if (Elliptic_Type == 'Type A' or Elliptic_Type == 'Type S' or ((i < N-1) and (Elliptic_Type == 'Type B' or Elliptic_Type == 'Type C'))):
                ## Lower-branch series resonator
                # Drawing
                Lseries_ = Kl * Cseries[i] / delta;
                d += elm.Inductor2(loops=2).down().label(getUnitsWithScale(Lseries_, 'Inductance'), fontsize=_fontsize).linewidth(1)
                
                Cseries_ = Kc * delta / Cseries[i]
                d += elm.Capacitor().down().label(getUnitsWithScale(Cseries_, 'Capacitance'), fontsize=_fontsize).linewidth(1)
                
                d += elm.Ground().linewidth(1)

                # Network
                count_L += 1
                L.append(line.inductor(Lseries_, name='L' + str(count_L)))
                
                count_C += 1
                C.append(line.capacitor(Cseries_, name='C' + str(count_C)))
                
                count_gnd += 1
                ground.append(rf.Circuit.Ground(frequency=freq, name='ground' + str(count_gnd), z0=RS))
            else:
                d += elm.Ground().linewidth(1)
                count_gnd += 1
                ground.append(rf.Circuit.Ground(frequency=freq, name='ground' + str(count_gnd), z0=RS))
                count_gnd += 1
                ground.append(rf.Circuit.Ground(frequency=freq, name='ground' + str(count_gnd), z0=RS))
            
            d.pop()

            # Make connections
            if (i == 0): # The first node must include the source port
                connections.append([(Port1, 0), (L[0],0)])
                connections.append([(L[0],1), (C[0], 0)])
                
            elif (i < N): # The other nodes must connect the current component with the ones from the last iteration
                connections.append([(L[3*i], 1), (C[3*i], 0)])
                connections.append([(C[3*i-3], 1), (L[3*i-2], 0), (C[3*i-2], 0), (L[3*i], 0)])
                connections.append([(C[3*i-2], 1), (L[3*i-2], 1), (L[3*i-1], 0)])
                connections.append([(L[3*i-1], 1), (C[3*i-1], 0)])
                connections.append([(C[3*i-1], 1), (ground[i-1], 0)])
               
            
        if (Elliptic_Type == 'Type A' or Elliptic_Type == 'Type S'):
            # Last upper-branch series resonator
            # Drawing
            Lseries_ = Kl * Cshunt[-1] / delta
            d += elm.Inductor2(loops=2).right().label(getUnitsWithScale(Lseries_, 'Inductance'), fontsize=_fontsize).linewidth(1)
            
            Cseries_ = Kc * delta / Cshunt[-1]
            d += elm.Capacitor().right().label(getUnitsWithScale(Cseries_, 'Capacitance'), fontsize=_fontsize).linewidth(1)
            
            # Network
            count_L += 1
            L.append(line.inductor(Lseries_, name='L' + str(count_L)))
            count_C += 1
            C.append(line.capacitor(Cseries_, name='C' + str(count_C)))   

        if(Elliptic_Type == 'Type A' or Elliptic_Type == 'Type S'):# Types A and S have a resonator in the last position. In this sense, these lines are the same as above
            connections.append([(L[-1], 1), (C[-1], 0)])
            connections.append([(C[-4], 1), (L[-3], 0), (C[-3], 0), (L[-1], 0)])
            connections.append([(C[-3], 1), (L[-3], 1), (L[-2], 0)])
            connections.append([(L[-2], 1), (C[-2], 0)])
            connections.append([(C[-2], 1), (ground[-1], 0)])

        
        # Load port
          
        # Drawing
        d += elm.Line().right().length(2).linewidth(1)
        d += elm.Dot().label('ZL = ' + str(float("{:.2f}".format(RL))) + " \u03A9", fontsize=_fontsize).linewidth(1)
        d += elm.Line(color='white').length(2).linewidth(0)

        # Network
        Port2 = rf.Circuit.Port(frequency=freq, name='port2', z0=RL)
        if (Elliptic_Type == 'Type A' or Elliptic_Type == 'Type S'):
            connections.append([(Port2, 0), (C[-1] , 1)])
        else:
            connections.append([(L[-1], 0), (ground[-1], 0)])
            connections.append([(C[-1], 0), (ground[-2], 0)])
            connections.append([(Port2, 0), (C[-1] , 1), (L[-1], 1), (C[-2], 1)])
            

    # BANDSTOP - FIRST SHUNT
    if (FilterType == "Bandstop" and FirstShunt == 1):
        Kl = RS / (2 * np.pi * fc);
        Kc = 1 / (2 * np.pi * fc * RS);
        delta = bw / fc;
        # Filter components
        for i in range(N):
            
            ## Lower-branch series resonator
            # Drawing
            d.push() # Save the drawing point for later
      
            Lshunt_ =  Kl / (delta * Cshunt[i])
            d += elm.Inductor2(loops=2).down().label(getUnitsWithScale(Lshunt_, 'Inductance'), fontsize=_fontsize).linewidth(1)
            
            Cshunt_ = Kc * Cshunt[i] * delta
            d += elm.Capacitor().down().label(getUnitsWithScale(Cshunt_, 'Capacitance'), fontsize=_fontsize).linewidth(1)
            d += elm.Ground().linewidth(1)
            
            # Network
            count_L += 1
            L.append(line.inductor(Lshunt_, name='L' + str(count_L)))
            
            count_C += 1
            C.append(line.capacitor(Cshunt_, name='C' + str(count_C)))
            count_gnd += 1
            ground.append(rf.Circuit.Ground(frequency=freq, name='ground' + str(count_gnd), z0=RS))
            

            
            ## Upper-branch parallel resonator
            # Drawing
            d.pop()
            d.push()
            Lseries_ = Kl * Lseries[i] * delta
            d += elm.Line().right().length(1.5).linewidth(1)
            d += elm.Inductor2(loops=2).right().label(getUnitsWithScale(Lseries_, 'Inductance'), fontsize=_fontsize).linewidth(1)
            d += elm.Line().right().length(1.5).linewidth(1)
            
            d.pop()
            d.push()
            d += elm.Line().up().length(1).linewidth(1)
            d += elm.Line().right().length(1.5).linewidth(1)
            Cseries_ = Kc / (delta * Lseries[i])
            d += elm.Capacitor().right().label(getUnitsWithScale(Cseries_, 'Capacitance'), fontsize=_fontsize).linewidth(1)
            d += elm.Line().right().length(1.5).linewidth(1)
            d += elm.Line().down().length(1).linewidth(1)

            
            # Network
            count_L += 1
            L.append(line.inductor(Lseries_, name='L' + str(count_L)))
            count_C += 1
            C.append(line.capacitor(Cseries_, name='C' + str(count_C)))
                        
            ## Upper-branch series resonator
            if (Elliptic_Type == 'Type A' or Elliptic_Type == 'Type S' or ((i < N-1) and (Elliptic_Type == 'Type B' or Elliptic_Type == 'Type C'))):
                # Drawing
                d.pop()
                
                Cseries_ = Kc * delta * Cseries[i];
                Lseries_ = Kl / (Cseries[i] * delta);
                d += elm.Line().up().length(2).linewidth(1)
                d += elm.Capacitor().right().label(getUnitsWithScale(Cseries_, 'Capacitance'), fontsize=_fontsize).linewidth(1)
                d += elm.Inductor2(loops=2).right().label(getUnitsWithScale(Lseries_, 'Inductance'), fontsize=_fontsize).linewidth(1)
                d += elm.Line().down().length(2).linewidth(1)
                
                # Network
                count_C += 1
                C.append(line.capacitor(Cseries_, name='C' + str(count_C)))
                count_L += 1
                L.append(line.inductor(Lseries_, name='L' + str(count_L)))
                          
            
            
            if ((i == N-1) and (Elliptic_Type == 'Type A' or Elliptic_Type == 'Type S')):
                d.push()
                
            # Make connections
            if (i < N): # The last connection must be done after the load port instantiation
                if (i == 0): # The first node must include the source port
                    connections.append([(Port1, 0), (L[0], 0), (L[1], 0), (C[1], 0), (L[2], 0)])
                    connections.append([(L[2], 1), (C[2], 0)])
                    connections.append([(L[0], 1), (C[0], 0)])
                    connections.append([(C[0], 1), (ground[0], 0)])
                    
                elif (i < N-1): # The other nodes must connect the current component with the ones from the last iteration
                    connections.append([(C[3*i-1], 1), (C[3*i-2], 1), (L[3*i-2], 1), (L[3*i], 0), (L[3*i+1], 0), (C[3*i+1], 0), (L[3*i+2], 0)])
                    connections.append([(L[3*i+2], 1), (C[3*i+2], 0)])
                    connections.append([(L[3*i], 1), (C[3*i], 0)])
                    connections.append([(C[3*i], 1), (ground[i], 0)])
                else:
                    if(Elliptic_Type == 'Type A' or Elliptic_Type == 'Type S'):# Types A and S have a resonator in the last position.
                        connections.append([(C[3*i-1], 1), (C[3*i-2], 1), (L[3*i-2], 1), (L[3*i], 0), (L[3*i+1], 0), (C[3*i+1], 0), (L[3*i+2], 0)])
                        connections.append([(L[3*i+2], 1), (C[3*i+2], 0)])
                        connections.append([(L[3*i], 1), (C[3*i], 0)])
                        connections.append([(C[3*i], 1), (ground[i], 0)])
                    else:# Types B and C
                        connections.append([(C[3*i-1], 1), (C[3*i-2], 1), (L[3*i-2], 1), (L[3*i], 0), (L[3*i+1], 0), (C[3*i+1], 0)])
                        connections.append([(L[3*i], 1), (C[3*i], 0)])
                        connections.append([(C[3*i], 1), (ground[i], 0)])

        
        if (Elliptic_Type == 'Type A' or Elliptic_Type == 'Type S'):
            # Lower-branch shunt resonator
            # Drawing
            d.push()
            
            Lshunt_ =  Kl / (delta * Cshunt[-1]);
            d += elm.Inductor2(loops=2).down().label(getUnitsWithScale(Lshunt_, 'Inductance'), fontsize=_fontsize).linewidth(1)
            
            Cshunt_ = Kc * Cshunt[-1] * delta;
            d += elm.Capacitor().down().label(getUnitsWithScale(Cshunt_, 'Capacitance'), fontsize=_fontsize).linewidth(1)
            d += elm.Ground().linewidth(1)
            # Network
            count_C += 1
            C.append(line.capacitor(Cshunt_, name='C' + str(count_C)))
            count_gnd += 1
            ground.append(rf.Circuit.Ground(frequency=freq, name='ground' + str(count_gnd), z0=RS))
            
            count_L += 1
            L.append(line.inductor(Lshunt_, name='L' + str(count_L)))
            count_gnd += 1
            ground.append(rf.Circuit.Ground(frequency=freq, name='ground' + str(count_gnd), z0=RS))
            d.pop()
            
        # Load port
        # Drawing
        
        d += elm.Line().right().length(2).linewidth(1)
        d += elm.Dot().label('ZL = ' + str(float("{:.2f}".format(RL))) + " \u03A9", fontsize=_fontsize).linewidth(1)
        d += elm.Line(color='white').length(2).linewidth(0)
        
        # Network
        Port2 = rf.Circuit.Port(frequency=freq, name='port2', z0=RL)
        if (Elliptic_Type == 'Type A' or Elliptic_Type == 'Type S'):
            connections.append([(Port2, 0), (L[-1], 0), (C[-2], 1), (L[-3], 1), (C[-3], 1)])
            connections.append([(L[-1], 1), (C[-1], 0)])
            connections.append([(C[-1], 1), (ground[-1], 0)])
        else:
            connections.append([(Port2, 0), (C[-1], 1), (L[-1], 1)])

            
    # BANDSTOP - FIRST SERIES
    if (FilterType == "Bandstop" and FirstShunt == 2):
        Kl = RS / (2 * np.pi * fc);
        Kc = 1 / (2 * np.pi * fc * RS);
        delta = bw / fc;
        # Filter components
        for i in range(N):
            
            ## Upper-branch parallel resonator
            # Drawing
            d.push() # Save the drawing point for later
      
            Lshunt_ =  Kl * Cshunt[i] * delta
            d += elm.Line().right().length(1).linewidth(1)
            d += elm.Inductor2(loops=2).right().label(getUnitsWithScale(Lshunt_, 'Inductance'), fontsize=_fontsize).linewidth(1)
            d += elm.Line().right().length(1).linewidth(1)
            
            Cshunt_ = Kc / (delta * Cshunt[i]);
            d.pop()
            d += elm.Line().up().length(1).linewidth(1)
            d += elm.Line().right().length(1).linewidth(1)
            d += elm.Capacitor().right().label(getUnitsWithScale(Cshunt_, 'Capacitance'), fontsize=_fontsize).linewidth(1)
            d += elm.Line().right().length(1).linewidth(1)
            d += elm.Line().down().length(1).linewidth(1)
            
            # Network
            count_L += 1
            L.append(line.inductor(Lshunt_, name='L' + str(count_L)))
            
            count_C += 1
            C.append(line.capacitor(Cshunt_, name='C' + str(count_C)))        
            
            ## Lower-branch series resonator
            # Drawing
            d.push()
            d.push()
            Lseries_ = Kl / (delta * Lseries[i]);
            d += elm.Inductor2(loops=2).down().label(getUnitsWithScale(Lseries_, 'Inductance'), fontsize=_fontsize).linewidth(1)
            
            Cseries_ = Kc * Lseries[i] * delta
            d += elm.Capacitor().down().label(getUnitsWithScale(Cseries_, 'Capacitance'), fontsize=_fontsize).linewidth(1)
            
            # Network
            count_L += 1
            L.append(line.inductor(Lseries_, name='L' + str(count_L)))
            count_C += 1
            C.append(line.capacitor(Cseries_, name='C' + str(count_C)))
                        
            ## Lower-branch parallel resonator
            if (Elliptic_Type == 'Type A' or Elliptic_Type == 'Type S' or ((i < N-1) and (Elliptic_Type == 'Type B' or Elliptic_Type == 'Type C'))):
                # Drawing
                               
                Cseries_ = Kc / (Cseries[i] * delta);
                Lseries_ = Kl * delta * Cseries[i];
                d.push()
                d += elm.Line().left().length(1).linewidth(1)
                d += elm.Capacitor().down().label(getUnitsWithScale(Cseries_, 'Capacitance'), fontsize=_fontsize).linewidth(1)
                d += elm.Ground().linewidth(1)
                
                d.pop()
                d += elm.Line().right().length(1).linewidth(1)
                d += elm.Inductor2(loops=2).down().label(getUnitsWithScale(Lseries_, 'Inductance'), fontsize=_fontsize).linewidth(1)    
                d += elm.Ground().linewidth(1)
                d.pop()
                
                # Network
                count_C += 1
                C.append(line.capacitor(Cseries_, name='C' + str(count_C)))
                count_L += 1
                L.append(line.inductor(Lseries_, name='L' + str(count_L)))
                
                count_gnd += 1
                ground.append(rf.Circuit.Ground(frequency=freq, name='ground' + str(count_gnd), z0=RS))

                count_gnd += 1
                ground.append(rf.Circuit.Ground(frequency=freq, name='ground' + str(count_gnd), z0=RS))

                
            else:
                d += elm.Ground().linewidth(1)
                d.pop()
                
                count_gnd += 1
                ground.append(rf.Circuit.Ground(frequency=freq, name='ground' + str(count_gnd), z0=RS))
                          
            
            # Make connections
            if (i < N): # The last connection must be done after the load port instantiation
                if (i == 0): # The first node must include the source port
                    connections.append([(Port1, 0), (L[0], 0), (C[0], 0)])
                    
                elif (i < N-1): # The other nodes must connect the current component with the ones from the last iteration
                    connections.append([(C[3*i], 0), (L[3*i], 0), (C[3*i-3], 1), (L[3*i-3], 1), (C[3*i-2], 0)])
                    connections.append([(C[3*i-2], 1), (L[3*i-2], 0)])
                    connections.append([(L[3*i-2], 1), (C[3*i-1], 0), (L[3*i-1], 0)])
                    connections.append([(C[3*i-1], 1), (ground[2*i-2], 0)])
                    connections.append([(L[3*i-1], 1), (ground[2*i -1], 0)])
                else:
                    if(Elliptic_Type == 'Type A' or Elliptic_Type == 'Type S'):# Types A and S have a resonator in the last position.
                        connections.append([(C[3*i], 0), (L[3*i], 0), (C[3*i-3], 1), (L[3*i-3], 1), (C[3*i-2], 0)])
                        connections.append([(C[3*i-2], 1), (L[3*i-2], 0)])
                        connections.append([(L[3*i-2], 1), (C[3*i-1], 0), (L[3*i-1], 0)])
                        connections.append([(C[3*i-1], 1), (ground[2*i-2], 0)])
                        connections.append([(L[3*i-1], 1), (ground[2*i -1], 0)])
                    else:# Types B and C
                        connections.append([(C[3*i], 0), (L[3*i], 0), (C[3*i-3], 1), (L[3*i-3], 1), (C[3*i-2], 0)])
                        connections.append([(C[3*i-2], 1), (L[3*i-2], 0)])
                        connections.append([(L[3*i-2], 1), (C[3*i-1], 0), (L[3*i-1], 0)])
                        connections.append([(C[3*i-1], 1), (ground[2*i-2], 0)])
                        connections.append([(L[3*i-1], 1), (ground[2*i -1], 0)])
        
        if (Elliptic_Type == 'Type A' or Elliptic_Type == 'Type S'):
            # Upper-branch parallel resonator
            # Drawing
            
            d.pop()
            d.push()
            Lshunt_ =   Kl * Cshunt[-1] * delta
            d += elm.Inductor2(loops=2).right().label(getUnitsWithScale(Lshunt_, 'Inductance'), fontsize=_fontsize).linewidth(1)
            
            d.pop()
            d += elm.Line().up().length(1).linewidth(1)
            Cshunt_ = Kc / (delta * Cshunt[-1]);
            d += elm.Capacitor().right().label(getUnitsWithScale(Cshunt_, 'Capacitance'), fontsize=_fontsize).linewidth(1)
            d += elm.Line().down().length(1).linewidth(1)
            
            # Network
            count_C += 1
            C.append(line.capacitor(Cshunt_, name='C' + str(count_C)))
            count_gnd += 1
            ground.append(rf.Circuit.Ground(frequency=freq, name='ground' + str(count_gnd), z0=RS))
            
            count_L += 1
            L.append(line.inductor(Lshunt_, name='L' + str(count_L)))
            count_gnd += 1
            ground.append(rf.Circuit.Ground(frequency=freq, name='ground' + str(count_gnd), z0=RS))
            
        # Load port
        # Drawing
        
        d += elm.Line().right().length(2).linewidth(1)
        d += elm.Dot().label('ZL = ' + str(float("{:.2f}".format(RL))) + " \u03A9", fontsize=_fontsize).linewidth(1)
        d += elm.Line(color='white').length(2).linewidth(0)
        
        # Network
        Port2 = rf.Circuit.Port(frequency=freq, name='port2', z0=RL)
        if (Elliptic_Type == 'Type A' or Elliptic_Type == 'Type S'):
            connections.append([(Port2, 0), (L[-1], 1), (C[-1], 1)
                               ])
            connections.append([(L[-1], 0), (C[-1], 0), (C[-3], 0), (C[-4], 1), (L[-4], 1)])
            connections.append([(L[-3], 0), (C[-3], 1)])
            connections.append([(L[-3], 1), (C[-2], 0), (L[-2], 0)])
            connections.append([(C[-2], 1), (ground[-1], 0)])
            connections.append([(L[-2], 1), (ground[-2], 0)])
        else:
            connections.append([(Port2, 0), (C[-2], 1), (L[-2], 1), (L[-1], 0)])
            connections.append([(L[-1], 1), (C[-1], 0)])
            connections.append([(C[-1], 1), (ground[-1], 0)])
          
    return d, connections
    
# This function is used to rearrange the coefficients from the synthesis function.
def RearrangeTypeS(Lseries, Cseries, Cshunt):
    # Rearrange coefficients of the type-S filter

    N = len(Lseries)# Number of resonators

    N = N + 1
    idx1 = np.array(range(1, N+N%2, 2))

    idx2 = np.array(range(N-N%2, 0, -2))
    

    idx_Cshunt = np.ma.concatenate([idx1, idx2])-1
    if (N % 2 == 0):
        idx_Cseries = np.ma.concatenate([idx1, idx2[1:]])-1
    else:
        idx_Cseries = np.ma.concatenate([idx1[:-1], idx2[1-N%2:]])-1

    idx_Lseries = idx_Cseries
    Lseries = Lseries[idx_Lseries]
    Cseries = Cseries[idx_Cseries]
    Cshunt = Cshunt[idx_Cshunt]
    
    return Lseries, Cseries, Cshunt 
    

# [1] "Elliptic Approximation and Elliptic Filter Design on Small Computers", Pierre Amstutz, IEEE Transactions on Circuits and Systems, vol. CAS-25, No 12, December 1978

def EllipticTypeABC_Coefficients(a_s, a_p, M, RS, Elliptic_Type):
    
    dbn = 0.23025851; # dB -> Np conversion
    N = 2 * M;

    u = np.pi * np.pi / np.log(16 * (np.exp(a_s * dbn) - 1) / (np.exp(a_p * dbn) - 1));
    W =(u / (2 * np.pi)) * np.log((np.exp(a_p * dbn / 2) + 1) / (np.exp(a_p * dbn / 2) - 1));
    
    E = np.zeros(N)
    R = np.zeros(M)
    S = np.zeros(M)
    B = np.zeros(M+1)
    F = np.zeros(M+1)
    D = np.zeros(M+1)
    
    for j in range(0, N):
        E[j] = Sn(M * u, (j + 1 - M) * u / 2);

    K = 1;
    j = 1;
    delta = 1;
    
    while (delta > 1e-6):
        Kaux = K * (np.power(np.tan(W), 2) + np.power(np.tanh(j * M * u), 2)) / (1 + np.power(np.tan(W) * np.tanh(j * M * u), 2));
        delta = np.abs(K - Kaux);
        K = Kaux;
        j = j + 1;
    a0 = np.tan(W) * K;
    
    RS_ = np.empty(M, dtype=complex)
    
    # Calculation of the natural frequencies for the Type S
    for j in range(0, M):
        RS_[j] = 1j * Sn(M * u, 1j * W + (M + 1 - 2 * (j + 1)) * u / 2);
        
    for i in range(0, M):
        R[i] = np.real(RS_[i])
        S[i] = np.imag(RS_[i])

    if (Elliptic_Type == "Type A"):
        E8 = E[N - 1];
        IT = 1;
    else:
        IT = 2;
        E8 = -E[0];
        
    if (Elliptic_Type == "Type C"):
        E0 = -E[0]
    else:
        E0 = E[N - 1]
        
    # The normalized passband and stopband edges for a type S characteristic are given by Eq. 4.15
    FP = Sn(N * u, N * u / 2); # Normalized passband edge. It is estimated as: sqrt((E(N)+E0)/(1+E(N)*E8));
    
    # Calculation of the attenuation peaks
    for j in range(IT, M+1):
        D[j - 1] = (E[2 * j - 2] + E8) / (1 + E0 * E[2 * j - 2]);
    
    TQ = 0
    T0 = 0
    I = 1
    
    for i in range(0, M):
        if (D[i] == 0):
            F[i] = 1e4
        else:
            F[i] = np.sqrt(1 / D[i]);
        
    for j in range(0, M):
        W = (a0 * a0 + np.power(E[2 * j], 2)) / (1 + np.power(a0 * E[2 * j], 2));
        U = np.sqrt((E0 * E0 + 2 * E0 * S[j] + W) / (1 + 2 * E8 * S[j] + W * E8 * E8));
        V = ((1 + E0 * E8) * S[j] + E0 + E8 * W) /  (1 + 2 * E8 * S[j] + W * E8 * E8);
        R[j] = np.sqrt((U - V) / 2);
        S[j] = np.sqrt((U + V) / 2);
        I = -I;
        W = I * R[j] / S[j];
        TQ = (TQ + W) / (1 - TQ * W);
        if (Elliptic_Type == "Type A"):
            U = (F[1] - S[j]) / R[j];
            V = (F[1] + S[j]) / R[j];
            W = I * (V - U) / (1 + U * V);
            T0 = (T0 + W) / (1 - T0 * W);

        B[0] = B[0] + R[j];
        
    if (Elliptic_Type == "Type A"):
        T0 = T0 / (1 + np.sqrt(1 + T0 * T0));
        
    DB = np.zeros(M+1)
    TB = np.zeros(M+1)
    C = np.zeros(M+1)

    # Calculation of the derivative of the phase at F(K)
    for k in range(IT-1, M):
        DB[k] = 0;
        TB[k] = T0;
        I = 1;
        for j in range(0, M):
            DB[k] = DB[k] + 1 / (R[j] + np.power(F[k] - S[j], 2) / R[j]);
            DB[k] = DB[k] + 1 / (R[j] + np.power(F[k] + S[j], 2) / R[j]);
            I = -I;
            W = (F[k] - I * S[j]) / R[j];
            TB[k] = (TB[k] + W) / (1 - TB[k] * W);

    D[M] = D[M - 1];
    F[M] = F[M - 1];
    DB[M] = DB[M - 1];
    TB[M] = TB[M - 1];
    
    for j in range(0,M+1-IT, 2):
        TB[M - j - 1] = -1 / TB[M - j - 1];

    for j in range(IT-1, M+1):
        B[j] = (1 + pow(TB[j], 2)) * DB[j] / (4 * D[j]) - TB[j] * F[j] / 2;
        C[j] = TB[j] / F[j];
    RL = RS / W;

    # Permutations method Eq 3.6
    for l in range(0, 2):
        for k in range(l+2, M+1, 2):
            for j in range(l, k-1, 2):
                U = C[j] - C[k];
                V = 1 / (U / (B[j] * (D[k] - D[j])) - 1);
                C[k] = U * V;
                B[k] = (B[k] - B[j]) * V * V - B[j] * (V + V + 1);
    if (Elliptic_Type != "Type C"):
        W = np.power((1 - TQ * T0) / (TQ + T0), 2); # Types A and B have RL != RS
    else:
        W = 1;

    for j in range(0, M+1, 2):
        B[j] = B[j] * W;
        C[j] = C[j] * W;

    RL = RS / W; # Load resistance
    
    Cseries = np.zeros(M)
    Lseries = np.empty(M)
    Cshunt = np.zeros(M+1)
    
    if (Elliptic_Type != "Type A"):
        Lseries[0] = FP / B[0];
      
    V = 0
    for j in range(IT-1, M-1):
        V = V * C[j];
        # Calculation of the capacitor of the resonator
        w = F[j] / FP;
        L_ = FP / B[j];
        C_ = 1 / (w * w * L_);
        Cseries[j] = C_;
        Lseries[j] = FP / B[j];
        Cshunt[j] = FP * C[j];
        
        K = K - 2;
 

    w = F[M - 1] / FP;
    L_ = FP / B[M - 1];
    C_ = 1 / (w * w * L_);
    Cseries[M - 1] = C_;
    Lseries[M - 1] = FP / B[M - 1];
    Cshunt[M - 1] = FP * C[M - 1];
    Cshunt[M] = FP * C[M];
    
    return Lseries, Cseries, Cshunt, RL

# This function is used to rearrange the coefficients from the synthesis function.
def RearrangeTypesABC(Lseries, Cseries, Cshunt, Elliptic_Type):
    # Rearrange coefficients for filter types A, B, and C
    N = len(Lseries)
    idx1 = np.array(range(1, N+1, 2))
    idx2 = np.array(range(N-N%2, -1-N%2, -2))

    
    if (Elliptic_Type == "Type A"):
        if (N % 2 == 0):
            idx2[0] -= 1
        idx_Lseries = np.ma.concatenate([idx1[:-1], idx2])
        idx_Cseries = np.ma.concatenate([idx1[:-1], idx2])
        if (N % 2 == 0):
            idx2[0] += 1
        idx_Cshunt = np.ma.concatenate([idx1, idx2])
    else:
        if (N % 2 == 0):
            idx2[0] -= 1
            idx_Cseries = np.ma.concatenate([idx1[:-1], idx2])
            idx_Lseries = np.ma.concatenate([idx1[:-1], idx2])
            idx2[0] += 1
            idx_Cshunt = np.ma.concatenate([idx1, idx2])
        else:
            idx_Lseries = np.ma.concatenate([idx1[:-1], idx2])
            idx_Cshunt = np.ma.concatenate([idx1, idx2[:-1]])
            idx_Cseries = np.ma.concatenate([idx1[:-1], idx2[:-1]])

    Lseries = Lseries[idx_Lseries]
    Cseries = Cseries[idx_Cseries]
    Cshunt = Cshunt[idx_Cshunt]

    print(Cseries)
    
    return Lseries, Cseries, Cshunt

# This function exports the filter as a Qucs schematic. Depending on the filter type it delegates the task into another function.
def getEllipticFilterQucsSchematic(params):
    Mask = params['Mask']
    FirstElement = params['FirstElement']

    if (FirstElement == 1): # First shunt
        if (Mask == 'Lowpass'):
            QucsSchematic = getLowpassEllipticFirstShuntFilterQucsSchematic(params)
        elif(Mask == 'Highpass'):
            QucsSchematic = getHighpassEllipticFirstShuntFilterQucsSchematic(params)
        elif(Mask == 'Bandpass'):
            QucsSchematic = getBandpassEllipticFirstShuntFilterQucsSchematic(params)
    else: # First series
        if (Mask == 'Lowpass'):
            QucsSchematic = getLowpassEllipticFirstSeriesFilterQucsSchematic(params)
        elif(Mask == 'Highpass'):
            QucsSchematic = getHighpassEllipticFirstSeriesFilterQucsSchematic(params)
        elif(Mask == 'Bandpass'):
            QucsSchematic = getBandpassEllipticFirstSeriesFilterQucsSchematic(params)

    return QucsSchematic

# This function exports the first series elliptic LPF
def getLowpassEllipticFirstSeriesFilterQucsSchematic(params):
    # Unpack the dictionary
    Cshunt = params['Cshunt']
    Cseries = params['Cseries']
    Lseries = params['Lseries']
    Elliptic_Type = params['EllipticType']
    N =  params['N']
    RS = params['ZS']
    RL = params['ZL']
    fc = params['fc']*1e6
    Mask = params['Mask']
    Response = params['Response']

    count_L = 0
    count_C = 0

    # Set initial positions and text
    x = 60 # Current x-position in the schematic
    y = 150 # Current y-position in the schematic
    ys = 60

    # Position of the text in the lower branch components
    xtext_lower = 17
    ytext_lower = -26

    # Position of the text in the upper branch components
    xtext_upper = -35
    ytext_upper = -65
    
    schematic = "<Qucs Schematic 0.0.20>\n"

    # Size of the frame
    frame_DIN = 3
    if (((Mask == 'Bandpass') or (Mask == 'Bandstop')) and (N > 5)):
        frame_DIN = 5

    # Frame
    datasetName = "sample.dat"
    title = Response + " " + Mask + " Filter" + " - Order " + str(N)
    today = date.today()
    d = today.strftime("%B %d, %Y")
    schematic += ("<Properties>\n<View=0,-60,800,800,0.683014,0,0>\n<Grid=10,10,1>\n<DataSet=" 
                + datasetName
                + ">\n<DataDisplay=sample.dpl>\n<OpenDisplay=0>\n<Script=sample.m>\n<RunScript=0>\n<showFrame=" + str(frame_DIN) + ">\n"
                + "<FrameText0=" + title + ">\n<FrameText1=Drawn By: Andrés Martínez Mera>\n<FrameText2=Date: " 
                + d + ">\n<FrameText3=Revision:>\n</Properties>\n<Symbol>\n</Symbol>\n")

    components = "<Components>\n"
    wires = "<Wires>\n"

    # Source
    components += "<Pac P1 1 " + str(x) + " " + str(y + 150) + " " + str(xtext_lower) + " " + str(ytext_lower) + " 0 1 \"1\" 1 \"" + str(RS) + " Ohm\" 1 \"0 dBm\" 0 \"1 GHz\" 0>\n"
    components += "<GND *1 5 " + str(x) + " " + str(y + 180) + " 0 0 0 0>\n"

    # Wire to the mainline
    x1 = x; x2 = x; y1 = y+120; y2 = y
    wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

    step = 90

    for i in range(N):
            
        x += step
        ## Series inductor
        L = getUnitsWithScale(RS / (2 * np.pi * fc) * Cshunt[i], 'Inductance')
        count_L += 1
        components += "<L L" + str(count_L) + " 1 " + str(x) + " " + str(y) + " " + str(xtext_upper) + " " + str(ytext_upper) + " 0 0 \"" + L + "\" 1 \"\" 0 \"neutral\" 0>\n"
        
        # Wire to the previous component
        x1 = x-step; x2 = x-30; y1 = y; y2 = y
        wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

        x += step
        ## Shunt capacitor
        count_C += 1
        C = getUnitsWithScale(1 / (2 * np.pi * fc * RS) * Lseries[i], 'Capacitance')
        components += "<C C" + str(count_C) + " 1 " + str(x) + " " + str(y+60) + " " + str(xtext_lower) + " " + str(ytext_lower) + " 0 1 \"" + C + "\" 1 \"\" 0 \"neutral\" 0>\n"

        # Capacitor to mainline
        x1 = x; x2 = x; y1 = y+30; y2 = y
        wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

        # Node to the previous component
        x1 = x-step+30; x2 = x; y1 = y; y2 = y
        wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

        
        if (Elliptic_Type == 'Type A' or Elliptic_Type == 'Type S' or ((i < N-1) and (Elliptic_Type == 'Type B' or Elliptic_Type == 'Type C'))):
            ## Shunt inductor

            L = getUnitsWithScale(RS / (2 * np.pi * fc) * Cseries[i], 'Inductance')
            count_L += 1
            components += "<L L" + str(count_L) + " 1 " + str(x) + " " + str(y+150) + " " + str(xtext_lower) + " " + str(ytext_lower) + " 0 1 \"" + L + "\" 1 \"\" 0 \"neutral\" 0>\n"
            components += "<GND *1 5 " + str(x) + " " + str(y+180) + " 0 0 0 0>\n"

            # Wire to the capacitor
            x1 = x; x2 = x; y1 = y+120; y2 = y+90
            wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"
        else:
            x1 = x; x2 = x+step+30; y1 = y; y2 = y
            wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"
            components += "<GND *1 5 " + str(x) + " " + str(y+90) + " 0 0 0 0>\n"
            
    
    x += step
    if (Elliptic_Type == 'Type A' or Elliptic_Type == 'Type S'):          
        L = getUnitsWithScale(RS / (2 * np.pi * fc) * Cshunt[-1], 'Inductance')
        count_L += 1
        components += "<L L" + str(count_L) + " 1 " + str(x) + " " + str(y) + " " + str(xtext_upper) + " " + str(ytext_upper) + " 0 0 \"" + L + "\" 1 \"\" 0 \"neutral\" 0>\n"
        
        # Wire to the previous component
        x1 = x-step; x2 = x-30; y1 = y; y2 = y
        wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

    # Load port
    if ((Elliptic_Type != 'Type S') and (Elliptic_Type != 'Type C')):
        RL = round(RS*RS/RL, 2)
        
    x += step
    components += "<Pac P2 1 " + str(x) + " " + str(y + 150) + " " + str(xtext_lower) + " " + str(ytext_lower) + " 0 1 \"2\" 1 \"" + str(RL) + " Ohm\" 1 \"0 dBm\" 0 \"1 GHz\" 0>\n"
    components += "<GND *1 5 " + str(x) + " " + str(y + 180) + " 0 0 0 0>\n"

    # Wire to the mainline
    x1 = x; x2 = x; y1 = y+120; y2 = y
    wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

    # Node to the previous component
    x1 = x-step+30; x2 = x; y1 = y; y2 = y
    wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

    # Add title, diagrams, S-parameter block and equations
    comps, footer = getFooter(params, 400)
    components += comps # Add S-parameter simulation block

    # Close components block
    components += "</Components>\n"
    wires += "</Wires>\n"

    schematic += components
    schematic += wires
    schematic += footer

    return schematic

# This function exports the first series elliptic LPF
def getHighpassEllipticFirstSeriesFilterQucsSchematic(params):
    # Unpack the dictionary
    Cshunt = params['Cshunt']
    Cseries = params['Cseries']
    Lseries = params['Lseries']
    Elliptic_Type = params['EllipticType']
    N =  params['N']
    RS = params['ZS']
    RL = params['ZL']
    fc = params['fc']*1e6
    Mask = params['Mask']
    Response = params['Response']

    count_L = 0
    count_C = 0

    # Set initial positions and text
    x = 60 # Current x-position in the schematic
    y = 150 # Current y-position in the schematic
    ys = 60

    # Position of the text in the lower branch components
    xtext_lower = 17
    ytext_lower = -26

    # Position of the text in the upper branch components
    xtext_upper = -35
    ytext_upper = -65
    
    schematic = "<Qucs Schematic 0.0.20>\n"

    # Size of the frame
    frame_DIN = 3
    if (((Mask == 'Bandpass') or (Mask == 'Bandstop')) and (N > 5)):
        frame_DIN = 5

    # Frame
    datasetName = "sample.dat"
    title = Response + " " + Mask + " Filter" + " - Order " + str(N)
    today = date.today()
    d = today.strftime("%B %d, %Y")
    schematic += ("<Properties>\n<View=0,-60,800,800,0.683014,0,0>\n<Grid=10,10,1>\n<DataSet=" 
                + datasetName
                + ">\n<DataDisplay=sample.dpl>\n<OpenDisplay=0>\n<Script=sample.m>\n<RunScript=0>\n<showFrame=" + str(frame_DIN) + ">\n"
                + "<FrameText0=" + title + ">\n<FrameText1=Drawn By: Andrés Martínez Mera>\n<FrameText2=Date: " 
                + d + ">\n<FrameText3=Revision:>\n</Properties>\n<Symbol>\n</Symbol>\n")

    components = "<Components>\n"
    wires = "<Wires>\n"

    # Source
    components += "<Pac P1 1 " + str(x) + " " + str(y + 150) + " " + str(xtext_lower) + " " + str(ytext_lower) + " 0 1 \"1\" 1 \"" + str(RS) + " Ohm\" 1 \"0 dBm\" 0 \"1 GHz\" 0>\n"
    components += "<GND *1 5 " + str(x) + " " + str(y + 180) + " 0 0 0 0>\n"

    # Wire to the mainline
    x1 = x; x2 = x; y1 = y+120; y2 = y
    wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

    step = 90

    for i in range(N):
            
        x += step
        ## Series capacitor
        C = getUnitsWithScale(1 / (2 * np.pi * fc * RS * Cshunt[i]), 'Capacitance')
        count_C += 1
        components += "<C C" + str(count_C) + " 1 " + str(x) + " " + str(y) + " " + str(xtext_upper) + " " + str(ytext_upper) + " 0 0 \"" + C + "\" 1 \"\" 0 \"neutral\" 0>\n"
        
        # Wire to the previous component
        x1 = x-step; x2 = x-30; y1 = y; y2 = y
        wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

        x += step
        ## Shunt inductor
        count_L += 1
        L = getUnitsWithScale(RS / (2 * np.pi * fc * Lseries[i]), 'Inductance')
        components += "<L L" + str(count_L) + " 1 " + str(x) + " " + str(y+60) + " " + str(xtext_lower) + " " + str(ytext_lower) + " 0 1 \"" + L + "\" 1 \"\" 0 \"neutral\" 0>\n"

        # Capacitor to mainline
        x1 = x; x2 = x; y1 = y+30; y2 = y
        wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

        # Node to the previous component
        x1 = x-step+30; x2 = x; y1 = y; y2 = y
        wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

        
        if (Elliptic_Type == 'Type A' or Elliptic_Type == 'Type S' or ((i < N-1) and (Elliptic_Type == 'Type B' or Elliptic_Type == 'Type C'))):
            ## Shunt capacitor
            C = getUnitsWithScale(1 / (2 * np.pi * fc * RS * Cseries[i]), 'Capacitance')
            count_C += 1
            components += "<C C" + str(count_C) + " 1 " + str(x) + " " + str(y+150) + " " + str(xtext_lower) + " " + str(ytext_lower) + " 0 1 \"" + C + "\" 1 \"\" 0 \"neutral\" 0>\n"
            components += "<GND *1 5 " + str(x) + " " + str(y+180) + " 0 0 0 0>\n"

            # Wire to the capacitor
            x1 = x; x2 = x; y1 = y+120; y2 = y+90
            wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"
        else:
            x1 = x; x2 = x+step+30; y1 = y; y2 = y
            wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"
            components += "<GND *1 5 " + str(x) + " " + str(y+90) + " 0 0 0 0>\n"
            
    
    x += step
    if (Elliptic_Type == 'Type A' or Elliptic_Type == 'Type S'):          
        C = getUnitsWithScale(1 / (2 * np.pi * fc * RS * Cshunt[-1]), 'Capacitance')
        count_C += 1
        components += "<C C" + str(count_C) + " 1 " + str(x) + " " + str(y) + " " + str(xtext_upper) + " " + str(ytext_upper) + " 0 0 \"" + C + "\" 1 \"\" 0 \"neutral\" 0>\n"
        
        # Wire to the previous component
        x1 = x-step; x2 = x-30; y1 = y; y2 = y
        wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

    # Load port
    if ((Elliptic_Type != 'Type S') and (Elliptic_Type != 'Type C')):
        RL = round(RS*RS/RL, 2)
        
    x += step
    components += "<Pac P2 1 " + str(x) + " " + str(y + 150) + " " + str(xtext_lower) + " " + str(ytext_lower) + " 0 1 \"2\" 1 \"" + str(RL) + " Ohm\" 1 \"0 dBm\" 0 \"1 GHz\" 0>\n"
    components += "<GND *1 5 " + str(x) + " " + str(y + 180) + " 0 0 0 0>\n"

    # Wire to the mainline
    x1 = x; x2 = x; y1 = y+120; y2 = y
    wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

    # Node to the previous component
    x1 = x-step+30; x2 = x; y1 = y; y2 = y
    wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

    # Add title, diagrams, S-parameter block and equations
    comps, footer = getFooter(params, 400)
    components += comps # Add S-parameter simulation block

    # Close components block
    components += "</Components>\n"
    wires += "</Wires>\n"

    schematic += components
    schematic += wires
    schematic += footer

    return schematic


# This function exports the first shunt elliptic LPF
def getLowpassEllipticFirstShuntFilterQucsSchematic(params):
    # Unpack the dictionary
    Cshunt = params['Cshunt']
    Cseries = params['Cseries']
    Lseries = params['Lseries']
    Elliptic_Type = params['EllipticType']
    N =  params['N']
    RS = params['ZS']
    RL = params['ZL']
    fc = params['fc']*1e6
    Mask = params['Mask']
    Response = params['Response']

    count_L = 0
    count_C = 0

    # Set initial positions and text
    x = 60 # Current x-position in the schematic
    y = 150 # Current y-position in the schematic
    ys = 60

    # Position of the text in the lower branch components
    xtext_lower = 18
    ytext_lower = -25

    # Position of the text in the upper branch components
    xtext_upper = -30
    ytext_upper = 10
    
    schematic = "<Qucs Schematic 0.0.20>\n"

    # Size of the frame
    frame_DIN = 3
    if (N > 7):
        frame_DIN = 5

    # Frame
    datasetName = "sample.dat"
    title = Response + " " + Mask + " Filter" + " - Order " + str(N)
    today = date.today()
    d = today.strftime("%B %d, %Y")
    schematic += ("<Properties>\n<View=0,-60,800,800,0.683014,0,0>\n<Grid=10,10,1>\n<DataSet=" 
                + datasetName
                + ">\n<DataDisplay=sample.dpl>\n<OpenDisplay=0>\n<Script=sample.m>\n<RunScript=0>\n<showFrame=" + str(frame_DIN) + ">\n"
                + "<FrameText0=" + title + ">\n<FrameText1=Drawn By: Andrés Martínez Mera>\n<FrameText2=Date: " 
                + d + ">\n<FrameText3=Revision:>\n</Properties>\n<Symbol>\n</Symbol>\n")

    components = "<Components>\n"
    wires = "<Wires>\n"

    # Source
    components += "<Pac P1 1 " + str(x) + " " + str(y + 150) + " " + str(xtext_lower) + " " + str(ytext_lower) + " 0 1 \"1\" 1 \"" + str(RS) + " Ohm\" 1 \"0 dBm\" 0 \"1 GHz\" 0>\n"
    components += "<GND *1 5 " + str(x) + " " + str(y + 180) + " 0 0 0 0>\n"

    # Wire to the mainline
    x1 = x; x2 = x; y1 = y+120; y2 = y + 60
    wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

    # Wire to the mainline
    x1 = x; x2 = x+80; y1 = y+60; y2 = y + 60
    wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

    x += 50
    step = 90

    for i in range(N):
            
        x += step
        ## Shunt capacitor
        C = getUnitsWithScale(Cshunt[i] / (2 * np.pi * fc * RS), 'Capacitance')
        count_C += 1
        components += "<C C" + str(count_C) + " 1 " + str(x) + " " + str(y+150) + " " + str(xtext_lower) + " " + str(ytext_lower) + " 1 1 \"" + C + "\" 1 \"\" 0 \"neutral\" 0>\n"
        components += "<GND *1 5 " + str(x) + " " + str(y+180) + " 0 0 0 0>\n"


        # Shunt capacitor to node
        x1 = x; x2 = x; y1 = y+120; y2 = y + 60
        wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

        # Node to the previous series capacitor
        x1 = x-step+30; x2 = x; y1 = y + 60; y2 = y + 60
        wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

        # Node
        x1 = x; x2 = x; y1 = y+60; y2 = y
        wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

        if (i > 0):
            # Node to the previous series inductor
            x1 = x-step+30; x2 = x; y1 = y; y2 = y
            wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

        x += step
        ## Series inductor
        count_L += 1
        L = getUnitsWithScale(Lseries[i] * RS / (2 * np.pi * fc), 'Inductance')
        components += "<L L" + str(count_L) + " 1 " + str(x) + " " + str(y+60) + " " + str(xtext_upper) + " " + str(ytext_upper) + " 0 0 \"" + L + "\" 1 \"\" 0 \"neutral\" 0>\n"

        # Current inductor to node
        x1 = x-30; x2 = x-step; y1 = y + 60; y2 = y + 60
        wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

        
        if (Elliptic_Type == 'Type A' or Elliptic_Type == 'Type S' or ((i < N-1) and (Elliptic_Type == 'Type B' or Elliptic_Type == 'Type C'))):
            ## Series capacitor
            C = getUnitsWithScale(Cseries[i] / (2 * np.pi * fc * RS), 'Capacitance')
            count_C += 1
            components += "<C C" + str(count_C) + " 1 " + str(x) + " " + str(y) + " " + str(xtext_upper) + " " + str(ytext_upper-70) + " 0 0 \"" + C + "\" 1 \"\" 0 \"neutral\" 0>\n"

            # Current capacitor to node
            x1 = x-30; x2 = x-step; y1 = y; y2 = y
            wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"
        else:
            x1 = x+30; x2 = x+90; y1 = y+60; y2 = y+60
            wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

            
    
    x += step
    if (Elliptic_Type == 'Type A' or Elliptic_Type == 'Type S'):          
        C = getUnitsWithScale(Cshunt[-1]/ (2 * np.pi * fc * RS), 'Capacitance')
        count_C += 1
        components += "<C C" + str(count_C) + " 1 " + str(x) + " " + str(y+150) + " " + str(xtext_lower) + " " + str(ytext_lower) + " 1 1 \"" + C + "\" 1 \"\" 0 \"neutral\" 0>\n"
        components += "<GND *1 5 " + str(x) + " " + str(y+180) + " 0 0 0 0>\n"

        # Shunt capacitor to node
        x1 = x; x2 = x; y1 = y+120; y2 = y + 60
        wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

        # Node to the previous series capacitor
        x1 = x-step+30; x2 = x; y1 = y + 60; y2 = y + 60
        wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

        # Node
        x1 = x; x2 = x; y1 = y+60; y2 = y
        wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

        # Node to the previous series inductor
        x1 = x-step+30; x2 = x; y1 = y; y2 = y
        wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

    # Load port
    if ((Elliptic_Type != 'Type S') and (Elliptic_Type != 'Type C')):
        RL = round(RS*RS/RL, 2)
        
    x += (step + 60)
    components += "<Pac P2 1 " + str(x) + " " + str(y + 150) + " " + str(xtext_lower) + " " + str(ytext_lower) + " 0 1 \"2\" 1 \"" + str(RL) + " Ohm\" 1 \"0 dBm\" 0 \"1 GHz\" 0>\n"
    components += "<GND *1 5 " + str(x) + " " + str(y + 180) + " 0 0 0 0>\n"

    # Wire to the mainline
    x1 = x; x2 = x; y1 = y+120; y2 = y+60
    wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

    # Node to the previous component
    x1 = x-step-60; x2 = x; y1 = y+60; y2 = y+60
    wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

    # Add title, diagrams, S-parameter block and equations
    comps, footer = getFooter(params, 400)
    components += comps # Add S-parameter simulation block

    # Close components block
    components += "</Components>\n"
    wires += "</Wires>\n"

    schematic += components
    schematic += wires
    schematic += footer

    return schematic


# This function exports the first shunt elliptic LPF
def getHighpassEllipticFirstShuntFilterQucsSchematic(params):
    # Unpack the dictionary
    Cshunt = params['Cshunt']
    Cseries = params['Cseries']
    Lseries = params['Lseries']
    Elliptic_Type = params['EllipticType']
    N =  params['N']
    RS = params['ZS']
    RL = params['ZL']
    fc = params['fc']*1e6
    Mask = params['Mask']
    Response = params['Response']

    count_L = 0
    count_C = 0

    # Set initial positions and text
    x = 60 # Current x-position in the schematic
    y = 150 # Current y-position in the schematic
    ys = 60

    # Position of the text in the lower branch components
    xtext_lower = 18
    ytext_lower = -25

    # Position of the text in the upper branch components
    xtext_upper = -30
    ytext_upper = 10
    
    schematic = "<Qucs Schematic 0.0.20>\n"

    # Size of the frame
    frame_DIN = 3
    if (N > 7):
        frame_DIN = 5

    # Frame
    datasetName = "sample.dat"
    title = Response + " " + Mask + " Filter" + " - Order " + str(N)
    today = date.today()
    d = today.strftime("%B %d, %Y")
    schematic += ("<Properties>\n<View=0,-60,800,800,0.683014,0,0>\n<Grid=10,10,1>\n<DataSet=" 
                + datasetName
                + ">\n<DataDisplay=sample.dpl>\n<OpenDisplay=0>\n<Script=sample.m>\n<RunScript=0>\n<showFrame=" + str(frame_DIN) + ">\n"
                + "<FrameText0=" + title + ">\n<FrameText1=Drawn By: Andrés Martínez Mera>\n<FrameText2=Date: " 
                + d + ">\n<FrameText3=Revision:>\n</Properties>\n<Symbol>\n</Symbol>\n")

    components = "<Components>\n"
    wires = "<Wires>\n"

    # Source
    components += "<Pac P1 1 " + str(x) + " " + str(y + 150) + " " + str(xtext_lower) + " " + str(ytext_lower) + " 0 1 \"1\" 1 \"" + str(RS) + " Ohm\" 1 \"0 dBm\" 0 \"1 GHz\" 0>\n"
    components += "<GND *1 5 " + str(x) + " " + str(y + 180) + " 0 0 0 0>\n"

    # Wire to the mainline
    x1 = x; x2 = x; y1 = y+120; y2 = y + 60
    wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

    # Wire to the mainline
    x1 = x; x2 = x+80; y1 = y+60; y2 = y + 60
    wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

    x += 50
    step = 90

    for i in range(N):
        x += step
        ## Shunt inductor
        L = getUnitsWithScale(RS / (2 * np.pi * fc * Cshunt[i]), 'Inductance')
        count_L += 1
        components += "<L L" + str(count_L) + " 1 " + str(x) + " " + str(y+150) + " " + str(xtext_lower) + " " + str(ytext_lower) + " 1 1 \"" + L + "\" 1 \"\" 0 \"neutral\" 0>\n"
        components += "<GND *1 5 " + str(x) + " " + str(y+180) + " 0 0 0 0>\n"


        # Shunt capacitor to node
        x1 = x; x2 = x; y1 = y+120; y2 = y + 60
        wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

        # Node to the previous series capacitor
        x1 = x-step+30; x2 = x; y1 = y + 60; y2 = y + 60
        wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

        # Node
        x1 = x; x2 = x; y1 = y+60; y2 = y
        wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

        if (i > 0):
            # Node to the previous series inductor
            x1 = x-step+30; x2 = x; y1 = y; y2 = y
            wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

        x += step
        ## Series capacitor
        count_C += 1
        C = getUnitsWithScale(1 / (2 * np.pi * fc * RS * Lseries[i]), 'Capacitance')
        components += "<C C" + str(count_C) + " 1 " + str(x) + " " + str(y+60) + " " + str(xtext_upper) + " " + str(ytext_upper) + " 0 0 \"" + C + "\" 1 \"\" 0 \"neutral\" 0>\n"

        # Current inductor to node
        x1 = x-30; x2 = x-step; y1 = y + 60; y2 = y + 60
        wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

        
        if (Elliptic_Type == 'Type A' or Elliptic_Type == 'Type S' or ((i < N-1) and (Elliptic_Type == 'Type B' or Elliptic_Type == 'Type C'))):
            ## Series inductor
            L = getUnitsWithScale(RS / (2 * np.pi * fc * Cseries[i]), 'Inductance')
            count_L += 1
            components += "<L L" + str(count_L) + " 1 " + str(x) + " " + str(y) + " " + str(xtext_upper) + " " + str(ytext_upper-70) + " 0 0 \"" + L + "\" 1 \"\" 0 \"neutral\" 0>\n"

            # Current capacitor to node
            x1 = x-30; x2 = x-step; y1 = y; y2 = y
            wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

        else:
            x1 = x+30; x2 = x+90; y1 = y+60; y2 = y+60
            wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"
            
    
    x += step
    if (Elliptic_Type == 'Type A' or Elliptic_Type == 'Type S'):          
        L = getUnitsWithScale(RS / (2 * np.pi * fc * Cshunt[-1]), 'Inductance')
        count_L += 1
        components += "<L L" + str(count_L) + " 1 " + str(x) + " " + str(y+150) + " " + str(xtext_lower) + " " + str(ytext_lower) + " 1 1 \"" + L + "\" 1 \"\" 0 \"neutral\" 0>\n"
        components += "<GND *1 5 " + str(x) + " " + str(y+180) + " 0 0 0 0>\n"

        # Shunt capacitor to node
        x1 = x; x2 = x; y1 = y+120; y2 = y + 60
        wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

        # Node to the previous series capacitor
        x1 = x-step+30; x2 = x; y1 = y + 60; y2 = y + 60
        wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

        # Node
        x1 = x; x2 = x; y1 = y+60; y2 = y
        wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

        # Node to the previous series inductor
        x1 = x-step+30; x2 = x; y1 = y; y2 = y
        wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

    # Load port
    if ((Elliptic_Type != 'Type S') and (Elliptic_Type != 'Type C')):
        RL = round(RS*RS/RL, 2)
        
    x += (step + 60)
    components += "<Pac P2 1 " + str(x) + " " + str(y + 150) + " " + str(xtext_lower) + " " + str(ytext_lower) + " 0 1 \"2\" 1 \"" + str(RL) + " Ohm\" 1 \"0 dBm\" 0 \"1 GHz\" 0>\n"
    components += "<GND *1 5 " + str(x) + " " + str(y + 180) + " 0 0 0 0>\n"

    # Wire to the mainline
    x1 = x; x2 = x; y1 = y+120; y2 = y+60
    wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

    # Node to the previous component
    x1 = x-step-60; x2 = x; y1 = y+60; y2 = y+60
    wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

    # Add title, diagrams, S-parameter block and equations
    comps, footer = getFooter(params, 400)
    components += comps # Add S-parameter simulation block

    # Close components block
    components += "</Components>\n"
    wires += "</Wires>\n"

    schematic += components
    schematic += wires
    schematic += footer

    return schematic

# This function exports the first shunt elliptic LPF
def getBandpassEllipticFirstShuntFilterQucsSchematic(params):
    # Unpack the dictionary
    Cshunt = params['Cshunt']
    Cseries = params['Cseries']
    Lseries = params['Lseries']
    Elliptic_Type = params['EllipticType']
    N =  params['N']
    RS = params['ZS']
    RL = params['ZL']
    fc = params['fc']*1e6
    f1 = params['f1']*1e6
    f2 = params['f2']*1e6
    Mask = params['Mask']
    Response = params['Response']

    bw = f2 - f1

    count_L = 0
    count_C = 0

    # Set initial positions and text
    x = 60 # Current x-position in the schematic
    y = 200 # Current y-position in the schematic
    ys = 60

    # Position of the text in the lower branch components
    xtext_lower = 18
    ytext_lower = -25

    # Position of the text in the upper branch components
    xtext_upper = -30
    ytext_upper = 10
    
    schematic = "<Qucs Schematic 0.0.20>\n"

    # Size of the frame
    frame_DIN = 3
    if (N == 3):
        frame_DIN = 5
    elif(N > 3):
        frame_DIN = 0
 

    # Frame
    datasetName = "sample.dat"
    title = Response + " " + Mask + " Filter" + " - Order " + str(N)
    today = date.today()
    d = today.strftime("%B %d, %Y")
    schematic += ("<Properties>\n<View=0,-60,800,800,0.683014,0,0>\n<Grid=10,10,1>\n<DataSet=" 
                + datasetName
                + ">\n<DataDisplay=sample.dpl>\n<OpenDisplay=0>\n<Script=sample.m>\n<RunScript=0>\n<showFrame=" + str(frame_DIN) + ">\n"
                + "<FrameText0=" + title + ">\n<FrameText1=Drawn By: Andrés Martínez Mera>\n<FrameText2=Date: " 
                + d + ">\n<FrameText3=Revision:>\n</Properties>\n<Symbol>\n</Symbol>\n")

    components = "<Components>\n"
    wires = "<Wires>\n"

    # Source
    components += "<Pac P1 1 " + str(x) + " " + str(y + 150) + " " + str(xtext_lower) + " " + str(ytext_lower) + " 0 1 \"1\" 1 \"" + str(RS) + " Ohm\" 1 \"0 dBm\" 0 \"1 GHz\" 0>\n"
    components += "<GND *1 5 " + str(x) + " " + str(y + 180) + " 0 0 0 0>\n"

    # Wire to the mainline
    x1 = x; x2 = x; y1 = y+120; y2 = y + 60
    wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

    x1 = x; x2 = x+110; y1 = y+60; y2 = y + 60
    wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

    x += 50
    step = 140

    # Scaling
    Kl = RS / (2 * np.pi * fc);
    Kc = 1 / (RS  * 2 * np.pi * fc)
    delta = bw / fc;

    for i in range(N):
        x += step
        # Shunt parallel resonator
        L = getUnitsWithScale(Kl * delta / (Cshunt[i]), 'Inductance')
        count_L += 1
        components += "<L L" + str(count_L) + " 1 " + str(x-60) + " " + str(y+150) + " " + str(xtext_lower) + " " + str(ytext_lower) + " 1 1 \"" + L + "\" 1 \"\" 0 \"neutral\" 0>\n"
        components += "<GND *1 5 " + str(x-60) + " " + str(y+180) + " 0 0 0 0>\n"

        C = getUnitsWithScale(Cshunt[i] * Kc / delta, 'Capacitance')
        count_C += 1
        components += "<C C" + str(count_C) + " 1 " + str(x+60) + " " + str(y+150) + " " + str(xtext_lower) + " " + str(ytext_lower) + " 1 1 \"" + C + "\" 1 \"\" 0 \"neutral\" 0>\n"
        components += "<GND *1 5 " + str(x+60) + " " + str(y+180) + " 0 0 0 0>\n"

        # Shunt inductor to node
        x1 = x - 60; x2 = x - 60; y1 = y + 120; y2 = y + 100
        wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

        # Shunt capacitor to node
        x1 = x + 60; x2 = x + 60; y1 = y + 120; y2 = y + 100
        wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

        # Wire between capacitor and inductor
        x1 = x - 60; x2 = x; y1 = y + 100; y2 = y + 100
        wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"
        x1 = x; x2 = x + 60; y1 = y + 100; y2 = y + 100
        wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

        # Wire to the node
        x1 = x; x2 = x; y1 = y + 100; y2 = y + 60
        wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

        # Wire to the previous section
        x1 = x - 80; x2 = x; y1 = y+60; y2 = y+60
        wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

        x += step
        ## Upper branch series resonator
        count_L += 1
        L = getUnitsWithScale(Kl * Lseries[i] / delta, 'Inductance')
        components += "<L L" + str(count_L) + " 1 " + str(x) + " " + str(y+60) + " " + str(xtext_upper) + " " + str(ytext_upper) + " 0 0 \"" + L + "\" 1 \"\" 0 \"neutral\" 0>\n"

        x += step
        count_C += 1
        C = getUnitsWithScale(Kc * delta / Lseries[i], 'Capacitance')
        components += "<C C" + str(count_C) + " 1 " + str(x) + " " + str(y+60) + " " + str(xtext_upper) + " " + str(ytext_upper) + " 0 0 \"" + C + "\" 1 \"\" 0 \"neutral\" 0>\n"

        # Wire between capacitor and inductor
        x1 = x-step+30; x2 = x-30; y1 = y + 60; y2 = y + 60
        wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

        # Wire from the series inductor to the node
        x1 = x-step-30; x2 = x-step-60; y1 = y + 60; y2 = y + 60
        wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"
        x1 = x-step-60; x2 = x-2*step; y1 = y + 60; y2 = y + 60
        wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

        # Wire from the series capacitor to the next node
        x1 = x+30; x2 = x+60; y1 = y + 60; y2 = y + 60
        wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

        
        if (Elliptic_Type == 'Type A' or Elliptic_Type == 'Type S' or ((i < N-1) and (Elliptic_Type == 'Type B' or Elliptic_Type == 'Type C'))):
            # Upper-branch parallel resonator
            offset = round(0.5*step)
            L = getUnitsWithScale(Kl * delta / Cseries[i], 'Inductance')
            count_L += 1
            components += "<L L" + str(count_L) + " 1 " + str(x-offset) + " " + str(y+20) + " " + str(xtext_upper) + " " + str(ytext_upper-70) + " 0 0 \"" + L + "\" 1 \"\" 0 \"neutral\" 0>\n"

            C = getUnitsWithScale(Kc * Cseries[i] / delta, 'Capacitance')
            count_C += 1
            components += "<C C" + str(count_C) + " 1 " + str(x-offset) + " " + str(y-60) + " " + str(xtext_upper) + " " + str(ytext_upper-70) + " 0 0 \"" + C + "\" 1 \"\" 0 \"neutral\" 0>\n"

            # Wire from the parallel inductor to the previous node
            x1 = x-offset-30; x2 = x-step-60; y1 = y + 20; y2 = y + 20
            wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"
            x1 = x-step-60; x2 = x-step-60; y1 = y + 60; y2 = y + 20
            wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

            # Wire from the parallel capacitor to the previous node
            x1 = x-offset-30; x2 = x-step-60; y1 = y - 60; y2 = y - 60
            wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"
            x1 = x-step-60; x2 = x-step-60; y1 = y - 60; y2 = y + 20
            wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

            # Wire from the parallel inductor to the next node
            x1 = x-offset+30; x2 = x+60; y1 = y + 20; y2 = y + 20
            wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"
            x1 = x+60; x2 = x+60; y1 = y + 60; y2 = y + 20
            wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

            # Wire from the parallel capacitor to the next node
            x1 = x-offset+30; x2 = x+60; y1 = y - 60; y2 = y - 60
            wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"
            x1 = x+60; x2 = x+60; y1 = y - 60; y2 = y + 20
            wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

        else:
            # Wire from the parallel capacitor to the next node
            x1 = x+60; x2 = x+step; y1 = y + 60; y2 = y + 60
            wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

            
    
    
    if (Elliptic_Type == 'Type A' or Elliptic_Type == 'Type S'):
        x += step        
        # Lower-branch parallel resonator
        L = getUnitsWithScale(Kl * delta / (Cshunt[-1]), 'Inductance')
        count_L += 1
        components += "<L L" + str(count_L) + " 1 " + str(x-60) + " " + str(y+150) + " " + str(xtext_lower) + " " + str(ytext_lower) + " 1 1 \"" + L + "\" 1 \"\" 0 \"neutral\" 0>\n"
        components += "<GND *1 5 " + str(x-60) + " " + str(y+180) + " 0 0 0 0>\n"

        C = getUnitsWithScale(Cshunt[-1] * Kc / delta, 'Capacitance')
        count_C += 1
        components += "<C C" + str(count_C) + " 1 " + str(x+60) + " " + str(y+150) + " " + str(xtext_lower) + " " + str(ytext_lower) + " 1 1 \"" + C + "\" 1 \"\" 0 \"neutral\" 0>\n"
        components += "<GND *1 5 " + str(x+60) + " " + str(y+180) + " 0 0 0 0>\n"

        # Shunt inductor to node
        x1 = x - 60; x2 = x - 60; y1 = y + 120; y2 = y + 100
        wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

        # Shunt capacitor to node
        x1 = x + 60; x2 = x + 60; y1 = y + 120; y2 = y + 100
        wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

        # Wire between capacitor and inductor
        x1 = x - 60; x2 = x; y1 = y + 100; y2 = y + 100
        wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"
        x1 = x; x2 = x + 60; y1 = y + 100; y2 = y + 100
        wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

        # Wire to the node
        x1 = x; x2 = x; y1 = y + 100; y2 = y + 60
        wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

        # Wire to the previous section
        x1 = x - 80; x2 = x; y1 = y+60; y2 = y+60
        wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

        x1 = x; x2 = x+step; y1 = y+60; y2 = y + 60
        wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

    # Load port
    if ((Elliptic_Type != 'Type S') and (Elliptic_Type != 'Type C')):
        RL = round(RS*RS/RL, 2)
        
    x += (step + 60)
    components += "<Pac P2 1 " + str(x) + " " + str(y + 150) + " " + str(xtext_lower) + " " + str(ytext_lower) + " 0 1 \"2\" 1 \"" + str(RL) + " Ohm\" 1 \"0 dBm\" 0 \"1 GHz\" 0>\n"
    components += "<GND *1 5 " + str(x) + " " + str(y + 180) + " 0 0 0 0>\n"

    # Wire to the mainline
    x1 = x; x2 = x; y1 = y+120; y2 = y + 60
    wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

    x1 = x-60; x2 = x; y1 = y+60; y2 = y + 60
    wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

    # Add title, diagrams, S-parameter block and equations
    comps, footer = getFooter(params, 420)
    components += comps # Add S-parameter simulation block

    # Close components block
    components += "</Components>\n"
    wires += "</Wires>\n"

    schematic += components
    schematic += wires
    schematic += footer

    return schematic

def getBandpassEllipticFirstSeriesFilterQucsSchematic(params):
    # Unpack the dictionary
    Cshunt = params['Cshunt']
    Cseries = params['Cseries']
    Lseries = params['Lseries']
    Elliptic_Type = params['EllipticType']
    N =  params['N']
    RS = params['ZS']
    RL = params['ZL']
    fc = params['fc']*1e6
    f1 = params['f1']*1e6
    f2 = params['f2']*1e6
    Mask = params['Mask']
    Response = params['Response']

    bw = f2 - f1

    count_L = 0
    count_C = 0

    # Set initial positions and text
    x = 60 # Current x-position in the schematic
    y = 170 # Current y-position in the schematic
    ys = 60

    # Position of the text in the lower branch components
    xtext_lower = 18
    ytext_lower = -25

    # Position of the text in the upper branch components
    xtext_upper = -37
    ytext_upper = -65
    
    schematic = "<Qucs Schematic 0.0.20>\n"

    # Size of the frame
    frame_DIN = 3
    if (N == 3):
        frame_DIN = 5
    elif(N > 3):
        frame_DIN = 0
 

    # Frame
    datasetName = "sample.dat"
    title = Response + " " + Mask + " Filter" + " - Order " + str(N)
    today = date.today()
    d = today.strftime("%B %d, %Y")
    schematic += ("<Properties>\n<View=0,-60,800,800,0.683014,0,0>\n<Grid=10,10,1>\n<DataSet=" 
                + datasetName
                + ">\n<DataDisplay=sample.dpl>\n<OpenDisplay=0>\n<Script=sample.m>\n<RunScript=0>\n<showFrame=" + str(frame_DIN) + ">\n"
                + "<FrameText0=" + title + ">\n<FrameText1=Drawn By: Andrés Martínez Mera>\n<FrameText2=Date: " 
                + d + ">\n<FrameText3=Revision:>\n</Properties>\n<Symbol>\n</Symbol>\n")

    components = "<Components>\n"
    wires = "<Wires>\n"

    x += 50
    step = 180

    # Scaling
    Kl = RS / (2 * np.pi * fc);
    Kc = 1 / (RS  * 2 * np.pi * fc)
    delta = bw / fc;

    # Source
    components += "<Pac P1 1 " + str(x) + " " + str(y + 150) + " " + str(xtext_lower) + " " + str(ytext_lower) + " 0 1 \"1\" 1 \"" + str(RS) + " Ohm\" 1 \"0 dBm\" 0 \"1 GHz\" 0>\n"
    components += "<GND *1 5 " + str(x) + " " + str(y + 180) + " 0 0 0 0>\n"

    # Wire to the mainline
    x1 = x; x2 = x; y1 = y+120; y2 = y
    wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

    x1 = x; x2 = x+step-90; y1 = y; y2 = y 
    wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

    for i in range(N):
        x += step
        
        # Upper-brach series resonator
        L = getUnitsWithScale(Kl * Cshunt[i] / delta, 'Inductance')
        count_L += 1
        components += "<L L" + str(count_L) + " 1 " + str(x-60) + " " + str(y) + " " + str(xtext_upper) + " " + str(ytext_upper) + " 0 0 \"" + L + "\" 1 \"\" 0 \"neutral\" 0>\n"

        C = getUnitsWithScale(Kc * delta / Cshunt[i], 'Capacitance')
        count_C += 1
        components += "<C C" + str(count_C) + " 1 " + str(x+60) + " " + str(y) + " " + str(xtext_upper) + " " + str(ytext_upper) + " 0 0 \"" + C + "\" 1 \"\" 0 \"neutral\" 0>\n"
    
        # Wire between inductor and capacitor
        x1 = x-30; x2 = x+30; y1 = y; y2 = y
        wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

        # Wire to the node
        x1 = x+90; x2 = x+step; y1 = y; y2 = y
        wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

        # Wire to the next section
        x1 = x+step; x2 = x+step+90; y1 = y; y2 = y
        wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

        x += step
        # Lower-branch parallel resonator
        L = getUnitsWithScale(Kl * delta / Lseries[i], 'Inductance')
        count_L += 1
        components += "<L L" + str(count_L) + " 1 " + str(x-60) + " " + str(y+80) + " " + str(xtext_lower) + " " + str(ytext_lower) + " 1 1 \"" + L + "\" 1 \"\" 0 \"neutral\" 0>\n"

        C = getUnitsWithScale(Kc * Lseries[i] / delta, 'Capacitance')
        count_C += 1
        components += "<C C" + str(count_C) + " 1 " + str(x+60) + " " + str(y+80) + " " + str(xtext_lower) + " " + str(ytext_lower) + " 1 1 \"" + C + "\" 1 \"\" 0 \"neutral\" 0>\n"

        # Wires between the parallel resonator
        x1 = x-60; x2 = x-60; y1 = y+50; y2 = y+30
        wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"
        x1 = x+60; x2 = x+60; y1 = y+50; y2 = y+30
        wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"
        x1 = x-60; x2 = x; y1 = y+30; y2 = y+30
        wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"
        x1 = x+60; x2 = x; y1 = y+30; y2 = y+30
        wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"
        x1 = x; x2 = x; y1 = y+30; y2 = y
        wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

        if (Elliptic_Type == 'Type A' or Elliptic_Type == 'Type S' or ((i < N-1) and (Elliptic_Type == 'Type B' or Elliptic_Type == 'Type C'))):

            # Wires to the series resonator
            x1 = x-60; x2 = x-60; y1 = y+110; y2 = y+130
            wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"
            x1 = x+60; x2 = x+60; y1 = y+110; y2 = y+130
            wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"
            x1 = x-60; x2 = x; y1 = y+130; y2 = y+130
            wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"
            x1 = x+60; x2 = x; y1 = y+130; y2 = y+130
            wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"
            x1 = x; x2 = x; y1 = y+130; y2 = y+160
            wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"


            # Lower-branch series resonator
            L = getUnitsWithScale(Kl * Cseries[i] / delta, 'Inductance')
            count_L += 1
            components += "<L L" + str(count_L) + " 1 " + str(x) + " " + str(y+190) + " " + str(xtext_lower) + " " + str(ytext_lower) + " 1 1 \"" + L + "\" 1 \"\" 0 \"neutral\" 0>\n"

            C = getUnitsWithScale(Kc * delta / Cseries[i], 'Capacitance')
            count_C += 1
            components += "<C C" + str(count_C) + " 1 " + str(x) + " " + str(y+270) + " " + str(xtext_lower) + " " + str(ytext_lower) + " 1 1 \"" + C + "\" 1 \"\" 0 \"neutral\" 0>\n"
            components += "<GND *1 5 " + str(x) + " " + str(y + 300) + " 0 0 0 0>\n"

            # Wires between capacitor and inductor
            x1 = x; x2 = x; y1 = y+220; y2 = y+240
            wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"
        else:
            components += "<GND *1 5 " + str(x-60) + " " + str(y + 110) + " 0 0 0 0>\n"
            components += "<GND *1 5 " + str(x+60) + " " + str(y + 110) + " 0 0 0 0>\n"

    if (Elliptic_Type == 'Type A' or Elliptic_Type == 'Type S'):
        x += step
        # Last upper-branch series resonator
        L = getUnitsWithScale(Kl * Cshunt[-1] / delta, 'Inductance')
        count_L += 1
        components += "<L L" + str(count_L) + " 1 " + str(x-60) + " " + str(y) + " " + str(xtext_upper) + " " + str(ytext_upper) + " 0 0 \"" + L + "\" 1 \"\" 0 \"neutral\" 0>\n"

        C = getUnitsWithScale(Kc * delta / Cshunt[-1], 'Capacitance')
        count_C += 1
        components += "<C C" + str(count_C) + " 1 " + str(x+60) + " " + str(y) + " " + str(xtext_upper) + " " + str(ytext_upper) + " 0 0 \"" + C + "\" 1 \"\" 0 \"neutral\" 0>\n"
    
        # Wire between inductor and capacitor
        x1 = x-30; x2 = x+30; y1 = y; y2 = y
        wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

    # Source
    x += step
    components += "<Pac P2 1 " + str(x) + " " + str(y + 150) + " " + str(xtext_lower) + " " + str(ytext_lower) + " 0 1 \"2\" 1 \"" + str(RL) + " Ohm\" 1 \"0 dBm\" 0 \"1 GHz\" 0>\n"
    components += "<GND *1 5 " + str(x) + " " + str(y + 180) + " 0 0 0 0>\n"

    # Wires to the mainline
    x1 = x; x2 = x; y1 = y+120; y2 = y
    wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"

    x1 = x; x2 = x-step+90; y1 = y; y2 = y 
    wires += "<" + str(x1) + " " + str(y1) + " " + str(x2) +  " " + str(y2) +  " \"\" 0 0 0 \"\">\n"


    # Add title, diagrams, S-parameter block and equations
    comps, footer = getFooter(params, 420)
    components += comps # Add S-parameter simulation block

    # Close components block
    components += "</Components>\n"
    wires += "</Wires>\n"

    schematic += components
    schematic += wires
    schematic += footer

    return schematic

# Returns a footer for the schematics containing the title, the simulation block, the equations and the diagrams
def getFooter(params, y_offset):
    f_start = params['f_start']
    f_stop = params['f_stop']
    n_points = params['n_points']
    Response = params['Response']
    N = params['N']
    ZS = params['ZS']
    Mask = params['Mask']
    Ripple = params['Ripple']
    fc = params['fc']

    # S-parameter simulation block
    x_block = 60
    y_block = y_offset
    components = ''
    components += "<.SP SP1 1 " + str(x_block) + " " + str(y_block) + " 0 67 0 0 \"lin\" 1 \"" + str(f_start) + " MHz \" 1 \"" + str(f_stop) + " MHz \" 1 \"" + str(n_points) + "\" 1 \"no\" 0 \"1\" 0 \"2\" 0>\n"
    components += "<Eqn Eqn1 1 " + str(1230) + " " + str(600) + " -28 15 0 0 \"S21_dB=dB(S[2,1])\" 1 \"S11_dB=dB(S[1,1])\" 1 \"S22_dB=dB(S[2,2])\" 1 \"yes\" 0>\n"
    components += "<Eqn Eqn2 1 " + str(1230) + " " + str(780) + " -28 15 0 0 \"gd=groupdelay(S,2,1)\" 1 \"phase=(180/pi)*angle(S[2,1])\" 1 \"yes\" 0>\n"

    # Text
    y_title = str(50)
    paintings = "<Paintings>\n"
    today = date.today()
    copyright = " - Copyright \u00A9 2020-" + str(today.year) + " Andrés Martínez Mera - GNU Public License Version 3"

    paintings += ("<Text 50" + " " + y_title + " 15 #000000 0 \"" 
                    + Response + " " + Mask + " Filter" + ", Order: " + str(N) + ", Ripple: " + str(Ripple) + " dB, "
                    + str(fc) + " MHz, Z_0 = " + str(ZS) + " Ohm" + copyright + "\">\n")

    
    # Diagrams
    x_size = 400
    y_size = 300
    x_pos = 170
    y_pos = y_offset + 500
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

    footer = diagrams + paintings

    return components, footer