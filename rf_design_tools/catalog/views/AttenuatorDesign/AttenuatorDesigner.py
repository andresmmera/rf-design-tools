# Copyright 2020-2021 Andrés Martínez Mera - andresmartinezmera@gmail.com
# Schematic drawing
# Get units with scale, etc.
from ..utilities import *

import numpy as np


from .PiAttenuator import *
from .TeeAttenuator import *
from .BridgedTeeAttenuator import *

from .exportQucs import *

class Attenuator:

    def __init__(self):
        # ATTENUATOR SPECIFICATIONS
        self.f0 = 1000 # Frequency (just for transmission line attenuators) [MHz]
        self.Z1 = 50 # Input impedance
        self.Z2 = 50 # Output impedance
        self.att = 10 # [dB]
        self.Pin = -10 # Input power [dBm]

        # SIMULATION SETUP
        self.f_start = 10
        self.f_stop = 1e3
        self.n_points = 201

    def getParams(self):
        # Pack the design parameters into a dictionary to pass it to external functions
        params = {}
        params['Pin'] = self.Pin
        params['att'] = self.att
        params['f0'] = self.f0
        params['ZL'] = self.ZL
        params['ZS'] = self.ZS
      
        params['f_start'] = self.f_start
        params['f_stop'] = self.f_stop
        params['n_points'] = self.n_points

        return params

    def synthesize(self):
        params = self.getParams();
        if (self.Structure ==  'Pi'):
            Schematic, NetworkType, comp_val = Synthesize_Pi_Attenuator(params);
        elif(self.Structure ==  'Tee'):
            Schematic, NetworkType, comp_val = Synthesize_Tee_Attenuator(params);
        elif(self.Structure ==  'Bridged Tee'):
            Schematic, NetworkType, comp_val = Synthesize_BridgedTee_Attenuator(params);

        return Schematic, NetworkType, comp_val

    def getQucsSchematic(self):
        params = self.getParams()
        if (self.Structure == 'Pi'):
            QucsSchematic = getPiAttenuatorQucsSchematic(params)



            
        return QucsSchematic