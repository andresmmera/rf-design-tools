from django.urls import path

from catalog.views import GammaToZView
from catalog.views import tools_catalog
from catalog.views import ZToGammaView
from catalog.views import SWRtoRView
from catalog.views import ReflectionCoefficientDocs

from catalog.views import CalculatePowerConverterView
from catalog.views import RFPowerConversionDocs

from catalog.views import RparallelView
from catalog.views import RparallelDocs

from catalog.views import CseriesView
from catalog.views import CseriesDocs

from catalog.views import BWOctavesView
from catalog.views import BWOctavesDocs

from catalog.views import IP3_DiagramView

urlpatterns = [
    path('', tools_catalog, name='tools-catalog'),
    
    # REFLECTION COEFFICIENT TOOLS
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

    # IP3 AND NOISE-FLOOR DIAGRAM
    path('tool/IP3_NF_diagram', IP3_DiagramView, name='ip3_nf_diagram'),

    # PARALLEL RESISTOR EQUIVALENT
    path('tool/parallel_resistor', RparallelView, name='rparallel_tool'),
    path('tool/parallel_resistor/docs', RparallelDocs, name='rparallel_docs'),

    # SERIES CAPACITOR EQUIVALENT
    path('tool/series_capacitor', CseriesView, name='cseries_tool'),
    path('tool/series_capacitor/docs', CseriesDocs, name='cseries_docs'),
]