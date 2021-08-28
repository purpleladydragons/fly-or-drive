from django.http import HttpResponse
import json
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from .services.trip_calculator_service import TripCalculatorService

# TODO hack
@csrf_exempt
@require_http_methods(['POST'])
def calculate_trip(request):
    origin = request.POST.get('origin', None)
    destination = request.POST.get('destination', None)
    response = json.dumps(TripCalculatorService.calculate_trip(origin, destination))
    return HttpResponse(response, content_type='application/json')
