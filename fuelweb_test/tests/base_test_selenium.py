#    Copyright 2016 Mirantis, Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from fuelweb_test.tests.base_test_case import TestBasic
from fuelweb_test import logger
from fuelweb_test import settings


class SeleniumTestBase(TestBasic):

    def _get_public_url(self):
        with self.env.d_env.get_admin_remote() as remote:
            cmd = "fuel node \"$@\" | grep controller | awk '{print $1}'" \
                  " | head -1"
            controller_node_id = remote.execute(cmd)['stdout'][0].strip()
            controller_host = "node-{0}".format(controller_node_id)
            cmd = "ssh %s \". openrc; keystone catalog --service identity " \
                  "2>/dev/null | grep publicURL | awk '{print \$4}'\""\
                  % controller_host
            horizon_url = remote.execute(cmd)['stdout'][0].strip()
        url = horizon_url.split(":")
        return ":".join(url[0:2])

    def prepare_test_installation(self):
        with self.env.d_env.get_admin_remote() as remote:
            cmd = "cd dashboard_integration_tests/tools && " \
                  "./prepare_test_env.sh"
            logger.info("Running prepare environment script...")
            result = remote.execute(cmd)
            for line in result['stdout']:
                        logger.info(line)

    def clone_tests(self):
        with self.env.d_env.get_admin_remote() as remote:
            repository = settings.DASHBOARD_INTEGRATION_TESTS_REPO
            branch = "stable/7.0"
            cmd = ("yum install git -y && GIT_SSL_NO_VERIFY=true "
                   "git clone {0} -b {1}".format(repository, branch))

            logger.info("Cloning from {0}, branch {1}".format(
                repository, branch))
            result = remote.execute(cmd)
            for line in result['stdout']:
                logger.info(line)

    def edit_test_config(self):
        file_to_change = "/root/dashboard_integration_tests/openstack_" \
                         "dashboard/test/integration_tests/horizon.conf"
        dashboard_url = self._get_public_url()
        credentials = "simpleTun"
        login_url = "{0}/horizon/auth/login/".format(self._get_public_url())
        logger.info("Editing {0}".format(file_to_change))
        with self.env.d_env.get_admin_remote() as remote:
            prepare_cmd = (
                "sed -i 's#dashboard_url=http://localhost/#dashboard_url={1}#"
                "g' {0} && sed -i 's#login_url=http://localhost/auth/login/#"
                "login_url={2}#g' {0} && sed -i 's#username=demo#username={3}#"
                "g' {0} && sed -i 's#password=secretadmin#password={3}#g' {0} "
                "&& sed -i 's#admin_username=admin#admin_username={3}#g' {0} "
                "&& sed -i 's#admin_password=secretadmin#admin_password={3}#g'"
                " {0} && sed -i 's#sahara=True#sahara=False#g' {0}".format(
                    file_to_change, dashboard_url, login_url, credentials))
            prepare_result = remote.execute(prepare_cmd)
            for line in prepare_result['stdout']:
                logger.info(line)

    def run_ui_tests(self):
        with self.env.d_env.get_admin_remote() as remote:
            logger.info("Run Selenium tests")
            run_cmd = (
                "cd /root/dashboard_integration_tests && "
                "export NOSE_WITH_HTML_OUTPUT=1 && "
                "/bin/bash run_tests.sh -V --integration --selenium-headless")
            run_result = remote.execute(run_cmd)
            for line in run_result['stderr']:
                logger.info(line)

            remote.download('/root/dashboard_integration_tests/results.html',
                            'logs/')

            screenshots_directory = \
                "/root/dashboard_integration_tests/openstack_dashboard/test/" \
                "integration_tests/integration_tests_screenshots/"
            list_of_files = remote.execute(
                "if [ -d {0} ]; then ls {0}; fi".format(
                    screenshots_directory))['stdout']
            if list_of_files:
                for file in list_of_files:
                    file = file.replace('\n', '')
                    full_file_path = screenshots_directory + file

                    remote.download(full_file_path, 'logs/')


