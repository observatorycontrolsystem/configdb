from datetime import datetime
from dateutil.parser import parse
from django.utils import timezone
from django.views.generic import TemplateView
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponseNotFound
from rest_framework.generics import RetrieveAPIView

from configdb.hardware.serializers import AvailabilityHistorySerializer
from configdb.hardware.models import Site, Telescope, Camera, Instrument, OpticalElementGroup, GenericModeGroup
from configdb.hardware.availability import build_instrument_availability_history, build_telescope_availability_history

class IndexView(TemplateView):
    template_name = 'hardware/index.html'

    def get_context_data(self, **kwargs):
        context = super(IndexView, self).get_context_data(**kwargs)
        context['site_count'] = Site.objects.count()
        context['telescope_count'] = Telescope.objects.count()
        context['camera_count'] = Camera.objects.count()
        context['instrument_count'] = Instrument.objects.count()
        context['opticalelementgroup_count'] = OpticalElementGroup.objects.count()
        context['genericmodegroup_count'] = GenericModeGroup.objects.count()
        return context


class AvailabilityHistoryView(RetrieveAPIView):
    """ Use django-reversion models to build a set of timestamps for when an instrument or telescope has availability
        Meaning it has at least one schedulable instrument
    """
    serializer_class = AvailabilityHistorySerializer
    schema = None

    def get(self, request):
        instrument_id = request.GET.get('instrument_id')
        telescope_id = request.GET.get('telescope_id')
        site_id = request.GET.get('site_id')
        enclosure_id = request.GET.get('enclosure_id')
        # Start/end are optional parameters to cap what is returned
        start = request.GET.get('start')
        end = request.GET.get('end')
        try:
            if start:
                start = parse(start).replace(tzinfo=timezone.utc)
            else:
                start = datetime(2010, 1, 1, tzinfo=timezone.utc)
            if end:
                end = parse(end).replace(tzinfo=timezone.utc)
            else:
                end = timezone.now()
        except Exception:
            return HttpResponseBadRequest('The format used for the start/end parameters is not parseable')

        if instrument_id == None and (telescope_id == None or site_id == None or enclosure_id == None):
            return HttpResponseBadRequest('Must supply either instrument_id or site_id, enclosure_id, and telescope_id in params')
        availability = []
        # If use specifys a specific instrument_id, then use that
        if instrument_id:
            # Assume we only have a single instrument with that code
            instrument = Instrument.objects.filter(code=instrument_id).first()
            if not instrument:
                return HttpResponseNotFound(f'No instrument found with code {instrument_id}')
            availability = build_instrument_availability_history(instrument)

        # Otherwise if a telescope_id is provided, check accross all instruments on that telescope
        if telescope_id and enclosure_id and site_id:
            telescope = Telescope.objects.filter(code=telescope_id, enclosure__code=enclosure_id, enclosure__site__code=site_id).first()
            if not telescope:
                return HttpResponseNotFound(f'No telescope found with code {site_id}.{enclosure_id}.{telescope_id}')
            availability = build_telescope_availability_history(telescope)

        availability_data = {'availability_intervals': []}
        for interval in availability:
            if interval[0] <= end and interval[1] >= start:
                availability_data['availability_intervals'].append({
                    'start': interval[0].replace(microsecond=0, tzinfo=None).isoformat(),
                    'end': interval[1].replace(microsecond=0, tzinfo=None).isoformat()
                })
        return JsonResponse(data=availability_data)
