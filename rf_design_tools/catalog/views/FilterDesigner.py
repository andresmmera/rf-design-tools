# Schematic drawing
import schemdraw as schem
import schemdraw.elements as elm

# Get units with scale, etc.
from .utilities import *

import numpy as np

# standard imports
import skrf as rf
from skrf import network2

from multiprocessing.pool import ThreadPool



class Filter:

    FILTER_STRUCTURES =(
    ("1", "LC Ladder"),
    ("2", "Two"),
    ("3", "Three"),
    ("4", "Four"),
    ("5", "Five"),
    )

    RESPONSE_TYPE =(
    ("1", "Chebyshev"),
    ("2", "Butterworth"),
    ("3", "Elliptic"),
    )

    MASK_TYPE =(
        ("1", "Lowpass"),
        ("2", "Highpass"),
        ("3", "Bandpass"),
        ("4", "Bandstop"),
    )

    def __init__(self):
        # FILTER SPECIFICATIONS
        self.fc = 500 # LPF nad HPF: Cutoff frequency (MHz)
        self.f1 = 400 # BPF and BSP: first corner
        self.f2 = 600 # BPF and BSP: second corner

        self.ZS = 50 # Source impedance
        self.ZL = 50 # Load impedance
        self.w0 = 2*np.pi*self.fc*1e6 # rad/s
        self.Mask = 'Bandstop'
        self.Response = 'Chebyshev'
        self.N = 7 # Order
        self.Ripple = 0.1 #dB
        self.Structure = 'LC Ladder'
        self.FirstElement = 0

        if (self.Mask =='Bandpass' or self.Mask =='Bandstop'):
            self.w1 = 2*np.pi*self.f1*1e6 # rad/s
            self.w2 = 2*np.pi*self.f2*1e6 # rad/s
            self.w0 = np.sqrt(self.w1*self.w2)
            self.Delta = self.w2-self.w1

        # SIMULATION SETUP
        self.f_start = 10
        self.f_stop = 1e3
        self.n_points = 201

    def getLowpassCoefficients(self):
        gi = []
        if (self.Response == 'Chebyshev'):
            beta = np.log(1 / np.tanh(self.Ripple / 17.37))
            gamma = np.sinh(beta / (2*self.N))
            ak = []
            bk = []
            for k in range(1, self.N+1):
                ak.append(np.sin((np.pi * (2 * k - 1)) / (2 * self.N)))
                bk.append(gamma * gamma + np.sin(k * np.pi / self.N) * np.sin(k * np.pi / self.N))

            gi.append(1) # Source
            gi.append(2 * ak[0] / gamma)
            for k in range(2, self.N+1):
                gi.append((4 * ak[k - 2] * ak[k - 1]) / (bk[k - 2] * gi[k - 1]))

            # Load
            if (self.N % 2 == 0): # Even
                gi.append(1. / (np.tanh(beta / 4) * np.tanh(beta / 4)))
            else: # Odd
                gi.append(1)

        elif (self.Response == 'Butterworth'):
            gi.append(1) # Source
            for k in range(1, self.N+1):
                gi.append(2 * np.sin(np.pi * (2 * k - 1) / (2 * self.N)))
            gi.append(1) # Load

        return gi

    def getCanonicalFilterSchematic(self):
        gi = self.getLowpassCoefficients()

        if (self.Mask =='Bandpass' or self.Mask =='Bandstop'):
            self.w1 = 2*np.pi*self.f1*1e6 # rad/s
            self.w2 = 2*np.pi*self.f2*1e6 # rad/s
            self.w0 = np.sqrt(self.w1*self.w2)
            self.Delta = self.w2-self.w1
        else:
            self.w0 = 2*np.pi*self.fc*1e6 # rad/s

        print(gi)
        ##################################################
        # Draw circuit
        schem.use('svg')
        d = schem.Drawing()
        _fontsize = 12
        
        # Draw the source port and the first line (if needed)
        d += elm.Dot().label('ZS = ' + str(self.ZS) + " Ohm", fontsize=_fontsize).linewidth(1)
        d += elm.Line().length(2).linewidth(1)
                
        # Draw the filter components
        for i in range(self.N):
            if (((i % 2 == 0) and (self.FirstElement==1)) or ((i % 2 != 0) and (self.FirstElement!=1))):
                d += elm.Dot()
                d.push() # Save the drawing point for later
                
                # Mask-type transformation
                if (self.Mask == 'Lowpass'):
                    d += elm.Capacitor().down().label(getUnitsWithScale(gi[i+1]/(self.ZS*self.w0), 'Capacitance'), fontsize=_fontsize).linewidth(1)
                    d += elm.Ground().linewidth(1)
                elif (self.Mask == 'Highpass'):
                    d += elm.Inductor().down().label(getUnitsWithScale(self.ZS/(gi[i+1]*self.w0), 'Inductance'), fontsize=_fontsize).linewidth(1)
                    d += elm.Ground().linewidth(1)
                elif (self.Mask == 'Bandpass'):
                    d.push()
                    d += elm.Line().down().length(2).linewidth(1)
                    d += elm.Dot()
                    d.push()
                    d += elm.Line().left().length(1).linewidth(1)
                    d += elm.Capacitor().down().label(getUnitsWithScale(gi[i+1]/(self.ZS*self.Delta), 'Capacitance'), fontsize=_fontsize).linewidth(1)
                    d += elm.Ground().linewidth(1)
                    d.pop()
                    d += elm.Line().right().length(1).linewidth(1)
                    d += elm.Inductor().down().label(getUnitsWithScale(self.ZS*self.Delta/(gi[i+1]*self.w0*self.w0), 'Inductance'), fontsize=_fontsize).linewidth(1)
                    d += elm.Ground().linewidth(1)
                    d.pop()
                elif (self.Mask == 'Bandstop'):
                    d += elm.Dot()
                    d.push()
                    d += elm.Inductor().down().label(getUnitsWithScale(self.ZS/(gi[i+1]*self.Delta), 'Inductance'), fontsize=_fontsize).linewidth(1)
                    d += elm.Capacitor().down().label(getUnitsWithScale(gi[i+1]*self.Delta/(self.ZS*self.w0*self.w0), 'Capacitance'), fontsize=_fontsize).linewidth(1)
                    d += elm.Ground().linewidth(1)
                    d.pop()
                    
                d.pop() # Restore the drawing point
            else:
                # Mask-type transformation
                if (self.Mask == 'Lowpass'):
                    d += elm.Inductor().label(getUnitsWithScale(self.ZS*gi[i+1]/self.w0, 'Inductance'), fontsize=_fontsize).linewidth(1)
                elif (self.Mask == 'Highpass'):
                    d += elm.Capacitor().label(getUnitsWithScale(1/(gi[i+1]*self.w0*self.ZS), 'Capacitance'), fontsize=_fontsize).linewidth(1)
                elif (self.Mask == 'Bandpass'):
                    d += elm.Inductor().label(getUnitsWithScale(self.ZS*gi[i+1]/(self.Delta), 'Inductance'), fontsize=_fontsize).linewidth(1)
                    d += elm.Capacitor().label(getUnitsWithScale(self.Delta/(self.ZS*self.w0*self.w0*gi[i+1]), 'Capacitance'), fontsize=_fontsize).linewidth(1)
                elif (self.Mask == 'Bandstop'):
                    d.push()
                    d += elm.Inductor().right().label(getUnitsWithScale(gi[i+1]*self.ZS*self.Delta/(self.w0*self.w0), 'Inductance'), fontsize=_fontsize).linewidth(1)
                    d.pop()
                    d += elm.Line().up().length(2).linewidth(1)
                    d += elm.Capacitor().right().label(getUnitsWithScale(1/(self.ZS*self.Delta*gi[i+1]), 'Capacitance'), fontsize=_fontsize).linewidth(1)
                    d += elm.Line().down().length(2).linewidth(1)

        # Draw the last line (if needed) and the load port
        d += elm.Line().right().length(2).linewidth(1)

        d += elm.Dot().label('ZL = ' + str(float("{:.2f}".format(self.ZS*gi[-1]))) + " Ohm", fontsize=_fontsize).linewidth(1)
        
        return d

    def getCanonicalFilterNetwork(self):

        gi = self.getLowpassCoefficients()
                
        if (self.Mask =='Bandpass' or self.Mask =='Bandstop'):
            self.w1 = 2*np.pi*self.f1*1e6 # rad/s
            self.w2 = 2*np.pi*self.f2*1e6 # rad/s
            self.w0 = np.sqrt(self.w1*self.w2)
            self.Delta = self.w2-self.w1
        else:
            self.w0 = 2*np.pi*self.fc*1e6 # rad/s

        rf.stylely()
        freq = rf.Frequency(start=self.f_start, stop=self.f_stop, npoints=self.n_points, unit='MHz')
        line = rf.media.DefinedGammaZ0(frequency=freq)
        
        Port1 = rf.Circuit.Port(frequency=freq, name='port1', z0=self.ZS)
        Port2 = rf.Circuit.Port(frequency=freq, name='port2', z0=self.ZS*gi[-1])
        
        count_C = 0
        count_L = 0
        count_gnd = 0
        
        C = []
        L = []
        ground = []
        
        # Place components
        for i in range(0, self.N):
            if (((i % 2 == 0) and (self.FirstElement==1)) or ((i % 2 != 0) and (self.FirstElement!=1))):           
                if (self.Mask == 'Lowpass'):
                    # Shunt capacitance
                    count_C += 1
                    C.append(line.capacitor(gi[i+1]/(self.ZS*self.w0), name='C' + str(count_C)))
                    ground.append(rf.Circuit.Ground(frequency=freq, name='ground' + str(count_C), z0=50))
                elif (self.Mask == 'Highpass'):
                    # Shunt inductance
                    count_L += 1
                    L.append(line.inductor(self.ZS/(self.w0*gi[i+1]), name='L' + str(count_L)))
                    ground.append(rf.Circuit.Ground(frequency=freq, name='ground' + str(count_L), z0=50))
                elif (self.Mask == 'Bandpass'):
                    # Shunt parallel resonator
                    count_C += 1
                    count_L += 1
                    C.append(line.capacitor(gi[i+1]/(self.ZS*self.Delta), name='C' + str(count_C)))
                    L.append(line.inductor(self.ZS*self.Delta/(gi[i+1]*self.w0*self.w0), name='L' + str(count_L)))
                    count_gnd += 1
                    ground.append(rf.Circuit.Ground(frequency=freq, name='ground' + str(count_gnd), z0=50))
                    count_gnd += 1
                    ground.append(rf.Circuit.Ground(frequency=freq, name='ground' + str(count_gnd), z0=50))
                elif (self.Mask == 'Bandstop'):
                    # Shunt series resonator
                    count_C += 1
                    count_L += 1
                    C.append(line.capacitor(gi[i+1]*self.Delta/(self.ZS*self.w0*self.w0), name='C' + str(count_C)))
                    L.append(line.inductor(self.ZS/(gi[i+1]*self.Delta), name='L' + str(count_L)))
                    count_gnd += 1
                    ground.append(rf.Circuit.Ground(frequency=freq, name='ground' + str(count_gnd), z0=50))
                
            else:
                if (self.Mask == 'Lowpass'):
                    # Series inductor
                    count_L += 1
                    L.append(line.inductor(self.ZS*gi[i+1]/self.w0, name='L' + str(count_L)))
                elif (self.Mask == 'Highpass'):
                    # Series capacitor
                    count_C += 1
                    C.append(line.capacitor(1/(gi[i+1]*self.w0*self.ZS), name='C' + str(count_C)))
                elif (self.Mask == 'Bandpass'):
                    # Shunt parallel resonator
                    count_C += 1
                    count_L += 1
                    L.append(line.inductor(self.ZS*gi[i+1]/(self.Delta), name='L' + str(count_L)))
                    C.append(line.capacitor(self.Delta/(self.ZS*self.w0*self.w0*gi[i+1]), name='C' + str(count_C)))
                elif (self.Mask == 'Bandstop'):
                    # Series parallel resonator
                    count_C += 1
                    count_L += 1
                    L.append(line.inductor(gi[i+1]*self.ZS*self.Delta/(self.w0*self.w0), name='L' + str(count_L)))
                    C.append(line.capacitor(1/(self.ZS*self.Delta*gi[i+1]), name='C' + str(count_C)))
        
        # Make connections
        connections = []
        if (self.Mask == 'Lowpass'):
            if (self.FirstElement == 1): # First shunt
                connections.append([(Port1, 0), (C[0], 0), (L[0],0)])
                connections.append([(C[0], 1), (ground[0], 0)]) 
                for i in range(1, int(np.floor(self.N/2))):
                    connections.append([(L[i-1], 1), (C[i], 0), (L[i], 0)])
                    connections.append([(C[i], 1), (ground[i], 0)])

                if (self.N % 2 == 0): # Even order
                    connections.append([(Port2, 0), (L[-1],1)])
                else: # Odd order
                    connections.append([(Port2, 0), (C[-1], 0), (L[-1],1)])
                    connections.append([(C[-1], 1), (ground[-1], 0)])

            else: # First series
                connections.append([(Port1, 0), (L[0],0)])
                for i in range(0, int(np.floor(self.N/2))):
                    if (i == np.floor(self.N/2)-1):
                        if (self.N % 2 != 0): # Even
                            connections.append([(L[i], 1), (C[i], 0), (L[i+1], 0)])
                            connections.append([(C[i], 1), (ground[i], 0)])
                    else:
                        connections.append([(L[i], 1), (C[i], 0), (L[i+1], 0)])
                        connections.append([(C[i], 1), (ground[i], 0)])


                if (self.N % 2 == 0): # Even order
                    connections.append([(Port2, 0), (L[-1], 1), (C[-1], 0)])
                    connections.append([(C[-1], 1), (ground[-1], 0)])
                else: # Odd order
                    connections.append([(Port2, 0), (L[-1], 1)])
        elif (self.Mask == 'Highpass'):
            if (self.FirstElement == 1):
                connections.append([(Port1, 0), (L[0], 0), (C[0],0)])
                connections.append([(L[0], 1), (ground[0], 0)]) 
                for i in range(1, int(np.floor(self.N/2))):
                    connections.append([(C[i-1], 1), (L[i], 0), (C[i], 0)])
                    connections.append([(L[i], 1), (ground[i], 0)])

                if (self.N % 2 == 0): # Even order
                    connections.append([(Port2, 0), (C[-1],1)])
                else: # Odd order
                    connections.append([(Port2, 0), (L[-1], 0), (C[-1],1)])
                    connections.append([(L[-1], 1), (ground[-1], 0)])

            else: # First series
                connections.append([(Port1, 0), (C[0],0)])
                for i in range(0, int(np.floor(self.N/2))):
                    if (i == np.floor(self.N/2)-1):
                        if (self.N % 2 != 0): # Even
                            connections.append([(C[i], 1), (L[i], 0), (C[i+1], 0)])
                            connections.append([(L[i], 1), (ground[i], 0)])
                    else:
                        connections.append([(C[i], 1), (L[i], 0), (C[i+1], 0)])
                        connections.append([(L[i], 1), (ground[i], 0)])


                if (self.N % 2 == 0): # Even order
                    connections.append([(Port2, 0), (C[-1], 1), (L[-1], 0)])
                    connections.append([(L[-1], 1), (ground[-1], 0)])
                else: # Odd order
                    connections.append([(Port2, 0), (C[-1], 1)])
        elif (self.Mask == 'Bandpass'):
            if (self.FirstElement == 1):
                connections.append([(Port1, 0), (C[0], 0), (L[0],0), (L[1], 0)])
                connections.append([(L[1], 1), (C[1],0)])
                
                for i in range(2, self.N-1, 2):
                    connections.append([(C[i-1], 1), (C[i], 0), (L[i], 0), (L[i+1], 0)])
                    connections.append([(L[i+1], 1), (C[i+1], 0)])
                        
                if (self.N % 2 == 0): # Even order
                    connections.append([(Port2, 0), (C[-1],1)])
                else: # Odd order
                    connections.append([(Port2, 0), (C[-2], 1), (C[-1], 0), (L[-1],0)])
                    
                for i in range(0, self.N, 2):
                    connections.append([(C[i], 1), (ground[i], 0)])
                    connections.append([(L[i], 1), (ground[i+1], 0)])

            else: # First series
                connections.append([(Port1, 0), (L[0],0)])
                connections.append([(L[0],1), (C[0], 0)])
                
                for i in range(1, self.N-1, 2):
                    connections.append([(C[i-1], 1), (C[i], 0), (L[i], 0), (L[i+1], 0)])
                    connections.append([(L[i+1], 1), (C[i+1], 0)])
                    
                if (self.N % 2 == 0): # Even order
                    connections.append([(Port2, 0), (C[-1],0), (L[-1],0), (C[-2],1)])
                else: # Odd order
                    connections.append([(Port2, 0), (C[-1], 1)])
                    
                for i in range(1, self.N, 2):
                    connections.append([(C[i], 1), (ground[i-1], 0)])
                    connections.append([(L[i], 1), (ground[i], 0)])
                    
        elif (self.Mask == 'Bandstop'):
            if (self.FirstElement == 1):
                connections.append([(Port1, 0), (L[0],0), (L[1], 0), (C[1], 0)])
                connections.append([(L[0],1), (C[0], 0)])
                
                for i in range(2, self.N-1, 2):
                    connections.append([(C[i-1], 1), (L[i-1], 1), (L[i], 0), (L[i+1], 0), (C[i+1], 0)])
                    connections.append([(L[i], 1), (C[i], 0)])
                    
                if (self.N % 2 == 0): # Even order
                    connections.append([(Port2, 0), (C[-1],1), (L[-1],1)])
                else: # Odd order
                    connections.append([(Port2, 0), (L[-2], 1), (C[-2], 1), (L[-1], 0)])
                    connections.append([(L[-1], 1), (C[-1], 0)])
                    
                for i in range(0, self.N, 2):
                    connections.append([(C[i], 1), (ground[int((i+1)/2)], 0)])
            else: # Bandstop first series
                connections.append([(Port1, 0), (L[0],0), (C[0], 0)])
                
                for i in range(1, self.N-1, 2):
                    connections.append([(C[i-1], 1), (L[i-1], 1), (L[i], 0), (L[i+1], 0), (C[i+1], 0)])
                    connections.append([(L[i], 1), (C[i], 0)])
                    
                if (self.N % 2 == 0): # Even order
                    connections.append([(Port2, 0), (L[-2], 1), (C[-2], 1), (L[-1], 0)])
                    connections.append([(L[-1], 1), (C[-1], 0)])
                else: # Odd order
                    connections.append([(Port2, 0), (C[-1],1), (L[-1],1)])
                    
                for i in range(1, self.N, 2):
                    connections.append([(C[i], 1), (ground[int((i+1)/2)-1], 0)])
        circuit = rf.Circuit(connections)
        d = circuit.network
        a = network2.Network.from_ntwkv1(circuit.network)
        S = a.s.val[:]
        freq = a.frequency.f*1e-6
        S11 = 20*np.log10(np.abs(S[:,1][:,1]))
        S21 = 20*np.log10(np.abs(S[:,1][:,0]))
        return freq, S11, S21
    
    def getResponse(self):
        pool = ThreadPool(processes=1)
        async_result = pool.apply_async(self.getCanonicalFilterNetwork, (self,)) # tuple of args for foo
        return async_result.get()