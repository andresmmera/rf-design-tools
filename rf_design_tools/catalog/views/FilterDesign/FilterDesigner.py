# Copyright 2020-2021 Andrés Martínez Mera - andresmartinezmera@gmail.com
# Schematic drawing
# Get units with scale, etc.
from ..utilities import *
from .CanonicalFilters import *
from .EllipticFilters import *
from .DirectCoupledFilters import *


from .exportQucs import getEllipticFilterQucsSchematic, getCanonicalFilterQucsSchematic
from .exportQucs import get_DirectCoupled_ShuntResonators_QucsSchematic

import numpy as np

import mysql.connector # MySQL connection for getting the filter coefficient from the Zverev Tables



class Filter:

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
        self.Structure = 'Conventional LC'
        self.DC_Type = 'C-coupled shunt resonators'
        self.FirstElement = 0
        self.PhaseError = 0.05
        self.warning = ''
        self.Xres = [] # Reactances selected by the user for the Direct Coupled LC filter design
        self.Lseries = []
        self.Cseries = []
        self.Cshunt = []

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

    def getParams(self):
        # Pack the design parameters into a dictionary to pass it to external functions
        params = {}
        params['gi'] = self.gi
        params['N'] = self.N
        params['ZS'] = self.ZS
        params['ZL'] = self.ZL
        params['fc'] = self.fc
        params['f1'] = self.f1
        params['f2'] = self.f2
        params['FirstElement'] = self.FirstElement
        params['Mask'] = self.Mask
        params['f_start'] = self.f_start
        params['f_stop'] = self.f_stop
        params['n_points'] = self.n_points
        params['Response'] = self.Response
        params['Ripple'] = self.Ripple
        params['Cseries'] = self.Cseries
        params['Lseries'] = self.Lseries
        params['Cshunt'] = self.Cshunt
        params['EllipticType'] = self.EllipticType
        params['Xres'] = self.Xres
        params['DC_Type'] = self.DC_Type

        return params

    def synthesize(self):
        if (self.Structure == 'Conventional LC'):
            if (self.Response == 'Elliptic'):
                
                if (self.EllipticType == "Type S"):
                    Lseries, Cseries, Cshunt = EllipticTypeS_Coefficients(self.a_s, self.Ripple, self.N)
                    Lseries, Cseries, Cshunt = RearrangeTypeS(Lseries, Cseries, Cshunt)
                    RS = self.ZS
                    RL = RS
                else:
                    Lseries, Cseries, Cshunt, RL = EllipticTypeABC_Coefficients(self.a_s, self.Ripple, self.N, self.ZS, self.EllipticType)
                    Lseries, Cseries, Cshunt = RearrangeTypesABC(Lseries, Cseries, Cshunt, self.EllipticType)

                # Save them into the class so that the export function can use them
                self.Lseries = Lseries
                self.Cseries = Cseries
                self.Cshunt = Cshunt
                self.ZL = RL

                Schematic, connections = SynthesizeEllipticFilter(Lseries, Cseries, Cshunt, self.EllipticType, self.Mask, self.FirstElement, self.ZS, RL, self.fc*1e6, (self.f2-self.f1)*1e6, self.f_start, self.f_stop, self.n_points);
            else: # Conventional LC filters
                self.getLowpassCoefficients()
                params = self.getParams()
                Schematic = getCanonicalFilterSchematic(params)
                connections = getCanonicalFilterNetwork(params)

        elif(self.Structure == 'Direct Coupled LC'):
            self.getLowpassCoefficients()
            BW = self.f2 - self.f1
            if (self.DC_Type == 'C-coupled shunt resonators'):
                if (not self.Xres):
                    Lres = [100e-9] * self.N
                else:
                    Lres = np.asarray(self.Xres, dtype='float64')*1e-9 # nH
                Schematic, connections = DirectCoupled_C_Coupled_ShuntResonators(self.gi, self.ZS, self.ZL, self.fc*1e6, BW*1e6, Lres, self.f_start, self.f_stop, self.n_points)
            elif (self.DC_Type == 'L-coupled shunt resonators'):
                if (not self.Xres):
                    Cres = [10e-12] * self.N
                else:
                    Cres = np.asarray(self.Xres, dtype='float64')*1e-12 # pF
                Schematic, connections = DirectCoupled_L_Coupled_ShuntResonators(self.gi, self.ZS, self.ZL, self.fc*1e6, BW*1e6, Cres, self.f_start, self.f_stop, self.n_points)
            elif (self.DC_Type == 'L-coupled series resonators'):
                # N+2 Coupling inductances
                if (not self.Xres):
                    Lres = [10e-9] * (self.N+2)
                else:
                    Lres = np.asarray(self.Xres, dtype='float64')*1e-9 # nH
                    Lres = np.insert(Lres, 0, Lres[0], axis=0)
                    Lres = np.append(Lres, Lres[-1])
                Schematic, connections = DirectCoupled_L_Coupled_SeriesResonators(self.gi, self.ZS, self.ZL, self.fc*1e6, BW*1e6, Lres, 0, self.f_start, self.f_stop, self.n_points)
            elif (self.DC_Type == 'C-coupled series resonators'):
                if (not self.Xres):
                    Lres = [100e-9] * self.N
                else:
                    Lres = np.asarray(self.Xres, dtype='float64')*1e-9 # nH
                port_match = ['C', 'C']
                Schematic, connections = DirectCoupled_C_Coupled_SeriesResonators(self.gi, self.ZS, self.ZL, self.fc*1e6, BW*1e6, Lres, port_match, self.f_start, self.f_stop, self.n_points)
            elif (self.DC_Type == 'Magnetic coupled resonators'):
                # N+2 Coupling inductances
                if (not self.Xres):
                    Lres = [10e-9] * (self.N+2)
                else:
                    Lres = np.asarray(self.Xres, dtype='float64')*1e-9 # nH
                    Lres = np.insert(Lres, 0, Lres[0], axis=0)
                    Lres = np.append(Lres, Lres[-1])
                Schematic, connections = DirectCoupled_L_Coupled_SeriesResonators(self.gi, self.ZS, self.ZL, self.fc*1e6, BW*1e6, Lres, 1, self.f_start, self.f_stop, self.n_points)
            elif(self.DC_Type == 'Quarter-Wave coupled resonators'):
                Schematic, connections = DirectCoupled_QW_Coupled_ShuntResonators(self.gi, self.ZS, self.ZL, self.fc*1e6, BW*1e6, self.f_start, self.f_stop, self.n_points)

        return Schematic, connections

    def getQucsSchematic(self):
        params = self.getParams()
        if (self.Structure == 'Conventional LC'):
            if (self.Response == 'Elliptic'):
                QucsSchematic = getEllipticFilterQucsSchematic(params)
            else:
                QucsSchematic = getCanonicalFilterQucsSchematic(params)
        elif(self.Structure == 'Direct Coupled LC'):
            if ("shunt" or "Wave" in self.DC_Type):
                QucsSchematic = get_DirectCoupled_ShuntResonators_QucsSchematic(params)

            
        return QucsSchematic