'''
Copyright (c) 2012 Physion Consulting, LLC
'''
from ovation.xnat.importer import DATATYPE_PROPERTY, DATE_FORMAT

__author__ = 'barry'


from time import mktime, strptime


from ovation.xnat.util import xnat_api_pause, xnat_api, to_joda_datetime
from nose.tools import eq_, istest

from datetime import datetime

from ovation.xnat.test.OvationTestBase import OvationTestBase


class ImportingProjects(OvationTestBase):

    #TODO
#    @istest
#    def should_import_all_projects_form_xnat(self):
#        central = Interface(os.environ["XNAT_URL"],
#            os.environ["XNAT_USER"],
#            os.environ["XNAT_PASSWORD"])
#        import_projects(self.dsc, central)
#
#        ctx = self.dsc.getContext()
#        projects = ctx.getProjects()
#
#        eq_(len(projects), len(central.select.projects().get()))


    @istest
    def should_import_project_name_and_purpose_from_entity_attributes(self):
        xnatProject,projectURI = self._import_first_project()

        ctx = self.dsc.getContext()
        project = ctx.objectWithURI(projectURI)

        xnat_api_pause()
        expectedName = xnatProject.attrs.get('xnat:projectData/name')
        xnat_api_pause()
        expectedPurpose = xnatProject.attrs.get('xnat:projectData/description')

        eq_(project.getName(), expectedName)
        eq_(project.getPurpose(), expectedPurpose)

    @istest
    def should_import_project_keywords(self):
        xnatProject,projectURI = self._import_first_project()

        ctx = self.dsc.getContext()
        project = ctx.objectWithURI(projectURI)

        xnat_api_pause()
        expectedKeywords = xnatProject.attrs.get('xnat:projectData/keywords').split()
        for k in expectedKeywords:
            assert k in project.getTags()

    @istest
    def should_set_project_datatype_property(self):
        xnatProject,projectURI = self._import_first_project()

        ctx = self.dsc.getContext()
        project = ctx.objectWithURI(projectURI)

        eq_(project.getOwnerProperty(DATATYPE_PROPERTY), xnat_api(xnatProject.datatype))

    @istest
    def should_set_project_start_date_from_earliest_session_date(self):
        xnatProject,projectURI = self._import_first_project()

        # Find the earliest session date in the project
        projectID = xnat_api(xnatProject.id)
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
            sessionDates = [ datetime.fromtimestamp(mktime(strptime(time_str['date'], DATE_FORMAT))) for
                             time_str in
                             query if len(time_str['date']) > 0]
            if len(sessionDates) > 0:
                for sd in sessionDates:
                    if minSessionDate is not None:
                        if sd < minSessionDate:
                            minSessionDate = sd
                    else:
                        minSessionDate = sd


        if minSessionDate is not None:
            startTime = to_joda_datetime(minSessionDate, 'UTC')
        else:
            self.fail("Unable to find project sessions' start date")



        ctx = self.dsc.getContext()
        project = ctx.objectdWithURI(projectURI)


        eq_(project.getStartTime(), startTime)





