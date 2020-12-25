from django.urls import path
from catalog import views
from catalog.views import *

urlpatterns = [
    path('', tools_catalog, name='tools-catalog'),
    
    path('tool/reflection_coefficient/RtoZ', GammaToZView, name='RtoZ_tool'),
    path('tool/reflection_coefficient/ZtoR', ZToGammaView, name='ZtoR_tool'),
    path('tool/reflection_coefficient/SWRtoR', SWRtoRView, name='SWRtoR_tool'),
    path('tool/reflection_coefficient/docs', ReflectionCoefficientDocs, name='reflection_coeff_docs'),
    
    path('tool/rf_power_converter', CalculatePowerConverterView, name='rf_power_converter_tool'),
    path('tool/rf_power_converter/docs', RFPowerConversionDocs, name='rf_power_converter_docs'),

    path('tool/parallel_resistor', RparallelView, name='rparallel_tool'),
    path('tool/parallel_resistor/docs', RparallelDocs, name='rparallel_docs'),

    path('tool/series_capacitor', CseriesView, name='cseries_tool'),
]