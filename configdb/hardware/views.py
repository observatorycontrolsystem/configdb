from django.views.generic import TemplateView

from .models import Site, Telescope, Camera, Instrument, OpticalElementGroup, GenericModeGroup


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
