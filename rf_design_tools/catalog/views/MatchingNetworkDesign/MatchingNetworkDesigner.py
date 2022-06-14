# Copyright 2020-2021 Andrés Martínez Mera - andresmartinezmera@gmail.com
# Schematic drawing
# Get units with scale, etc.
from ..utilities import *

import numpy as np


from .Lsection import *

class MatchingNetwork:

    def __init__(self):
        # MATCHING NETWORK SPECIFICATIONS
        self.f0 = 1000 # Frequency (just for transmission line attenuators) [MHz]
        self.RS = 50
        self.XS = 0
        self.RL = 75
        self.XL = 0
        self.Structure = 'L-Section'
        self.Mask = 'Highpass'

        # SIMULATION SETUP
        self.f_start = 10e6
        self.f_stop = 1e9
        self.n_points = 201

    def getParams(self):
        # Pack the design parameters into a dictionary to pass it to external functions
        params = {}
        params['f0'] = self.f0

        params['RS'] = self.RS
        params['XS'] = self.XS

        params['RL'] = self.RL
        params['XL'] = self.XL

        params['Mask'] = self.Mask
      
        params['f_start'] = self.f_start
        params['f_stop'] = self.f_stop
        params['n_points'] = self.n_points

        return params

    def synthesize(self):
        params = self.getParams();
        if (self.Structure ==  'L-Section'):
            Schematic, NetworkType, comp_val = Synthesize_L_Section(params);


        return Schematic, NetworkType, comp_val

