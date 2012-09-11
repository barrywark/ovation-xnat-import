'''
Copyright (c) 2012 Physion Consulting, LLC
'''
import functools
import pyxnat

__author__ = 'barry'

from pyxnat import Interface
from ovation.xnat.importer import import_project
from mock import MagicMock, patch, Mock

import unittest
import os
import exceptions

from socket import gethostname

import ovation.api as api

from ovation.xnat.test.utils import create_local_database, clean_local_database

# Environment keys for testing
CONNECTION_PATH_KEY = "OVATION_CONNECTION_FILE"
OVATION_FDID_KEY = "OVATION_TEST_FDID"
OVATION_TEST_JAR_PATH_KEY = "OVATION_TEST_JAR_PATH"

class OvationTestException(exceptions.StandardError):
    pass

class OvationTestBase(unittest.TestCase):

    def _import_first_project(self):
        self.xnat = self._xnat_connection()
        xnatProject = self.xnat.select.project('IGT_FMRI_NEURO')
        projectURI = import_project(self.dsc, xnatProject, importProjectTree=True).getURI()
        return (xnatProject,projectURI)

    def _xnat_connection(self):
        xnat = Interface(os.environ["XNAT_URL"],
            os.environ["XNAT_USER"],
            os.environ["XNAT_PASSWORD"])
        xnat.cache.clear()
        xnat.manage.schemas.add("xnat.xsd")
        xnat.manage.schemas.add("fs.xsd")

        return xnat

    def setUp(self):
        api.initialize(extra_jars=(os.environ[OVATION_TEST_JAR_PATH_KEY],os.environ[OVATION_TEST_JAR_PATH_KEY]))

        if not CONNECTION_PATH_KEY in os.environ:
            raise OvationTestException("OVATION_CONNECTION_FILE not defined in the test environment")

        self.connection_file_path = os.environ[CONNECTION_PATH_KEY]

        if not os.path.exists(self.connection_file_path):
            if 'OVATION_LOCK_SERVER' in os.environ:
                host = os.environ['OVATION_LOCK_SERVER']
            else:
                host = gethostname()
                if host == 'localhost':
                    host = '127.0.0.1'

            create_local_database(self.connection_file_path,
                host=host,
                federatedDatabaseID=os.environ.get(OVATION_FDID_KEY, None))

        test = api.ovation_package().test

        self.test_manager = test.TestManager(self.connection_file_path,
            'Institution',
            'Lab',
            'crS9RjS6wJgmZkJZ1WRbdEtIIwynAVmqFwrooGgsM7ytyR+wCD3xpjJEENey+b0GVVEgib++HAKh94LuvLQXQ2lL2UCUo75xJwVLL3wmd21WbumQqKzZk9p6fkHCVoiSxgon+2RaGA75ckKNmUVTeIBn+QkalKCg9p1P7FbWqH3diXlAOKND2mwjI8V4unq7aaKEUuCgdU9V/BjFBkoytG8FzyBCNn+cBUNTByYy7RxYxH37xECZJ6/hG/vP4QjKpks9cu3yQL9QjXBQIizrzini0eQj62j+QzCSf0oQg8KdIeZHuU+ZSZZ1pUHLYiOiQWaOL9cVPxqMzh5Q/Zvu6Q==',
            'TestUser',
            'TestPassword')

        self.dsc = self.test_manager.setupDatabase()


    def tearDown(self):
        clean_local_database(self.test_manager)

def call_fn(fn, *args, **kwargs):
    return fn(*args, **kwargs)

def no_op():
    pass

def patch_xnat_api(func):
    """
    Patch xnat_api pausing calls
    """
    @functools.wraps(func)
    @patch("ovation.xnat.util.xnat_api", call_fn)
    @patch("ovation.xnat.util.xnat_api_pause", no_op)
    def wrapper(*args):
        func(*args)

    return wrapper

def _mock_entity(attrs):
    m = MagicMock()
    _set_mock_attrs(attrs, m)

    return m


def session_mock(baseURI=None, xnat=None):
    expAttrs = {'xnat:mrSessionData/date': '2012-02-03',
                'xnat:mrSessionData/time': '08:13:23.2',
                'xnat:mrSessionData/duration': '12',
                'xnat:mrSessionData/scanner': 'MR Scanner',
                }

    exp1 = _mock_entity(expAttrs)
    exp1.datatype = Mock(side_effect=return_collection('xnat:mrSessionData'))
    exp1.id = Mock(return_value='1')

    if xnat is None:
        xnat = _set_mock_intf(exp1)
    exp1._intf = xnat
    _add_mock_resource_files(xnat, exp1)

    if baseURI is None:
        baseURI = xnat._server

    exp1._uri = baseURI + '/experiments/' + exp1.id()

    scanAttrs = {'xnat:mrScanData/date': '2012-02-03',
                'xnat:mrScanData/time': '08:13:23.2',
                'xnat:mrScanData/parameters/scanTime' : '08:13:23.2',
                'xnat:mrScanData/type': 'Some Scan Type',
                'xnat:mrScanData/parameters/voxelRes/units' : 'cm',
                'xnat:mrScanData/parameters/voxelRes/x' : 0.1,
                'xnat:mrScanData/parameters/voxelRes/y' : 0.2,
                'xnat:mrScanData/parameters/voxelRes/z' : 0.3}

    scan = _mock_entity(scanAttrs)
    _set_mock_intf(scan)
    scan.datatype = Mock(side_effect=return_collection('xnat:mrScanData'))
    scan.parent = Mock(return_value = exp1)
    scan.id = Mock(return_value="1")
    _add_mock_resource_files(xnat, scan)

    exp1.scans = Mock(side_effect=return_collection((scan,)))

    return exp1


def subject_mock(id, projectID):
    s = MagicMock(name='subject', spec=pyxnat.core.resources.Subject)

    xnat = _set_mock_intf(s)
    s.id = Mock(return_value=id)
    s.datatype = Mock(return_value='xnat:subjectData')
    s._uri = '/subjects/' + id
    attrs = {
        'xnat:subjectData/project' : projectID
    }
    _set_mock_attrs(attrs, s)

    # Resources

    _add_mock_resource_files(xnat, s)

    #Sessions
    exp1 = session_mock(baseURI=s._uri, xnat=xnat)

    sessions = (exp1,)

    s.experiments = Mock(side_effect=return_collection(sessions))

    return s


def return_collection(values):
    while True:
        yield values

def _set_mock_intf(mockEntity):
    xnat = MagicMock(name='xnat')
    xnat._server = 'http://my.xnat'

    mockEntity._intf = xnat

    return xnat

def _set_mock_attrs(attrs_values, mockEntity):
    mockEntity.mock_add_spec(['attrs'])
    if not hasattr(mockEntity, 'attrs'):
        mockEntity.attrs = MagicMock()

    mockEntity.attrs.get.side_effect = attrs_values.get
    mockEntity.attrs.side_effect = return_collection(attrs_values.keys())


def _add_mock_resource_files(xnat, mockEntity):
    file1URI = '/file.dcm'
    file1 = Mock()
    #file1.get = Mock(side_effect=return_collection(xnat._server + file1URI))
    file1._uri = file1URI
    file1.label = Mock(side_effect=return_collection('file.dcm'))

    file2URI = '/file2.dcm'
    file2 = Mock()
    #file2.get = Mock(side_effect=return_collection(xnat._server + file2URI))
    file2._uri = file2URI
    file2.label = Mock(side_effect=return_collection('file2.dcm'))

    files = (file1, file2)

    rsrcMock = Mock()
    _set_mock_intf(rsrcMock)
    rsrcMock.label = Mock(side_effect=return_collection('DICOM'))
    rsrcMock.files = Mock(side_effect=return_collection(files))

    resources = (rsrcMock,)
    mockEntity.resources = Mock(side_effect=return_collection(resources))


def project_mock(projectName='PROJECT_NAME'):
    projectMock = MagicMock(name='xnatProject', spec=pyxnat.core.resources.Project)

    projectMock.id = Mock(return_value=projectName)

    projectMock._uri = '/projects/' + projectName

    xnat = _set_mock_intf(projectMock)

    # xnat.inspect.experiment_types
    xnat.inspect.experiment_types.return_value = ('xnat:mrSessionData', 'xnat:ctSessionData')
    # xnat.select().where()
    sessionDates = [
        {'date': '2012-01-01', 'project': 'PROJECT2'},
        {'date': '2012-02-02', 'project': 'PROJECT2'}
    ]
    select = xnat.select
    where = select.return_value.where
    where.return_value = sessionDates

    # project attrs
    attrs = {'xnat:projectData/name': projectName,
             'xnat:projectData/description': 'PROJECT_DESCRIPTION',
             'xnat:projecdtData/keywords': 'TAG1, TAG2',
    }
    _set_mock_attrs(attrs, projectMock)

    # Datatype
    projectMock.datatype = Mock(return_value='xnat:projectData')

    # Subjects
    subjects = [subject_mock('1', projectMock.id()), subject_mock('2', projectMock.id())]
    projectMock.subjects = Mock(side_effect=return_collection(subjects))

    # Resources
    _add_mock_resource_files(xnat, projectMock)

    return projectMock


def mock_project_for_import(func):
    projectMock = project_mock()

    @functools.wraps(func)
    def wrapper(*args):
        args = list(args)
        args.append(projectMock)
        func(*args)

    return wrapper


