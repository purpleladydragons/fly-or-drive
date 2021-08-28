from django.urls import include, path
from rest_framework import routers
from . import views

router = routers.DefaultRouter()

urlpatterns = [
    path('api/', include(router.urls)),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    # path('api/buoy_reads/<int:buoy_id>', views.BuoyReadingViewSet.ListBuoyReadings.as_view()),
    path('api/calculate', views.calculate_trip)
]
