# Copyright 2020-2021 Andrés Martínez Mera - andresmartinezmera@gmail.com

from schemdraw.elements import Element2Term
from schemdraw.segments import Segment

# Ideal transmission line component (not available in the Schemdraw library)

class TransmissionLine(Element2Term):
    def __init__(self, *d, **kwargs):
        super().__init__(*d, **kwargs)
        width = 1.5
        height = 0.5
        lead = 0.1
        self.segments.append(Segment([(lead, 0), (lead, -0.5*height), (lead+width, -0.5*height), (lead+width, 0)]))
        self.segments.append(Segment([(0, 0), (lead, 0), (lead, 0.5*height), (lead+width, 0.5*height), (lead+width, 0)]))