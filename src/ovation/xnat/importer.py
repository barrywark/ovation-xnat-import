'''
Copyright (c) 2012 Physion Consulting, LLC. All rights reserved.
'''

from ovation.xnat.exceptions import OvationXnatException
from time import mktime, strptime
from datetime import datetime
import ovation.api as api
from ovation.xnat.util import  xnat_api_pause, xnat_api, atomic_attributes, entity_keywords, iterate_entity_collection, to_joda_datetime


class XnatImportError(OvationXnatException):
    pass

def import_projects(dsc, xnat):
    """
    Import all projects from the given XNAT REST API Interface
    """

    _init_xnat(xnat)

    for project in xnat.select.projects():
        import_project(dsc, project)



DATATYPE_PROPERTY = 'xnat:datatype'
DATE_FORMAT = '%Y-%m-%d'
DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S.%f'


def import_project(dsc, xnatProject, timezone='UTC', importProjectTree=True):
    """
    Import a single XNAT project.

    """

    projectID = xnat_api(xnatProject.id)
    name = xnat_api(xnatProject.attrs.get,'xnat:projectData/name')
    purpose = xnat_api(xnatProject.attrs.get, 'xnat:projectData/description')

    # Find the earliest session date in the project
    xnat = xnatProject._intf
    sessionTypes = xnat.inspect.experiment_types()
    if len(sessionTypes) == 0:
        sessionTypes = ('xnat:mrSessionData', 'xnat:ctSessionData')
        #raise XnatImportError("No session types defined in database")

    minSessionDate = None
    for sessionType in sessionTypes:
        columns = (sessionType + '/DATE', sessionType + '/PROJECT')
        xnat_api_pause()
        query = xnat.select(sessionType, columns=columns).where([(sessionType + '/Project', '=', projectID), 'AND'])
        sessionDates = [ datetime.fromtimestamp(mktime(strptime(row['date'], DATE_FORMAT))) for
                         row in
                         query if len(row['date']) > 0]
        if len(sessionDates) > 0:
            for sd in sessionDates:
                if minSessionDate is not None:
                    if sd < minSessionDate:
                        minSessionDate = sd
                else:
                    minSessionDate = sd


    if minSessionDate is not None:
        startTime = to_joda_datetime(minSessionDate, timezone)
    else:
        startTime = api.datetime()

    ctx = dsc.getContext()
    project = ctx.insertProject(name,
        purpose,
        startTime)

    _import_entity_common(project, xnatProject)

    if importProjectTree:
        for s in iterate_entity_collection(xnatProject.subjects):
            src = import_source(dsc, s)
            for session in iterate_entity_collection(s.experiments):
                import_session(dsc, src, project, session)

    return project

def import_session(dsc, src, project, xnatSession):
    pass


def _add_entity_keywords(ovEntity, xnatEntity):
    try:
        tags = entity_keywords(xnatEntity)
        for k in tags:
            ovEntity.addTag(k)
    except OvationXnatException:
        pass

def _add_entity_attributes(ovEntity, xnatEntity):
    attributes = atomic_attributes(xnatEntity)
    for (k, v) in attributes.iteritems():
        ovEntity.addProperty(k, v)

def _import_entity_common(ovEntity, xnatEntity):
    _add_entity_attributes(ovEntity, xnatEntity)
    dtype = xnatEntity.datatype()
    ovEntity.addProperty(DATATYPE_PROPERTY, dtype)
    _add_entity_keywords(ovEntity, xnatEntity)

def import_source(dsc, xnatSubject):
    """
    Insert a single XNAT subject
    """

    sourceID = xnat_api(xnatSubject.id)

    ctx = dsc.getContext()

    r = ctx.sourceForInsertion([sourceID], ['xnat:subjectURI'], [xnatSubject._uri])
    src = r.getSource()

    if r.isNew():
        _import_entity_common(src, xnatSubject)

    return src


def _init_xnat(xnat):
    xnat.cache.clear()
    xnat.manage.schemas.add('xnat.xsd')
    xnat.manage.schemas.add('fs.xsd')

