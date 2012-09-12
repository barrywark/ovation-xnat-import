'''
Copyright (c) 2012 Physion Consulting, LLC. All rights reserved.
'''
import os
from pyxnat.core.errors import DatabaseError
import ovation
import logging
from ovation.xnat.exceptions import OvationXnatException
#noinspection PyUnresolvedReferences
from time import mktime, strptime
#noinspection PyUnresolvedReferences
from datetime import datetime
import ovation.api as api
from ovation.xnat.util import  xnat_api_pause, xnat_api, atomic_attributes, entity_keywords, iterate_entity_collection, to_joda_datetime, dict2map


_log = logging.getLogger(__name__)

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
DATETIMESHORT_FORMAT = '%Y-%m-%d %H:%M:%S'


def import_project(dsc, xnatProject, timezone='UTC', importProjectTree=True):
    """
    Import a single XNAT project.

    """

    projectID = xnat_api(xnatProject.id)
    _log.info('Importing project: ' + projectID)
    name = xnat_api(xnatProject.attrs.get,'xnat:projectData/name')
    purpose = xnat_api(xnatProject.attrs.get, 'xnat:projectData/description')

    if not purpose:
        purpose = "<None>"

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
        _log.info("  importing project tree...")
        subjectIDs = xnat_api(xnatProject.subjects().get)
        for s in subjectIDs:
            import_subject(dsc, xnat_api(xnatProject.subject, s), timezone=timezone)

    return project

def import_session(dsc, src, project, xnatSession, timezone='UTC'):
    if project == None:
        return

    try:
        attrs = xnatSession.attrs
        dtype = xnat_api(xnatSession.datatype)
        #print(dtype)
        _log.info('    Importing session: ' + dtype)

        dateString = xnat_api(attrs.get, dtype + '/date')
        timeString = xnat_api(attrs.get, dtype + '/time')
        purpose = xnat_api(attrs.get, dtype + '/note')
        if not purpose: #None or len 0
            purpose = 'XNAT experiment ' + xnatSession._uri

        dateTimeString = dateString + ' ' + timeString
        if timeString:
            format = DATETIME_FORMAT if timeString.find('.') > 0 else DATETIMESHORT_FORMAT
        else:
            format = DATE_FORMAT

        startTime = datetime.fromtimestamp(mktime(strptime(dateTimeString, format)))

        exp = project.insertExperiment(purpose, to_joda_datetime(startTime, timezone))
        _import_entity_common(exp, xnatSession)

        scanIDs = xnat_api(xnatSession.scans().get)
        for scanID in scanIDs:
            import_scan(dsc, src, exp, xnat_api(xnatSession.scan, scanID), timezone=timezone)

        return exp
    except DatabaseError, e:
        _log.exception("Unable to import session: " + e.message)
        return None

def import_scan(dsc, src, exp, xnatScan, timezone='UTC'):

    dtype = xnat_api(xnatScan.datatype)

    _log.info('      Importing scan: ' + dtype)
#    dateString = xnat_api(xnatScan.attrs.get, dtype + '/date')
#        timeString = xnat_api(xnatScan.attrs.get, dtype + '/parameters/scanTime')
#        dateTimeString = dateString + ' ' + timeString
#
#    if timeString:
#        format = DATETIME_FORMAT if timeString.find('.') > 0 else DATETIMESHORT_FORMAT
#    else:
#        format = DATE_FORMAT
#
#        startTime = to_joda_datetime(
#            datetime.fromtimestamp(mktime(strptime(dateTimeString, format))),
#                    timezone)


    startTime = exp.getStartTime()

    parentSession = xnat_api(xnatScan.parent)
    parentDtype = xnat_api(parentSession.datatype)
    scanAttrs = parentSession.attrs
    sessionScanner = xnat_api(scanAttrs.get, parentDtype + '/scanner')
    durationString = xnat_api(scanAttrs.get, parentDtype + '/duration')
    if durationString:
        duration = float(durationString)
    else:
        _log.warn("Scan duration is empty")
        duration = 1.0

    endTime = startTime.plusMillis(int(duration*1000))

    scanType = xnat_api(xnatScan.attrs.get, dtype + '/type')
    g = exp.insertEpochGroup(src, scanType, startTime, endTime)
    _import_entity_common(g, xnatScan, resources=False)

    try:
        parameterPairs = [(k, xnat_api(xnatScan.attrs.get, k)) for k in xnatScan.attrs() if k.startswith(dtype + '/parameters/')]
        paramDict = { k : v for (k,v) in parameterPairs}
    except DatabaseError, e:
        _log.exception("Unable to set parameters: " + e.message)
        paramDict = {}

    parameters = dict2map(paramDict)
    scannerParameters = parameters

    ovation = api.ovation_package()
    BYTE_DATATYPE = ovation.NumericDataType(ovation.NumericDataFormat.SignedFixedPointDataType, 1, ovation.NumericByteOrder.ByteOrderNeutral)

    for r in iterate_entity_collection(xnatScan.resources):
        _log.info("        Resource " + xnat_api(r.label))
        print("Resource...")
        # Insert one epoch group per resource group
        resourceGroup = g.insertEpochGroup(xnat_api(r.label),
                            g.getStartTime())

        for f in iterate_entity_collection(r.files):
            # Import one epoch per resource file
            e = resourceGroup.insertEpoch(
                g.getStartTime(),
                g.getEndTime(), #TODO
                scanType,
                parameters
            )

            url,uti = file_info(xnatScan._intf, f)
            _log.info("          File " + xnat_api(r.label))

            e.insertURLResponse(
                resourceGroup.getExperiment().externalDevice(sessionScanner, sessionScanner), #TODO
                scannerParameters,
                url,
                [1,1], # Shape
                BYTE_DATATYPE,
                'unknown', #TODO units
                ['x', 'y'],
                [1.0, 1.0], # TODO sampling rate
                ['pixels', 'pixels'], # TODO srate units
                uti
            )

    return g


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


def file_info(xnat, f):
    fileExt = os.path.splitext(f._uri)[-1].lstrip('.')
    #TODO: special cased
    if fileExt == 'dcm':
        uti = 'org.nema.dicom'
    else:
        uti = ovation.api.ovation_package().Resource.UTIForExtension(fileExt)
    url = xnat._server + f._uri
    return url, uti


def _insert_entity_resources(ovEntity, xnatEntity):
    xnat = xnatEntity._intf
    for rsrc in iterate_entity_collection(xnatEntity.resources):
        label = xnat_api(rsrc.label)
        for f in iterate_entity_collection(rsrc.files):

            url, uti = file_info(xnat, f)

            ovEntity.addURLResource(uti, xnat_api(f.label) + ' (' + label + ')', url)


def _import_entity_common(ovEntity, xnatEntity, resources=True):
    try:
        _add_entity_attributes(ovEntity, xnatEntity)
    except DatabaseError, e:
        _log.exception("Unable to set entity properties: " + e.message)

    dtype = xnat_api(xnatEntity.datatype)
    ovEntity.addProperty(DATATYPE_PROPERTY, dtype)

    try:
        _add_entity_keywords(ovEntity, xnatEntity)
    except DatabaseError, e:
        _log.exception("Unable to set entity properties: " + e.message)

    if(resources):
        _insert_entity_resources(ovEntity, xnatEntity)

def import_subject(dsc, xnatSubject, project=None, timezone='UTC'):
    """
    Insert a single XNAT subject
    """

    sourceID = xnat_api(xnatSubject.id)

    #print(sourceID)
    _log.info('  Importing subject: ' + sourceID)

    ctx = dsc.getContext()

    r = ctx.sourceForInsertion([sourceID], ['xnat:subjectURI'], [xnatSubject._uri])
    src = r.getSource()

    if r.isNew():
        _import_entity_common(src, xnatSubject)

    expIDs = xnat_api(xnatSubject.experiments().get)
    for experimentID in expIDs:
        import_session(dsc, src, project, xnat_api(xnatSubject.experiment, experimentID), timezone=timezone)

    return src


def _init_xnat(xnat):
    xnat.cache.clear()
    xnat.manage.schemas.add('xnat.xsd')
    xnat.manage.schemas.add('fs.xsd')

