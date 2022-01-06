"""
Attributes
==============
Attribute types used for the model.

The types system provides a mechanism for serializing/un the data to/from JSON
structures and for capturing additional information about the model attributes.
"""
from __future__ import division, absolute_import, print_function, unicode_literals
import logging
from datetime import datetime, timedelta, tzinfo, date
from collections import namedtuple
from weakref import WeakKeyDictionary, WeakValueDictionary

import arrow
import pytz
from units.quantity import Quantity
import six

import stravalib.model

# Depending on the type of request, objects will be returned in meta,  summary or detailed representations. The
# representation of the returned object is indicated by the resource_state attribute.
# (For more info, see https://developers.strava.com/docs/reference/)

META = 1
SUMMARY = 2
DETAILED = 3


class Attribute(object):
    """
    Base descriptor class for a Strava model attribute.
    """
    _type = None

    def __init__(self, type_, resource_states=None, units=None):
        self.log = logging.getLogger('{0.__module__}.{0.__name__}'.format(self.__class__))
        self.type = type_
        self.resource_states = resource_states
        self.data = WeakKeyDictionary()
        self.units = units

    def __get__(self, obj, clazz):
        if obj is not None:
            # It is being called on an object (not class)
            # This can cause infinite loops, when we're attempting to get the resource_state attribute ...
            #if hasattr(clazz, 'resource_state') \
            #   and obj.resource_state is not None \
            #   and not obj.resource_state in self.resource_states:
            #    raise AttributeError("attribute required resource state not satisfied by object")
            return self.data.get(obj)
        else:
            # Rather than return the wrapped value, return the actual descriptor object
            return self

    def __set__(self, obj, val):
        if val is not None:
            self.data[obj] = self.unmarshal(val)
        else:
            self.data[obj] = None

    @property
    def type(self):
        return self._type

    @type.setter
    def type(self, v):
        self._type = v

    def marshal(self, v):
        """
        Turn this value into format for wire (JSON).

        (By default this will just return the underlying object; subclasses
        can override for specific behaviors -- e.g. date formatting.)
        """
        if isinstance(v, Quantity):
            return v.num
        else:
            return v

    def unmarshal(self, v):
        """
        Convert the value from parsed JSON structure to native python representation.

        By default this will leave the value as-is since the JSON parsing routines
        typically convert to native types. The exception may be date strings or other
        more complex types, where subclasses will override this behavior.
        """
        if self.units:
            # Note that we don't want to cast to type in this case!
            if not isinstance(v, Quantity):
                v = self.units(v)
        elif not isinstance(v, self.type):
            v = self.type(v)
        return v


class DateAttribute(Attribute):
    """
    """
    def __init__(self, resource_states=None):
        super(DateAttribute, self).__init__(date, resource_states=resource_states)

    def marshal(self, v):
        """

        :param v: The date object to convert.
        :type v: date
        :return:
        """
        return v.isoformat() if v else None

    def unmarshal(self, v):
        """
        Convert a date in "2012-12-13" format to a :class:`datetime.date` object.
        """
        if not isinstance(v, date):
            # 2012-12-13
            v = datetime.strptime(v, "%Y-%m-%d").date()
        return v


class TimestampAttribute(Attribute):
    """
    """
    def __init__(self, resource_states=None, tzinfo=pytz.utc):
        super(TimestampAttribute, self).__init__(datetime, resource_states=resource_states)
        self.tzinfo = tzinfo

    def marshal(self, v):
        """
        Serialize the timestamp to string.

        :param v: The timestamp.
        :type v: datetime
        :return: The serialized date time.
        """
        return v.isoformat() if v else None

    def unmarshal(self, v):
        """
        Convert a timestamp in "2012-12-13T03:43:19Z" format to a `datetime.datetime` object.
        """
        if not isinstance(v, datetime):
            if isinstance(v, six.integer_types):
                v = arrow.get(v)
            else:
                try:
                    # Most dates are in this format 2012-12-13T03:43:19Z
                    v = datetime.strptime(v, "%Y-%m-%dT%H:%M:%SZ")
                except ValueError:
                    # ... but not all.
                    v = arrow.get(v).datetime
            # Translate to specified TZ
            v = v.replace(tzinfo=self.tzinfo)

        return v


LatLon = namedtuple('LatLon', ['lat', 'lon'])


class LocationAttribute(Attribute):
    """
    """
    def __init__(self, resource_states=None):
        super(LocationAttribute, self).__init__(LatLon, resource_states=resource_states)

    def marshal(self, v):
        """
        Turn this value into format for wire (JSON).

        :param v: The lat/lon.
        :type v: LatLon
        :return: Serialized format.
        :rtype: str
        """
        return "{lat},{lon}".format(lat=v.lat, lon=v.lon) if v else None

    def unmarshal(self, v):
        """
        """
        if not isinstance(v, LatLon):
            v = LatLon(lat=v[0], lon=v[1]) if v else None
        return v


class TimezoneAttribute(Attribute):
    """
    """
    def __init__(self, resource_states=None):
        super(TimezoneAttribute, self).__init__(pytz.timezone, resource_states=resource_states)

    def unmarshal(self, v):
        """
        Convert a timestamp in format "America/Los_Angeles" or
        "(GMT-08:00) America/Los_Angeles" to
        a `pytz.timestamp` object.
        """
        if not isinstance(v, tzinfo):
            if ' ' in v:
                # (GMT-08:00) America/Los_Angeles
                tzname = v.split(' ', 1)[1]
            else:
                # America/Los_Angeles
                tzname = v
            v = pytz.timezone(tzname)
        return v

    def marshal(self, v):
        """
        Serialize time zone name.

        :param v: The timezone.
        :type v: tzdata
        :return: The name of the time zone.
        """
        return str(v) if v else None


class TimeIntervalAttribute(Attribute):
    """
    Handles time durations, assumes upstream int value in seconds.
    """
    def __init__(self, resource_states=None):
        super(TimeIntervalAttribute, self).__init__(int, resource_states=resource_states)

    def unmarshal(self, v):
        """
        Convert the value from parsed JSON structure to native python representation.

        By default this will leave the value as-is since the JSON parsing routines
        typically convert to native types. The exception may be date strings or other
        more complex types, where subclasses will override this behavior.
        """
        if not isinstance(v, timedelta):
            if isinstance(v, six.text_type) or isinstance(v, six.binary_type):
                h,m,s = v.split(':')
                v = timedelta(seconds = int(h)*3600 + int(m)*60 + int(s))
            else:
                v = timedelta(seconds=v)
        return v

    def marshal(self, v):
        """
        Serialize native python timedelta object to seconds as int.

        :param v: time interval.
        :type v: timedelta
        :return: time interval in seconds as int.
        """
        if isinstance(v, timedelta):
            return v.seconds
        else:
            return str(v) if v else None

class ChoicesAttribute(Attribute):
    """
    Attribute where there are several choices the attribute may take.

    Allows conversion from the API value to a more helpful python value.
    """
    def __init__(self, *args, **kwargs):
        self.choices = kwargs.pop("choices", {})
        super(ChoicesAttribute, self).__init__(*args, **kwargs)

    def marshal(self, v):
        """
        Turn this value into API format.

        Do a reverse dictionary lookup on choices to find the original value. If
        there are no keys or too many keys for now we raise a NotImplementedError
        as marshal is not used anywhere currently. In the future we will want to
        fail gracefully.
        """
        if v:
            orig = [i for i in self.choices if self.choices[i] == v]
            if len(orig) == 1:
                return orig[0]
            elif len(orig) == 0:
                # No such choice
                raise NotImplementedError("No such reverse choice {0} for field {1}.".format(v, self))
            else:
                # Too many choices. We could return one possible choice (e.g. orig[0]).
                raise NotImplementedError("Too many reverse choices {0} for value {1} for field {2}".format(orig, v, self))

    def unmarshal(self, v):
        """
        Convert the value from Strava API format to useful python representation.

        If the value does not appear in the choices attribute we log an error rather
        than raising an exception as this may be caused by a change to the API upstream
        so we want to fail gracefully.
        """
        try:
            return self.choices[v]
        except KeyError:
            self.log.warning("No such choice {0} for field {1}.".format(v, self))
            # Just return the value from the API
            return v


class EntityAttribute(Attribute):
    """
    Attribute for another entity.
    """
    _lazytype = None

    def __init__(self, *args, **kwargs):
        super(EntityAttribute, self).__init__(*args, **kwargs)
        self.bind_clients = WeakKeyDictionary()

    @property
    def type(self):
        if self._lazytype:
            clazz = getattr(stravalib.model, self._lazytype)
        else:
            clazz = self._type
        return clazz

    @type.setter
    def type(self, v):
        if isinstance(v, (six.text_type, six.binary_type)):
            # Supporting lazy class referencing
            self._lazytype = v
        else:
            self._type = v

    def __set__(self, obj, val):
        if val is not None:
            # If the "owning" object has a bind_client set, we want to pass that
            # down into the objects we are deserializing here
            self.data[obj] = self.unmarshal(val, bind_client=getattr(obj, 'bind_client', None))
        else:
            self.data[obj] = None

    def marshal(self, v):
        """
        Turn an entity into a dictionary.

        :param v: The entity to serialize.
        :type v: stravalib.model.BaseEntity
        :return: Dictionary of attributes
        :rtype: Dict[str, Any]
        """
        return v.to_dict() if v else None

    def unmarshal(self, value, bind_client=None):
        """
        Cast the specified value to the entity type.
        """
        #self.log.debug("Unmarshall {0!r}: {1!r}".format(self, value))
        if not isinstance(value, self.type):
            o = self.type()
            if bind_client is not None and hasattr(o.__class__, 'bind_client'):
                o.bind_client = bind_client

            if isinstance(value, dict):
                for (k, v) in value.items():
                    if not hasattr(o.__class__, k):
                        self.log.warning("Unable to set attribute {0} on entity {1!r}".format(k, o))
                    else:
                        #self.log.debug("Setting attribute {0} on entity {1!r}".format(k, o))
                        setattr(o, k, v)
                value = o
            else:
                raise Exception("Unable to unmarshall object {0!r}".format(value))
        return value


class EntityCollection(EntityAttribute):

    def marshal(self, values):
        """
        Turn a list of entities into a list of dictionaries.

        :param values: The entities to serialize.
        :type values: List[stravalib.model.BaseEntity]
        :return: List of dictionaries of attributes
        :rtype: List[Dict[str, Any]]
        """
        if values is not None:
            return [super(EntityCollection, self).marshal(v) for v in values]

    def unmarshal(self, values, bind_client=None):
        """
        Cast the list.
        """
        if values is not None:
            return [super(EntityCollection, self).unmarshal(v, bind_client=bind_client) for v in values]
