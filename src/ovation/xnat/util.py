'''
Copyright (c) 2012 Physion Consulting, LLC. All rights reserved.
'''
import logging

from ovation import api

__author__ = 'barry'

#noinspection PyUnresolvedReferences
import time

_log = logging.getLogger(__name__)

def xnat_api(fn, *args, **kwargs):
    xnat_api_pause()
    return fn(*args, **kwargs)



def xnat_api_pause(seconds=1):
    time.sleep(seconds)

def iterate_entity_collection(fn):
    for e in fn():
        xnat_api_pause()
        yield e

def entity_keywords(e):
    datatype = xnat_api(e.datatype)
    attr = datatype + '/keywords'
    if attr in e.attrs():
        return xnat_api(e.attrs.get, attr).split()
    else:
        return []

def entity_resource_files(e):
    for rsrc in iterate_entity_collection(e.resources):
        for f in iterate_entity_collection(rsrc.files):
            yield f


def dict2map(d):
    m = api.jpype.java.util.HashMap()
    for (k,v) in d.iteritems():
        m.put(k,v)

    return m

def is_atomic_attribute(e, attr):
    return _is_atomic_attribute_in_attrs(attr, e.attrs())

def _is_atomic_attribute_in_attrs(attr, attrs):
    if attr not in attrs:
        return False

    comps = _attr_comps(attr)
    if len(comps) > 1:
        return False

    if len([x for x in attrs if x.startswith(attr)]) > 1:
        return False

    return True

def _attr_comps(attr):
    return attr.split('/')[1:]

def atomic_attributes(e):
    try:
        keys = xnat_api(e.attrs)
        attrs = e.attrs

        result = {}
        for key in keys:
            if is_atomic_attribute(e, key):
                try:
                    value = xnat_api(attrs.get, key)
                    result[key] = value
                except StandardError, e:
                    _log.exception('Unable to retrieve attributes: ' + e.message)
                except StopIteration:
                    _log.exception('Unable to retrieve attributes: StopIteration')

        return result
    except StandardError, e:
        _log.exception(e.message)
        return {}

def to_joda_datetime(date, timezone):
    return api.datetime(date.year,
        date.month,
        date.day,
        date.hour,
        date.minute,
        date.second,
        int(date.microsecond / 1000),
        api.timezone_with_id(timezone))
