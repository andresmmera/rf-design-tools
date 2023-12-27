# Copyright 2020-2021 Andrés Martínez Mera - andresmartinezmera@gmail.com
# Schematic drawing
# Get units with scale, etc.
from ..utilities import *

import numpy as np


from .Lsection import *
from .PiMatching import *
from .TeeMatching import *
from .SingleStub import *
from .DoubleStub import *
from .L4L8_Matching import *
from .L4_Matching import *
from .SingleSectionTransformer import *
from .Multisection_TL_Transformer import *
from .TappedC_Matching import *
from .TappedL_Matching import *

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
        self.PiTee_NetworkMask = 1
        self.Q = 1

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
        
        params['Q'] = self.Q
        params['N'] = self.N
        params['StubType'] = self.StubType
        params['PiTee_NetworkMask'] = self.PiTee_NetworkMask
        params['Weighting'] = self.Weighting
        params['gamma_max'] = self.gamma_max

        params['Mask'] = self.Mask
      
        params['f_start'] = self.f_start
        params['f_stop'] = self.f_stop
        params['n_points'] = self.n_points

        return params

    def synthesize(self):
        params = self.getParams();
        if (self.Structure ==  'L-Section'):
            Schematic, NetworkType, comp_val = Synthesize_L_Section(params)
        elif (self.Structure == 'Pi'):
            Schematic, NetworkType, comp_val = Pi_MatchingNetwork(params)
        elif (self.Structure == 'Tee'):
            Schematic, NetworkType, comp_val = Tee_MatchingNetwork(params)
        elif (self.Structure == 'Single Stub'):
            Schematic, NetworkType, comp_val = SingleStub_MatchingNetwork(params)
        elif (self.Structure == 'Double Stub'):
            Schematic, NetworkType, comp_val = DoubleStub_MatchingNetwork(params)
        elif (self.Structure == '&#955;/4'):
            Schematic, NetworkType, comp_val = L4_MatchingNetwork(params)
        elif (self.Structure == '&#955;/8 + &#955;/4'):
            Schematic, NetworkType, comp_val = L4L8_MatchingNetwork(params)
        elif (self.Structure == 'Single-Section Transformer'):
            Schematic, NetworkType, comp_val = SingleSectionTransformer_MatchingNetwork(params)
        elif (self.Structure == 'Multisection &#955;/4 Transformer'):
            Schematic, NetworkType, comp_val = MultiSection_TL_Transformer_MatchingNetwork(params)
        elif (self.Structure == 'Tapped-C Transformer'):
            Schematic, NetworkType, comp_val = Tapped_C_Transformer_MatchingNetwork(params)
        elif (self.Structure == 'Tapped-L Transformer'):
            Schematic, NetworkType, comp_val = Tapped_L_Transformer_MatchingNetwork(params)



        
        # Define frequency sweep
        if (self.sweep_mode == 1):
            NetworkType['freq'] = np.linspace(self.f_start, self.f_stop, self.n_points)
        else:
            NetworkType['freq'] = np.linspace(self.f0_span-0.5*self.f_span, self.f0_span+0.5*self.f_span, self.n_points)
        return Schematic, NetworkType, comp_val

