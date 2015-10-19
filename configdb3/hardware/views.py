from django.http import HttpResponse
from .models import Site, Telescope, Camera, FilterWheel
from django.views.generic import TemplateView


class IndexView(TemplateView):
    template_name = 'hardware/index.html'

    def get_context_data(self, **kwargs):
        context = super(IndexView, self).get_context_data(**kwargs)
        context['site_count'] = Site.objects.count()
        context['telescope_count'] = Telescope.objects.count()
        context['camera_count'] = Camera.objects.count()
        context['filterwheel_count'] = FilterWheel.objects.count()
        return context


def camera_mappings_dict():
    data = {"cameras": []}
    for site in Site.objects.filter(active=True):
        for enclosure in site.enclosure_set.filter(active=True):
            for telescope in enclosure.telescope_set.filter(active=True):
                for instrument in telescope.instrument_set.filter(active=True):
                    binning = ','.join([mode.binning_str for mode in instrument.science_camera.camera_type.mode_set.all()])
                    data['cameras'].append({
                        'site': site.code,
                        'observatory': enclosure.code,
                        'telescope': telescope.code,
                        'name': instrument.science_camera.code,
                        'cameratype': instrument.science_camera.camera_type.name,
                        'size': instrument.science_camera.camera_type.size,
                        'plate_scale': instrument.science_camera.camera_type.pscale,
                        'binning': binning,
                        'std_binning': instrument.science_camera.camera_type.default_mode.binning_str,
                        'overhead': instrument.science_camera.camera_type.default_mode.overhead / 1000, # in seconds
                        'autoguider': instrument.autoguider_camera.code,
                        'autoguider_type': instrument.autoguider_type,
                        'filters': instrument.science_camera.filter_wheel.filters,

                        })

            return data


def camera_mappings(request):
    data = camera_mappings_dict()
    lines = [('# Site  Observatory  Telescope  Camera    CameraType                    Size(arcmin)   '
              'PScale("/pix;1x1)   BinningAvailable    Std.Binning  Overhead(fullframe,1x1) '
              'Autoguider AutoguiderType  Filters')]
    for c in data['cameras']:
        lines.append(('  {site: <6}{observatory: <13}{telescope: <11}{name: <10}{cameratype: <30}'
                      '{size: <15}{plate_scale: <20}{binning: <20}{std_binning: <13}{overhead: <24}'
                      '{autoguider: <11}{autoguider_type: <16}{filters: <10}'
                      ).format(
            site=c['site'],
            observatory=c['observatory'],
            telescope=c['telescope'],
            name=c['name'],
            cameratype=c['cameratype'],
            size=c['size'],
            plate_scale=c['plate_scale'],
            binning=c['binning'],
            std_binning=c['std_binning'],
            overhead='{}sec'.format(c['overhead']),
            autoguider=c['autoguider'],
            autoguider_type=c['autoguider_type'],
            filters=c['filters'],
            )
        )

    return HttpResponse("\n".join(str(x) for x in lines), content_type="text/plain")
