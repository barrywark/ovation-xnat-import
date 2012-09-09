'''
Copyright (c) 2012 Physion Consulting, LLC
'''

from ovation.xnat.importer import DATATYPE_PROPERTY, import_project
from ovation.xnat.util import iterate_entity_collection, xnat_api
from nose.tools import eq_, istest
from ovation.xnat.test.OvationTestBase import OvationTestBase, mock_project_for_import, patch_xnat_api


class ImportingSubjects(OvationTestBase):

    @istest
    @patch_xnat_api
    @mock_project_for_import
    def should_import_all_subjects_for_project(self, xnatProject):

        import_project(self.dsc, xnatProject, importProjectTree=True)

        ctx = self.dsc.getContext()

        for s in iterate_entity_collection(xnatProject.subjects):
            subjectID = xnat_api(s.id)
            sources = ctx.getSources(subjectID)

            eq_(1, len(sources))
            eq_(sources[0].getOwnerProperty('xnat:subjectURI'), s._uri)


    @istest
    @patch_xnat_api
    @mock_project_for_import
    def should_set_subject_datatype_property(self, xnatProject):
        ctx = self.dsc.getContext()

        for s in iterate_entity_collection(xnatProject.subjects):
            subjectID = xnat_api(s.id)
            sources = ctx.getSources(subjectID)

            eq_(1, len(sources))
            eq_(sources[0].getOwnerProperty(DATATYPE_PROPERTY), xnat_api(s.datatype))
