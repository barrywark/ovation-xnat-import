'''
Copyright (c) 2012 Physion Consulting, LLC. All rights reserved.
'''

from ovation.xnat.importer import DATATYPE_PROPERTY
from nose.tools import istest
from ovation.xnat.test.OvationTestBase import OvationTestBase, subject_mock

class ImportingSessions(OvationTestBase):

    @istest
    def should_import_session_from_subject_as_experiments_with_one_epochgroup(self):
        subjectMock = subject_mock("1", "PROJECT_NAME")

        self.fail("implement")



    @istest
    def should_set_session_datatpe(self):
        self.fail("implement " + DATATYPE_PROPERTY)

    @istest
    def should_import_epochgroup_per_scan(self):
        self.fail("implement")

    @istest
    def should_import_epoch_per_file(self):
        """
        Should import files as URLResponses, not as Resources
        """

        self.fail("implement")
