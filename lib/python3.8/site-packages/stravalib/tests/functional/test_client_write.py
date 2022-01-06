from __future__ import absolute_import, unicode_literals
from datetime import datetime, timedelta
from io import BytesIO

from stravalib import model, exc, attributes, unithelper as uh
from stravalib.client import Client
from stravalib.tests.functional import FunctionalTestBase

class ClientWriteTest(FunctionalTestBase):
    
    def test_create_activity(self):
        """
        Test Client.create_activity simple case.
        """
        now = datetime.now().replace(microsecond=0)
        a = self.client.create_activity("test_create_activity#simple",
                                        activity_type=model.Activity.RIDE,
                                        start_date_local=now,
                                        elapsed_time=timedelta(hours=3, minutes=4, seconds=5),
                                        distance=uh.miles(15.2))
        print(a)
        
        self.assertIsInstance(a, model.Activity)
        self.assertEqual("test_create_activity#simple", a.name)
        self.assertEqual(now, a.start_date_local)
        self.assertEqual(round(float(uh.miles(15.2)), 2), round(float(uh.miles(a.distance)), 2))
        self.assertEqual(timedelta(hours=3, minutes=4, seconds=5), a.elapsed_time)
    
    
    def test_update_activity(self):
        """
        Test Client.update_activity simple case.
        """
        now = datetime.now().replace(microsecond=0)
        a = self.client.create_activity("test_update_activity#create",
                                        activity_type=model.Activity.RIDE,
                                        start_date_local=now,
                                        elapsed_time=timedelta(hours=3, minutes=4, seconds=5),
                                        distance=uh.miles(15.2))
        
        self.assertIsInstance(a, model.Activity)
        self.assertEqual("test_update_activity#create", a.name)
        
        update1 = self.client.update_activity(a.id, name="test_update_activivty#update")
        self.assertEqual("test_update_activivty#update", update1.name)
        self.assertFalse(update1.private)
        self.assertFalse(update1.trainer)
        self.assertFalse(update1.commute)
        
        update2 = self.client.update_activity(a.id, private=True)
        self.assertTrue(update2.private)
        
        update3 = self.client.update_activity(a.id, trainer=True)
        self.assertTrue(update3.private)
        self.assertTrue(update3.trainer)
        
        
        
    def test_upload_activity(self):
        """
        Test uploading an activity.
        
        NOTE: This requires clearing out the uploaded activities from configured 
        writable Strava acct.
        """
        with open(os.path.join(RESOURCES_DIR, 'sample.tcx')) as fp:
            uploader = self.client.upload_activity(fp, data_type='tcx')
            self.assertTrue(uploader.is_processing)
            a = uploader.wait()
            self.assertTrue(uploader.is_complete)
            self.assertIsInstance(a, model.Activity)
            self.assertEqual("02/21/2009 Leiden, ZH, The Netherlands", a.name)
            
            # And we'll get an error if we try the same file again
            with self.assertRaises(exc.ActivityUploadFailed):
                self.client.upload_activity(fp, data_type='tcx')
        