'''
Copyright (c) 2012 Physion Consulting, LLC. All rights reserved.
'''

from ovation.xnat.util import xnat_api, entity_keywords, is_atomic_attribute, entity_resource_files
from nose.tools import  istest, eq_
from ovation.xnat.test.OvationTestBase import OvationTestBase, mock_project_for_import, patch_xnat_api, subject_mock, project_mock
from ovation.xnat.importer import import_subject, import_project


class ImportingEntityMetadata(OvationTestBase):


    @istest
    @patch_xnat_api
    @mock_project_for_import
    def should_import_keywords(self, xnatProject):

        project = import_project(self.dsc, xnatProject, importProjectTree=False)

        tags = entity_keywords(xnatProject)
        actualTags = project.getTags()
        for tag in tags:
            self.assertIn(tag, actualTags)

    @istest
    @patch_xnat_api
    @mock_project_for_import
    def should_import_resources(self, xnatProject):
        project = import_project(self.dsc, xnatProject, importProjectTree=False)
        xnat = xnatProject._intf

        files = entity_resource_files(xnatProject)
        for f in files:
            fileURI = xnat._server + f._uri
            self.assertIsNotNone(project.getResource(fileURI))

    @istest
    def should_import_attrs(self):

        projectName = 'PROJECT_NAME'
        xnatSubject = subject_mock('1', project_mock(projectName))
        subject = import_subject(self.dsc, xnatSubject)

        attributes = xnat_api(xnatSubject.attrs)
        attrs = xnatSubject.attrs
        for attr in attributes:
            if is_atomic_attribute(xnatSubject, attrs):
                value = xnat_api(attrs.get, attr)
                eq_(subject.getOwnerProperty(attr), value)

