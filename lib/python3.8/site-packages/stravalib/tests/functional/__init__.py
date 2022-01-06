import warnings
import os
from six.moves.configparser import SafeConfigParser, NoOptionError

from stravalib import model
from stravalib.client import Client


from stravalib.tests import TestBase, TESTS_DIR, RESOURCES_DIR

TEST_CFG = os.path.join(TESTS_DIR, 'test.ini')

class FunctionalTestBase(TestBase):

    def setUp(self):
        super(FunctionalTestBase, self).setUp()
        if not os.path.exists(TEST_CFG):
            raise Exception("Unable to run the write tests without a test.ini in that defines an access_token with write privs.")

        cfg = SafeConfigParser()
        with open(TEST_CFG) as fp:
            cfg.readfp(fp, 'test.ini')
            access_token = cfg.get('write_tests', 'access_token')
            try:
                activity_id = cfg.get('activity_tests', 'activity_id')
            except NoOptionError:
                activity_id = None

        self.client = Client(access_token=access_token)
        self.activity_id = activity_id
