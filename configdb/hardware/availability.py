
from time_intervals.intervals import Intervals
from reversion.models import Version
from django.utils import timezone

from configdb.hardware.models import Instrument


# This is here for legacy compatibility with old configdb Versions that stored the state as a number
STATE_MAPPING = {
    '0': 'DISABLED',
    '10': 'MANUAL',
    '20': 'COMMISSIONING',
    '25': 'STANDBY',
    '30': 'SCHEDULABLE'
}


def state_conversion(version):
    """ For legacy compatibility with older numeric styled states """
    return STATE_MAPPING.get(version.field_dict['state'], version.field_dict['state'])


def build_availability_history(instance, initial, state_function, comparator):
    """ Utility method builds a set of availability windows using the reversion Version set for the object.
        This generic method takes in the initial value for the field you are using as the "state", as well
        as a function that retrieves the "state" from the version field_dict, and a value to compare said
        "state" to to see if you are "in" that "state".
    """
    availability = []
    versions = Version.objects.get_for_object(instance)
    current_state = initial
    current_time = timezone.now()
    if current_state == comparator:
        is_in_state = True
        state_start_time = current_time
        state_end_time = current_time
    else:
        is_in_state = False
        state_start_time = None
        state_end_time = None
    # Versions are in reverse time order, latest to earliest
    for version in versions:
        state = state_function(version)
        if state == current_state:
            if is_in_state:
                state_start_time = version.field_dict['modified']
        else:
            if is_in_state:
                availability.append((state_start_time, state_end_time))
                is_in_state = False
            elif state == comparator:
                is_in_state = True
                state_start_time = version.field_dict['modified']
                state_end_time = current_time
        current_time = version.field_dict['modified']
        current_state = state
    # If we've gone through all versions and the last was in_state, then add the last window
    if is_in_state:
        availability.append((state_start_time, state_end_time))
    return availability


def build_instrument_availability_history(instrument):
    """ Utility method to build a set of availability windows for an instrument given its version history
        Outputs a list of tuples of (start, end) times for intervals when the instrument is schedulable
    """
    return build_availability_history(instrument, instrument.state, state_conversion, Instrument.SCHEDULABLE)


def build_telescope_availability_history(telescope):
    """ Utility method to build a set of availability windows for an telescope given its version history.
        A telescope is considered available if it had any instruments in the SCHEDULABLE state during a time interval.
        Outputs a list of tuples of (start, end) times for intervals when the telescope is available.
    """
    instrument_intervals = []
    for instrument in telescope.instrument_set.all():
        instrument_intervals.append(Intervals(build_instrument_availability_history(instrument)))
    combined_instrument_availability = Intervals().union(instrument_intervals)

    # We can also check the telescope active state history and enforce that as well
    telescope_availability = build_availability_history(
        telescope, telescope.active, lambda version: version.field_dict['active'], True
    )
    telescope_intervals = Intervals(telescope_availability)
    # Reverse the intervals so the latest is first
    return reversed(combined_instrument_availability.intersect([telescope_intervals]).toTupleList())
