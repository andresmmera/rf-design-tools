# Copyright 2020-2021 Andrés Martínez Mera - andresmartinezmera@gmail.com
from django import forms
from django.core.exceptions import ValidationError


class SecondaryImageForm(forms.Form):
    # Secondary Image Calculation
    f_IF1 = forms.FloatField(initial=200,  label='First IF (MHz)')
    f_IF2 = forms.FloatField(initial=10,  label='Second IF (MHz)')
    f_RF = forms.FloatField(initial=800,  label='RF frequency (MHz)')

    def __init__(self, *args, **kwargs):
        super(SecondaryImageForm, self).__init__(*args, **kwargs)
        # Set the width of the boxes
        self.fields['f_IF1'].widget.attrs['style'] = "width:75px"
        self.fields['f_IF2'].widget.attrs['style'] = "width:75px"
        self.fields['f_RF'].widget.attrs['style'] = "width:75px"

        # Set the minimum values
        self.fields['f_IF1'].widget.attrs['min'] = 0
        self.fields['f_IF2'].widget.attrs['min'] = 0
        self.fields['f_RF'].widget.attrs['min'] = 0



FILTER_STRUCTURES =(
("1", "Conventional LC"),
("2", "Direct Coupled LC"),
("3", "Quarter-Wave TL"),
("4", "C-coupled shunt resonators (TL)"),
("5", "Stepped Impedance"),
)

DC_TYPE =(
("1", "C-coupled shunt resonators"),
("2", "L-coupled shunt resonators"),
("3", "L-coupled series resonators"),
("4", "C-coupled series resonators"),
("5", "Magnetic coupled resonators"),
("6", "Quarter-Wave coupled resonators")
)

FIRST_SHUNT_SERIES =(
    ("1", "First Shunt"),
    ("2", "First Series"),
)

RESPONSE_TYPE =(
    ("1", "Elliptic"),
    ("2", "Chebyshev"),
    ("3", "Butterworth"),
    ("4", "Bessel"),
    ("5", "Legendre"),
    ("6", "Gegenbauer"),
    ("7", "LinearPhase"),
    ("8", "Gaussian"),
)

ELLIPTIC_TYPE = (
    ("1", "Type S"),
    ("2", "Type A"),
    ("3", "Type B"),
    ("4", "Type C"),
)

MASK_TYPE =(
    ("1", "Lowpass"),
    ("2", "Highpass"),
    ("3", "Bandpass"),
    ("4", "Bandstop"),
)




class FilterDesignForm(forms.Form):

    Structure = forms.ChoiceField(choices = FILTER_STRUCTURES, widget = forms.Select(attrs = {'onchange' : "submit_form();"}))
    DC_Type = forms.ChoiceField(choices = DC_TYPE, widget = forms.Select(attrs = {'onchange' : "submit_form();"}))
    FirstElement = forms.ChoiceField(choices = FIRST_SHUNT_SERIES, widget = forms.Select(attrs = {'onchange' : "submit_form();"}))
    Response = forms.ChoiceField(choices = RESPONSE_TYPE, widget = forms.Select(attrs = {'onchange' : "submit_form();"}))
    EllipticType = forms.ChoiceField(choices = ELLIPTIC_TYPE, widget = forms.Select(attrs = {'onchange' : "submit_form();"}))
    Mask = forms.ChoiceField(choices = MASK_TYPE, widget = forms.Select(attrs = {'onchange' : "updateMask(this.value);"}))
    Order = forms.IntegerField(initial=3, min_value=1, widget = forms.NumberInput(attrs = {'onchange' : "submit_form();"}))
    Cutoff = forms.FloatField(initial=1000, widget = forms.NumberInput(attrs = {'onchange' : "submit_form();"})) # LPF and HPF
    f1 = forms.FloatField(initial=200, widget = forms.NumberInput(attrs = {'onchange' : "submit_form();"})) # BPF and BSF
    f2 = forms.FloatField(initial=400, widget = forms.NumberInput(attrs = {'onchange' : "submit_form();"})) # BPF and BSF
    Ripple = forms.FloatField(initial=0.01, widget = forms.NumberInput(attrs = {'onchange' : "submit_form();"}))
    a_s = forms.FloatField(initial=35, widget = forms.NumberInput(attrs = {'onchange' : "submit_form();"}))
    PhaseError = forms.FloatField(initial=0.05, widget = forms.NumberInput(attrs = {'onchange' : "submit_form();"}))
    ZS = forms.FloatField(initial=50, min_value=0.1, widget = forms.NumberInput(attrs = {'onchange' : "submit_form();"}))
    ZL = forms.FloatField(initial=50, min_value=0.1, widget = forms.NumberInput(attrs = {'onchange' : "submit_form();"}))
    f_start = forms.FloatField(initial=50, min_value=0.1, widget = forms.NumberInput(attrs = {'onchange' : "submit_form();"}))
    f_stop = forms.FloatField(initial=1000, min_value=0.1, widget = forms.NumberInput(attrs = {'onchange' : "submit_form();"}))
    n_points = forms.IntegerField(initial=201, min_value=50, widget = forms.NumberInput(attrs = {'onchange' : "submit_form();"}))
   
    def __init__(self, *args, **kwargs):
        super(FilterDesignForm, self).__init__(*args, **kwargs)
        # Set the width of the boxes
        self.fields['Order'].widget.attrs['style'] = "width:75px"
        self.fields['Cutoff'].widget.attrs['style'] = "width:75px" # LPF and HPF
        self.fields['f1'].widget.attrs['style'] = "width:75px" # BPF and BSF
        self.fields['f2'].widget.attrs['style'] = "width:75px" # BPF and BSF
        self.fields['Ripple'].widget.attrs['style'] = "width:75px"
        self.fields['a_s'].widget.attrs['style'] = "width:75px"
        self.fields['PhaseError'].widget.attrs['style'] = "width:75px" # Just for Linear Phase Error filters
        self.fields['ZS'].widget.attrs['style'] = "width:75px"
        self.fields['ZL'].widget.attrs['style'] = "width:75px"
        self.fields['f_start'].widget.attrs['style'] = "width:75px"
        self.fields['f_stop'].widget.attrs['style'] = "width:75px"
        self.fields['n_points'].widget.attrs['style'] = "width:75px"


ATTENUATOR_STRUCTURES =(
("1", "Pi"),
("2", "Tee"),
("3", "Bridged Tee"),
("4", "Reflection Attenuator"),
("5", "Quarter Wave Series"),
("6", "Quarter Wave Shunt"),
)


class AttenuatorDesignForm(forms.Form):

    f0 = forms.FloatField(initial=1000, widget = forms.NumberInput(attrs = {'onchange' : "submit_form();"}))
    Pin = forms.FloatField(initial=-10, widget = forms.NumberInput(attrs = {'onchange' : "submit_form();"})) # dBm
    ZS = forms.FloatField(initial=50, widget = forms.NumberInput(attrs = {'onchange' : "submit_form();"}))
    ZL = forms.FloatField(initial=50, widget = forms.NumberInput(attrs = {'onchange' : "submit_form();"}))
    att = forms.FloatField(initial=10, widget = forms.NumberInput(attrs = {'onchange' : "submit_form();"}))
    Structure = forms.ChoiceField(choices = ATTENUATOR_STRUCTURES, widget = forms.Select(attrs = {'onchange' : "submit_form();"}))
   
    def __init__(self, *args, **kwargs):
        super(AttenuatorDesignForm, self).__init__(*args, **kwargs)
        # Set the width of the boxes
        self.fields['f0'].widget.attrs['style'] = "width:75px"
        self.fields['Pin'].widget.attrs['style'] = "width:75px"
        self.fields['ZS'].widget.attrs['style'] = "width:75px"
        self.fields['ZL'].widget.attrs['style'] = "width:75px"
        self.fields['att'].widget.attrs['style'] = "width:75px"


MATCHING_NETWORK_STRUCTURES =(
("1", "L-Section"),
("2", "Pi"),
("3", "Tee"),
("4", "Single Stub"),
("5", "Double Stub"),
("6", "&#955;/4"),
("7", "&#955;/8 + &#955;/4"),
("8", "Single-Section Transformer"),
("9", "Multisection &#955;/4 Transformer"),
("10", "Tapped-C Transformer"),
("11", "Tapped-L Transformer"),
#("8", "lambda/4 matching"),
#("9", "Multistage lambda/4"),
#("12", "Double-tapped resonator"),
#("13", "Single-tuned transformer"),
#("14", "Parallel double-tuned transformer"),
#("15", "Series double-tuned transformer"),
)
