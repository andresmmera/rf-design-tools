# Copyright 2020-2021 Andrés Martínez Mera - andresmartinezmera@gmail.com
# Schematic drawing
# Get units with scale, etc.
from ..utilities import *

import numpy as np


from .Lumped_Pi_type_Line import *

class LumpedTransmissionLine:

    def __init__(self):
        # MATCHING NETWORK SPECIFICATIONS
        self.f0 = 1000 # Frequency (just for transmission line attenuators) [MHz]
        self.Z0 = 50
        self.length = 0.25
        self.Structure = 'Pi-Type'
        self.Mask = 'Lowpass'

        # SIMULATION SETUP
        self.f_start = 10e6
        self.f_stop = 1e9
        self.n_points = 201

    def getParams(self):
        # Pack the design parameters into a dictionary to pass it to external functions
        params = {}
        params['f0'] = self.f0
        params['Z0'] = self.Z0
        params['length'] = self.length

        params['Mask'] = self.Mask
        params['Structure'] = self.Structure
      
        params['f_start'] = self.f_start
        params['f_stop'] = self.f_stop
        params['n_points'] = self.n_points

        return params

    def synthesize(self):
        params = self.getParams();
        Schematic, NetworkType, comp_val = Synthesize_Lumped_Line_Section(params);

        # Define frequency sweep
        if (self.sweep_mode == 1):
            NetworkType['freq'] = np.linspace(self.f_start, self.f_stop, self.n_points)
        else:
            NetworkType['freq'] = np.linspace(self.f0_span-0.5*self.f_span, self.f0_span+0.5*self.f_span, self.n_points)
        return Schematic, NetworkType, comp_val

