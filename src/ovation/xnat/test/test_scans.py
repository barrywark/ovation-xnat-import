'''
Copyright (c) 2012 Physion Consulting, LLC. All rights reserved.
'''

from nose.tools import istest
from ovation import api
from ovation.xnat.importer import  import_session, DATATYPE_PROPERTY
from ovation.xnat.test.OvationTestBase import OvationTestBase, patch_xnat_api, session_mock

class ImportingScans(OvationTestBase):

    @istest
    @patch_xnat_api
    def should_insert_epochgroup_per_resource_group(self):
        """
        Should import files as URLResponses, not as Resources
        """
        ctx = self.dsc.getContext()
        src = ctx.insertSource('test')
        project = ctx.insertProject('test', 'test', api.datetime())

        xnatSession = session_mock()
        exp = import_session(self.dsc, src, project, xnatSession)

        for scanID in xnatSession.scans().get():
            s = xnatSession.scan(scanID)
            id = s.attrs.get('xnat:mrScanData/type')
            g = exp.getEpochGroupsWithLabel(id).iterator().next()
            for r in s.resources():
                label = r.label()
                self.assertEqual(len(g.getChildren(label)), 1)


    @istest
    @patch_xnat_api
    def should_import_epoch_per_file(self):
        """
        Should import files as URLResponses, not as Resources
        """
        ctx = self.dsc.getContext()
        src = ctx.insertSource('test')
        project = ctx.insertProject('test', 'test', api.datetime())

        xnatSession = session_mock()
        exp = import_session(self.dsc, src, project, xnatSession)
        sessionType = xnatSession.datatype()
        sessionScanner = xnatSession.attrs.get(sessionType + '/scanner')

        for scanID in xnatSession.scans().get():
            s = xnatSession.scan(scanID)
            id = s.attrs.get('xnat:mrScanData/type')
            g = exp.getEpochGroupsWithLabel(id).iterator().next()
            for r in s.resources():
                label = r.label()
                typeGroup = g.getChildren(label)[0]
                self.assertEqual(typeGroup.getEpochCount(), len(r.files()))

                for epoch in typeGroup.getEpochs():
                    self.assertEqual(len(epoch.getResponseNames()), 1)
                    r = epoch.getResponse(sessionScanner)
                    self.assertIsNotNone(r)

    @istest
    @patch_xnat_api
    def should_import_epochgroup_per_scan_with_scantype_as_label(self):
        ctx = self.dsc.getContext()
        project = ctx.insertProject('session_import', 'session_import', api.datetime())
        src = ctx.insertSource('test')

        xnatSession = session_mock()

        exp = import_session(self.dsc, src, project, xnatSession)

        self.assertGreaterEqual(xnatSession.scans().get(), 1)
        self.assertEqual(len(exp.getEpochGroups()), len(xnatSession.scans().get()))

    @istest
    @patch_xnat_api
    def should_set_session_id_as_epochgroup_label(self):
        ctx = self.dsc.getContext()
        project = ctx.insertProject('session_import', 'session_import', api.datetime())
        src = ctx.insertSource('test')

        xnatSession = session_mock()

        exp = import_session(self.dsc, src, project, xnatSession)

        for scanID in xnatSession.scans().get():
            scan = xnatSession.scan(scanID)
            id = scan.attrs.get('xnat:mrScanData/type')
            self.assertEqual(len(list(exp.getEpochGroupsWithLabel(id).iterator())), 1)


    @istest
    @patch_xnat_api
    def should_import_scan_parameters_as_epoch_parameters(self):
        ctx = self.dsc.getContext()
        src = ctx.insertSource('test')
        project = ctx.insertProject('test', 'test', api.datetime())

        xnatSession = session_mock()
        exp = import_session(self.dsc, src, project, xnatSession)
        sessionType = xnatSession.datatype()
        sessionScanner = xnatSession.attrs.get(sessionType + '/scanner')

        for epoch in exp.getEpochsIterable().iterator():
            parameters = epoch.getProtocolParameters()
            self.assertGreater(parameters.size(), 0)

    @istest
    @patch_xnat_api
    def should_import_scanner_perameters_as_device_parameters(self):
        ctx = self.dsc.getContext()
        src = ctx.insertSource('test')
        project = ctx.insertProject('test', 'test', api.datetime())

        xnatSession = session_mock()
        exp = import_session(self.dsc, src, project, xnatSession)
        sessionType = xnatSession.datatype()
        sessionScanner = xnatSession.attrs.get(sessionType + '/scanner')

        for epoch in exp.getEpochsIterable().iterator():
            r = epoch.getResponse(sessionScanner)
            self.assertIsNotNone(r)
            parameters = r.getDeviceParameters()
            self.assertIsNotNone(parameters)
            self.assertGreater(parameters.size(), 0)

    @istest
    @patch_xnat_api
    def should_set_scan_datatype(self):

        ctx = self.dsc.getContext()
        src = ctx.insertSource('test')
        project = ctx.insertProject('test', 'test', api.datetime())

        xnatSession = session_mock()
        exp = import_session(self.dsc, src, project, xnatSession)

        for g in exp.getEpochGroups():
            scanID = xnatSession.scans().get()[0]
            dtype = xnatSession.scan(scanID).datatype()
            self.assertEqual(g.getOwnerProperty(DATATYPE_PROPERTY), dtype)
