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
    d = schem.Drawing()
    _fontsize = 12
    
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
    
    posx = 0 # This index is used to draw the circuit
    
    # Source port
    # Drawing: Source port and the first line
    d += elm.Dot().label('ZS = ' + str(RS) + " Ohm", fontsize=_fontsize).linewidth(1)
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
            d += elm.Inductor().right().label(getUnitsWithScale(Lseries_, 'Inductance'), fontsize=_fontsize).linewidth(1)
            
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
        d += elm.Dot().label('ZL = ' + str(float("{:.2f}".format(RL))) + " Ohm", fontsize=_fontsize).linewidth(1)
        
        # Network
        Port2 = rf.Circuit.Port(frequency=freq, name='port2', z0=RL)
        if (Elliptic_Type == 'Type A' or Elliptic_Type == 'Type S'):
            connections.append([(Port2, 0), (C[-2], 1), (C[-1], 0), (L[-1] , 1)])
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
            d += elm.Inductor().right().label(getUnitsWithScale(Lseries_, 'Inductance'), fontsize=_fontsize).linewidth(1)
            
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
                d += elm.Inductor().down().label(getUnitsWithScale(Lshunt_, 'Inductance'), fontsize=_fontsize).linewidth(1)
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
            d += elm.Inductor().right().label(getUnitsWithScale(Lseries_, 'Inductance'), fontsize=_fontsize).linewidth(1)

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
        d += elm.Dot().label('ZL = ' + str(float("{:.2f}".format(RL))) + " Ohm", fontsize=_fontsize).linewidth(1)

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
            d += elm.Inductor().down().label(getUnitsWithScale(Lshunt_, 'Inductance'), fontsize=_fontsize).linewidth(1)
            
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
        d += elm.Dot().label('ZL = ' + str(float("{:.2f}".format(RL))) + " Ohm", fontsize=_fontsize).linewidth(1)

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
            d += elm.Inductor().down().label(getUnitsWithScale(Lshunt_, 'Inductance'), fontsize=_fontsize).linewidth(1)
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
                d += elm.Inductor().right().label(getUnitsWithScale(Lseries_, 'Inductance'), fontsize=_fontsize).linewidth(1)
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
            d += elm.Inductor().down().label(getUnitsWithScale(Lshunt_, 'Inductance'), fontsize=_fontsize).linewidth(1)
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
        d += elm.Dot().label('ZL = ' + str(float("{:.2f}".format(RL))) + " Ohm", fontsize=_fontsize).linewidth(1)
        
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
            d += elm.Inductor().down().label(getUnitsWithScale(Lshunt_, 'Inductance'), fontsize=_fontsize).linewidth(1)
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
            d += elm.Inductor().right().label(getUnitsWithScale(Lseries_, 'Inductance'), fontsize=_fontsize).linewidth(1)
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
                d += elm.Inductor().right().label(getUnitsWithScale(Lseries_, 'Inductance'), fontsize=_fontsize).linewidth(1)
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
            d += elm.Inductor().down().label(getUnitsWithScale(Lshunt_, 'Inductance'), fontsize=_fontsize).linewidth(1)
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
        d += elm.Dot().label('ZL = ' + str(float("{:.2f}".format(RL))) + " Ohm", fontsize=_fontsize).linewidth(1)
        
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
            d += elm.Inductor().right().label(getUnitsWithScale(Lseries_, 'Inductance'), fontsize=_fontsize).linewidth(1)
            
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
            d += elm.Inductor().down().label(getUnitsWithScale(Lshunt_, 'Inductance'), fontsize=_fontsize, loc='bottom').linewidth(1)
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
                d += elm.Inductor().down().label(getUnitsWithScale(Lseries_, 'Inductance'), fontsize=_fontsize).linewidth(1)
                
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
            d += elm.Inductor().right().label(getUnitsWithScale(Lseries_, 'Inductance'), fontsize=_fontsize).linewidth(1)
            
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
        d += elm.Dot().label('ZL = ' + str(float("{:.2f}".format(RL))) + " Ohm", fontsize=_fontsize).linewidth(1)

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
            d += elm.Inductor().down().label(getUnitsWithScale(Lshunt_, 'Inductance'), fontsize=_fontsize).linewidth(1)
            
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
            d += elm.Inductor().right().label(getUnitsWithScale(Lseries_, 'Inductance'), fontsize=_fontsize).linewidth(1)
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
                d += elm.Inductor().right().label(getUnitsWithScale(Lseries_, 'Inductance'), fontsize=_fontsize).linewidth(1)
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
            d += elm.Inductor().down().label(getUnitsWithScale(Lshunt_, 'Inductance'), fontsize=_fontsize).linewidth(1)
            
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
        d += elm.Dot().label('ZL = ' + str(float("{:.2f}".format(RL))) + " Ohm", fontsize=_fontsize).linewidth(1)
        
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
            d += elm.Inductor().right().label(getUnitsWithScale(Lshunt_, 'Inductance'), fontsize=_fontsize).linewidth(1)
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
            d += elm.Inductor().down().label(getUnitsWithScale(Lseries_, 'Inductance'), fontsize=_fontsize).linewidth(1)
            
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
                d += elm.Inductor().down().label(getUnitsWithScale(Lseries_, 'Inductance'), fontsize=_fontsize).linewidth(1)    
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
            d += elm.Inductor().right().label(getUnitsWithScale(Lshunt_, 'Inductance'), fontsize=_fontsize).linewidth(1)
            
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
        d += elm.Dot().label('ZL = ' + str(float("{:.2f}".format(RL))) + " Ohm", fontsize=_fontsize).linewidth(1)
        
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
          
    #print (connections)
        
    # Build network and get the frequency response
    circuit = rf.Circuit(connections)
    a = network2.Network.from_ntwkv1(circuit.network)
    S = a.s.val[:]
    freq = a.frequency.f*1e-6
    S11 = 20*np.log10(np.abs(S[:,1][:,1]))
    S21 = 20*np.log10(np.abs(S[:,1][:,0]))

    
    return d, freq, S11, S21
    
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