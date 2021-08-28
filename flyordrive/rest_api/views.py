from django.http import HttpResponse
import json
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt

# TODO hack
@csrf_exempt
@require_http_methods(['POST'])
def calculate_trip(request):
    origin = request.POST.get('origin', None)
    destination = request.POST.get('destination', None)

    # TODO indicate fail if either one is None

    # TODO calculate info about the trip

    response = json.dumps({'test': True})
    return HttpResponse(response, content_type='application/json')
