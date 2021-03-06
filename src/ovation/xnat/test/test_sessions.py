'''
Copyright (c) 2012 Physion Consulting, LLC. All rights reserved.
'''
from ovation import api

from ovation.xnat.importer import DATATYPE_PROPERTY, import_subject
from nose.tools import istest
from ovation.xnat.test.OvationTestBase import OvationTestBase, subject_mock, patch_xnat_api

class ImportingSessions(OvationTestBase):

    @istest
    @patch_xnat_api
    def should_import_session_from_subject_as_experiments(self):
        xnatSubject = subject_mock("1", "PROJECT_NAME")

        ctx = self.dsc.getContext()
        project = ctx.insertProject('session_import', 'session_import', api.datetime())
        s = import_subject(self.dsc, xnatSubject, project=project)

        # Assertions
        self.assertGreaterEqual(len(xnatSubject.experiments().get()), 1)
        self.assertEqual(len(project.getExperiments()), len(xnatSubject.experiments().get()))


    @istest
    def should_set_session_datatype(self):
        xnatSubject = subject_mock("1", "PROJECT_NAME")

        s = import_subject(self.dsc, xnatSubject)

        for exp in s.getExperiments():
            self.assertNotNone(exp.getOwnerProperty(DATATYPE_PROPERTY))


