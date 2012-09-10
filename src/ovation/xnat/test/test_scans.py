'''
Copyright (c) 2012 Physion Consulting, LLC. All rights reserved.
'''

from nose.tools import istest
from ovation.xnat.test.OvationTestBase import OvationTestBase

class ImportingScans(OvationTestBase):

    @istest
    def should_import_epoch_per_file(self):
        """
        Should import files as URLResponses, not as Resources
        """

        self.fail("implement")

    @istest
    def should_set_scan_datatype(self):
        self.fail("implement")
#        xnatSubject = subject_mock("1", "PROJECT_NAME")
#        ctx = self.dsc.getContext()
#        project = ctx.insertProject('session_import', 'session_import', api.datetime())
#        s = import_subject(self.dsc, xnatSubject, project=project)
#
#        for exp in s.getExperiments():
#            for epochGroup in exp.getEpochGroups:
#                self.assertNotNone(epochGroup.getOwnerProperty(DATATYPE_PROPERTY))
#                for childGroup in epochGroup.getEpochGroups():
#                    self.assertNotNone(childGroup.getOwnerProperty(DATATYPE_PROPERTY))

