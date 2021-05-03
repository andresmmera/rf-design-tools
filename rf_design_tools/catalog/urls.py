from django.urls import path

from catalog.views import GammaToZView
from catalog.views import tools_catalog
from catalog.views import ZToGammaView
from catalog.views import SWRtoRView
from catalog.views import ReflectionCoefficientDocs
from catalog.views import ReflectionToolsCatalogView

from catalog.views import CalculatePowerConverterView
from catalog.views import RFPowerConversionDocs

from catalog.views import CapRes_CatalogView
from catalog.views import RparallelView
from catalog.views import RparallelDocs
from catalog.views import CseriesView
from catalog.views import CseriesDocs

from catalog.views import BWOctavesView
from catalog.views import BWOctavesDocs

from catalog.views import WavelengthFrequencyView

from catalog.views import IPn_DiagramView
from catalog.views import IPn_DiagramDocs

from catalog.views import ImageFrequencyCatalogView
from catalog.views import ImageFrequencyView
from catalog.views import HalfIFView
from catalog.views import SecondaryImageView

from catalog.views import ImageFrequencyDocs
from catalog.views import ImageFrequency_CatalogNotes
from catalog.views import HartleyImageRejectionMixersDocs
from catalog.views import WeaverImageRejectionMixersDocs
from catalog.views import SSBMixerNotes

from catalog.views import SystemBalanceView
from catalog.views import SystemBalanceDocs

urlpatterns = [
    path('', tools_catalog, name='tools-catalog'),
    
    # REFLECTION COEFFICIENT TOOLS
    path('tool/reflection_coefficient', ReflectionToolsCatalogView, name='reflection_coeff_tools'),
    path('tool/reflection_coefficient/RtoZ', GammaToZView, name='RtoZ_tool'),
    path('tool/reflection_coefficient/ZtoR', ZToGammaView, name='ZtoR_tool'),
    path('tool/reflection_coefficient/SWRtoR', SWRtoRView, name='SWRtoR_tool'),
    path('tool/reflection_coefficient/docs', ReflectionCoefficientDocs, name='reflection_coeff_docs'),
    
    # RF POWER CONVERTER
    path('tool/rf_power_converter', CalculatePowerConverterView, name='rf_power_converter_tool'),
    path('tool/rf_power_converter/docs', RFPowerConversionDocs, name='rf_power_converter_docs'),

    # CALCULATE BANDWIDTH IN OCTAVES AND QUALITY FACTOR
    path('tool/bw_octaves', BWOctavesView, name='bw_octaves_tool'),
    path('tool/bw_octaves/docs', BWOctavesDocs, name='bw_octaves_docs'),

    # IPn AND NOISE-FLOOR DIAGRAM
    path('tool/IPn_NF_diagram', IPn_DiagramView, name='ipn_nf_diagram'),
    path('tool/IPn_NF_diagram/docs', IPn_DiagramDocs, name='ipn_nf_docs'),

    ###############################################################################
    # CAPACITOR AND RESISTOR CALCULATORS
    path('tool/Capacitor_Resistor_Calculators', CapRes_CatalogView, name='CapRes_Catalog'),

    ## PARALLEL RESISTOR EQUIVALENT
    path('tool/Capacitor_Resistor_Calculators/parallel_resistor', RparallelView, name='rparallel_tool'),
    path('tool/Capacitor_Resistor_Calculators/parallel_resistor/docs', RparallelDocs, name='rparallel_docs'),

    ## SERIES CAPACITOR EQUIVALENT
    path('tool/Capacitor_Resistor_Calculators/series_capacitor', CseriesView, name='cseries_tool'),
    path('tool/Capacitor_Resistor_Calculators/series_capacitor/docs', CseriesDocs, name='cseries_docs'),
    #################################################################################

    ## WAVELENGTH AND FREQUENCY CALCULATOR
    path('tool/wavelength_and_frequency', WavelengthFrequencyView, name='wavelength_frequency_tool'),

    #################################################################################

    # FREQUENCY PLANNING TOOLS
    path('tool/frequency_planning', ImageFrequencyCatalogView, name='image_frequency_catalog'),
    path('tool/frequency_planning/image_planning', ImageFrequencyView, name='image_frequency_planning'),
    path('tool/frequency_planning/image_planning/docs/image_frequency', ImageFrequencyDocs, name='image_frequency_planning_docs'),
    path('tool/frequency_planning/image_planning/docs', ImageFrequency_CatalogNotes, name='image_frequency_docs'),
    path('tool/frequency_planning/half_IF', HalfIFView, name='half_IF_tool'),
    path('tool/frequency_planning/SecondaryImage_tool', SecondaryImageView, name='Secondary_image_tool'),
    # Image rejection notes
    path('tool/frequency_planning/image_planning/docs/hartley_irm', HartleyImageRejectionMixersDocs, name='hartley_irm_docs'),
    path('tool/frequency_planning/image_planning/docs/ssb_mixer', SSBMixerNotes, name='ssb_mixer_notes'),
    path('tool/frequency_planning/image_planning/docs/weaver_irm', WeaverImageRejectionMixersDocs, name='weaver_irm_docs'),

    #################################################################################
    # SYSTEM BALANCE
    path('tool/system_balance', SystemBalanceView, name='system_balance_tool'),
    path('tool/system_balance/docs', SystemBalanceDocs, name='system_balance_docs'),
]