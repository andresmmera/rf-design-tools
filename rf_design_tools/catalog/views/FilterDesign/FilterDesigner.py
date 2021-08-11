# Schematic drawing
import schemdraw as schem
import schemdraw.elements as elm
from skrf.mathFunctions import find_closest

# Get units with scale, etc.
from ..utilities import *
from .EllipticFilters import *

import numpy as np

# standard imports
import skrf as rf
from skrf import network2

from multiprocessing.pool import ThreadPool

import mysql.connector # MySQL connection for getting the filter coefficient from the Zverev Tables



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
    ("3", "Bessel"),
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
        self.EllipticType = "Type S"
        self.N = 7 # Order
        self.Ripple = 0.1 #dB
        self.a_s = 35 #dB
        self.Structure = 'LC Ladder'
        self.FirstElement = 0
        self.PhaseError = 0.05
        self.warning = ''

        if (self.Mask =='Bandpass' or self.Mask =='Bandstop'):
            self.w1 = 2*np.pi*self.f1*1e6 # rad/s
            self.w2 = 2*np.pi*self.f2*1e6 # rad/s
            self.w0 = np.sqrt(self.w1*self.w2)
            self.Delta = self.w2-self.w1

        # SIMULATION SETUP
        self.f_start = 10
        self.f_stop = 1e3
        self.n_points = 201

        # OPEN DATABASE CONNECTION FOR THE ZVEREV TABLES
        self.ZverevDB = mysql.connector.connect(
          host="localhost",
          user="admin",
          passwd="",
          database="ZverevTables"
        )
        self.gi = []

    def getLowpassCoefficients(self):
        self.gi = []
        if ((self.Response == 'Chebyshev') and (self.ZS == self.ZL)):
            beta = np.log(1 / np.tanh(self.Ripple / 17.37))
            gamma = np.sinh(beta / (2*self.N))
            ak = []
            bk = []
            for k in range(1, self.N+1):
                ak.append(np.sin((np.pi * (2 * k - 1)) / (2 * self.N)))
                bk.append(gamma * gamma + np.sin(k * np.pi / self.N) * np.sin(k * np.pi / self.N))

            self.gi.append(1) # Source
            self.gi.append(2 * ak[0] / gamma)
            for k in range(2, self.N+1):
                self.gi.append((4 * ak[k - 2] * ak[k - 1]) / (bk[k - 2] * self.gi[k - 1]))

            # Load
            if (self.N % 2 == 0): # Even
                self.gi.append(1. / (np.tanh(beta / 4) * np.tanh(beta / 4)))
            else: # Odd
                self.gi.append(1)

        elif ((self.Response == 'Butterworth') and (self.ZS == self.ZL)):
            self.gi.append(1) # Source
            for k in range(1, self.N+1):
                self.gi.append(2 * np.sin(np.pi * (2 * k - 1) / (2 * self.N)))
            self.gi.append(1) # Load

        else: # Take the coefficients from the Zverev Database
                        
            ZDB_cursor = self.ZverevDB.cursor()

            # Get all possible values of N and find the closest in DB
            query_str = "SELECT DISTINCT N FROM ZverevTables."+ self.Response
            ZDB_cursor.execute(query_str)
            N_all = ZDB_cursor.fetchall()          
            N_DB = [row[0] for row in N_all]
            N = find_nearest(N_DB, self.N)

            # Get all possible values of RL given N
            query_str = "SELECT DISTINCT RS FROM ZverevTables."+ self.Response + " WHERE ""N='"+ str(N) + "';"
            ZDB_cursor.execute(query_str)
            RS_all = ZDB_cursor.fetchall()          
            RS_DB = [row[0] for row in RS_all]
            RS_user = self.ZL/self.ZS

            print("User N : ", self.N)
            print("Available N in DB: ", N_DB)
            print("Selected N from DB: ", N)

            print("User RL : ", RS_user)
            print("Available RL in DB: ", RS_DB)
            
            if ((RS_user > max(RS_DB)) or (RS_user < min(RS_DB))):
                RS_user = 1/RS_user

            RS = find_nearest(RS_DB, RS_user)
            
            print("Selected RL from DB: ", RS)

            if (self.Response == 'Butterworth' or self.Response == 'Bessel' or self.Response == 'Gaussian' or self.Response == 'Legendre'):
                query_str = "SELECT Coefficients FROM ZverevTables."+ self.Response + " WHERE ""N='"+ str(N) + "' AND RS='" + str(RS) + "';"
            elif(self.Response == 'LinearPhase'):
                # Get all possible values of PhaseError
                query_str = "SELECT DISTINCT PhaseError FROM ZverevTables."+ self.Response + " WHERE ""N='"+ str(N) + "' AND RS='" + str(RS) + "';"
                ZDB_cursor.execute(query_str)
                PhaseError_all = ZDB_cursor.fetchall()          
                PhaseError_DB = [row[0] for row in PhaseError_all]
                PhaseError = find_nearest(PhaseError_DB, self.PhaseError)

                print("User Phase Error : ", self.PhaseError)
                print("Available Phase Error in DB: ", PhaseError_DB)
                print("Selected Ripple from DB: ", PhaseError)
                
                query_str = "SELECT Coefficients FROM ZverevTables."+ self.Response + " WHERE ""N='"+ str(N) + "' AND RS='" + str(RS) + "' AND PhaseError='" + str(PhaseError) + "';"


            else:
                # Get all possible values of Ripple
                query_str = "SELECT DISTINCT Ripple FROM ZverevTables."+ self.Response + " WHERE ""N='"+ str(N) + "' AND RS='" + str(RS) + "';"
                ZDB_cursor.execute(query_str)
                Ripple_all = ZDB_cursor.fetchall()          
                Ripple_DB = [row[0] for row in Ripple_all]
                Ripple = find_nearest(Ripple_DB, self.Ripple)

                print("User Ripple : ", self.Ripple)
                print("Available Ripple in DB: ", Ripple_DB)
                print("Selected Ripple from DB: ", Ripple)

                query_str = "SELECT Coefficients FROM ZverevTables."+ self.Response + " WHERE ""N='"+ str(N) + "' AND RS='" + str(RS) + "' AND RIPPLE='" + str(Ripple) + "';"
            
            ZDB_cursor.execute(query_str)
            gi_str = ZDB_cursor.fetchall()
            #print("QUERY: ", query_str)
            #print("Response DB: ", gi_str)
            gi = str(gi_str[0])[2:-3].split(';')
            gi = gi[:-1] # Remove last blank space
            gi = [float(i) for i in gi]

            # Odd order implementations can realize RS > 1 or RS < 1, but even order doesn't 

            # At this point, we have the same record as in the DB. Now, it is needed to transform the coefficients to match the user request.
            if (N % 2 == 0): # Even. e.g. N = 4, 6, 8, ...
                if self.ZL/self.ZS > 1 : # First shunt
                    # It must be first series
                    if self.FirstElement == 1:
                    # Throw a warning to the user
                        self.warning = 'Even order first-shunt type filters cannot transform a low source impedance to a high load impedance. The topology was changes to first-series'
                    self.FirstElement = 2
                    gi = gi[::-1]
                else: # First shunt
                    # It must be first shunt
                    if self.FirstElement == 2:
                    # Throw a warning to the user
                        self.warning = 'Even order first-series type filters cannot transform a high source impedance to a low load impedance. The topology was changes to first-shunt'
                    self.FirstElement = 1
                     # TO DO: Throw a warning to the user
                    for i in range(1, len(gi)-1):
                        if i % 2 ==0 :
                            gi[i] = gi[i]/gi[0]
                        else:
                            gi[i] = gi[i]*gi[0]
                    gi[-1] = 1/gi[0]
                    gi[0] = 1

            else: # Odd, e.g. N = 3,5,7, ...
                if self.FirstElement == 1: # First shunt
                    # e.g. gi = {0.7, ..., 1}
                    if self.ZL/self.ZS < 1:
                        gi = gi[::-1]
                    else: # RS > 1
                        for i in range(0, len(gi)-1):
                            if i % 2 ==0 :
                                gi[i] = gi[i]/gi[0]
                            else:
                                gi[i] = gi[i]*gi[0]
                else: # First series
                    if self.ZL/self.ZS < 1:
                        for i in range(1, len(gi)-1):
                            if i % 2 ==0 :
                                gi[i] = gi[i]/gi[0]
                            else:
                                gi[i] = gi[i]*gi[0]
                        gi[-1] = gi[-1]*gi[0]
                        gi[0] = 1
                    else:
                        gi = gi[::-1]
                        gi[-1] = 1/gi[-1]
            
            print('gi = ', gi)

            self.gi = gi

    def getCanonicalFilterSchematic(self):
        if (self.Mask =='Bandpass' or self.Mask =='Bandstop'):
            self.w1 = 2*np.pi*self.f1*1e6 # rad/s
            self.w2 = 2*np.pi*self.f2*1e6 # rad/s
            self.w0 = np.sqrt(self.w1*self.w2)
            self.Delta = self.w2-self.w1
        else:
            self.w0 = 2*np.pi*self.fc*1e6 # rad/s

        print(self.gi)
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
                    d += elm.Capacitor().down().label(getUnitsWithScale(self.gi[i+1]/(self.ZS*self.w0), 'Capacitance'), fontsize=_fontsize).linewidth(1)
                    d += elm.Ground().linewidth(1)
                elif (self.Mask == 'Highpass'):
                    d += elm.Inductor().down().label(getUnitsWithScale(self.ZS/(self.gi[i+1]*self.w0), 'Inductance'), fontsize=_fontsize).linewidth(1)
                    d += elm.Ground().linewidth(1)
                elif (self.Mask == 'Bandpass'):
                    d.push()
                    d += elm.Line().down().length(2).linewidth(1)
                    d += elm.Dot()
                    d.push()
                    d += elm.Line().left().length(1).linewidth(1)
                    d += elm.Capacitor().down().label(getUnitsWithScale(self.gi[i+1]/(self.ZS*self.Delta), 'Capacitance'), fontsize=_fontsize).linewidth(1)
                    d += elm.Ground().linewidth(1)
                    d.pop()
                    d += elm.Line().right().length(1).linewidth(1)
                    d += elm.Inductor().down().label(getUnitsWithScale(self.ZS*self.Delta/(self.gi[i+1]*self.w0*self.w0), 'Inductance'), fontsize=_fontsize).linewidth(1)
                    d += elm.Ground().linewidth(1)
                    d.pop()
                elif (self.Mask == 'Bandstop'):
                    d += elm.Dot()
                    d.push()
                    d += elm.Inductor().down().label(getUnitsWithScale(self.ZS/(self.gi[i+1]*self.Delta), 'Inductance'), fontsize=_fontsize).linewidth(1)
                    d += elm.Capacitor().down().label(getUnitsWithScale(self.gi[i+1]*self.Delta/(self.ZS*self.w0*self.w0), 'Capacitance'), fontsize=_fontsize).linewidth(1)
                    d += elm.Ground().linewidth(1)
                    d.pop()
                    
                d.pop() # Restore the drawing point
            else:
                # Mask-type transformation
                if (self.Mask == 'Lowpass'):
                    d += elm.Inductor().label(getUnitsWithScale(self.ZS*self.gi[i+1]/self.w0, 'Inductance'), fontsize=_fontsize).linewidth(1)
                elif (self.Mask == 'Highpass'):
                    d += elm.Capacitor().label(getUnitsWithScale(1/(self.gi[i+1]*self.w0*self.ZS), 'Capacitance'), fontsize=_fontsize).linewidth(1)
                elif (self.Mask == 'Bandpass'):
                    d += elm.Inductor().label(getUnitsWithScale(self.ZS*self.gi[i+1]/(self.Delta), 'Inductance'), fontsize=_fontsize).linewidth(1)
                    d += elm.Capacitor().label(getUnitsWithScale(self.Delta/(self.ZS*self.w0*self.w0*self.gi[i+1]), 'Capacitance'), fontsize=_fontsize).linewidth(1)
                elif (self.Mask == 'Bandstop'):
                    d.push()
                    d += elm.Inductor().right().label(getUnitsWithScale(self.gi[i+1]*self.ZS*self.Delta/(self.w0*self.w0), 'Inductance'), fontsize=_fontsize).linewidth(1)
                    d.pop()
                    d += elm.Line().up().length(2).linewidth(1)
                    d += elm.Capacitor().right().label(getUnitsWithScale(1/(self.ZS*self.Delta*self.gi[i+1]), 'Capacitance'), fontsize=_fontsize).linewidth(1)
                    d += elm.Line().down().length(2).linewidth(1)

        # Draw the last line (if needed) and the load port
        d += elm.Line().right().length(2).linewidth(1)

        d += elm.Dot().label('ZL = ' + str(float("{:.2f}".format(self.ZS*self.gi[-1]))) + " Ohm", fontsize=_fontsize).linewidth(1)
        
        return d

    def getCanonicalFilterNetwork(self):              
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
        Port2 = rf.Circuit.Port(frequency=freq, name='port2', z0=self.ZS*self.gi[-1])
        
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
                    C.append(line.capacitor(self.gi[i+1]/(self.ZS*self.w0), name='C' + str(count_C)))
                    ground.append(rf.Circuit.Ground(frequency=freq, name='ground' + str(count_C), z0=50))
                elif (self.Mask == 'Highpass'):
                    # Shunt inductance
                    count_L += 1
                    L.append(line.inductor(self.ZS/(self.w0*self.gi[i+1]), name='L' + str(count_L)))
                    ground.append(rf.Circuit.Ground(frequency=freq, name='ground' + str(count_L), z0=50))
                elif (self.Mask == 'Bandpass'):
                    # Shunt parallel resonator
                    count_C += 1
                    count_L += 1
                    C.append(line.capacitor(self.gi[i+1]/(self.ZS*self.Delta), name='C' + str(count_C)))
                    L.append(line.inductor(self.ZS*self.Delta/(self.gi[i+1]*self.w0*self.w0), name='L' + str(count_L)))
                    count_gnd += 1
                    ground.append(rf.Circuit.Ground(frequency=freq, name='ground' + str(count_gnd), z0=50))
                    count_gnd += 1
                    ground.append(rf.Circuit.Ground(frequency=freq, name='ground' + str(count_gnd), z0=50))
                elif (self.Mask == 'Bandstop'):
                    # Shunt series resonator
                    count_C += 1
                    count_L += 1
                    C.append(line.capacitor(self.gi[i+1]*self.Delta/(self.ZS*self.w0*self.w0), name='C' + str(count_C)))
                    L.append(line.inductor(self.ZS/(self.gi[i+1]*self.Delta), name='L' + str(count_L)))
                    count_gnd += 1
                    ground.append(rf.Circuit.Ground(frequency=freq, name='ground' + str(count_gnd), z0=50))
                
            else:
                if (self.Mask == 'Lowpass'):
                    # Series inductor
                    count_L += 1
                    L.append(line.inductor(self.ZS*self.gi[i+1]/self.w0, name='L' + str(count_L)))
                elif (self.Mask == 'Highpass'):
                    # Series capacitor
                    count_C += 1
                    C.append(line.capacitor(1/(self.gi[i+1]*self.w0*self.ZS), name='C' + str(count_C)))
                elif (self.Mask == 'Bandpass'):
                    # Shunt parallel resonator
                    count_C += 1
                    count_L += 1
                    L.append(line.inductor(self.ZS*self.gi[i+1]/(self.Delta), name='L' + str(count_L)))
                    C.append(line.capacitor(self.Delta/(self.ZS*self.w0*self.w0*self.gi[i+1]), name='C' + str(count_C)))
                elif (self.Mask == 'Bandstop'):
                    # Series parallel resonator
                    count_C += 1
                    count_L += 1
                    L.append(line.inductor(self.gi[i+1]*self.ZS*self.Delta/(self.w0*self.w0), name='L' + str(count_L)))
                    C.append(line.capacitor(1/(self.ZS*self.Delta*self.gi[i+1]), name='C' + str(count_C)))
        
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
    
    def synthesize(self):
        if (self.Response == 'Elliptic'):
            
            if (self.EllipticType == "Type S"):
                Lseries, Cseries, Cshunt = EllipticTypeS_Coefficients(self.a_s, self.Ripple, self.N)
                Lseries, Cseries, Cshunt = RearrangeTypeS(Lseries, Cseries, Cshunt)
                RS = self.ZS
                RL = RS
            else:
                Lseries, Cseries, Cshunt, RL = EllipticTypeABC_Coefficients(self.a_s, self.Ripple, self.N, self.ZS, self.EllipticType)
                Lseries, Cseries, Cshunt = RearrangeTypesABC(Lseries, Cseries, Cshunt, self.EllipticType)

            Schematic, freq, S11, S21 = SynthesizeEllipticFilter(Lseries, Cseries, Cshunt, self.EllipticType, self.Mask, self.FirstElement, self.ZS, RL, self.fc*1e6, (self.f2-self.f1)*1e6, self.f_start, self.f_stop, self.n_points);
        else:
            self.getLowpassCoefficients()
            Schematic = self.getCanonicalFilterSchematic()
            freq, S11, S21 = self.getCanonicalFilterNetwork()
        return Schematic, freq, S11, S21


    def getResponse(self):
        pool = ThreadPool(processes=1)
        async_result = pool.apply_async(self.getCanonicalFilterNetwork, (self,)) # tuple of args for foo
        return async_result.get()