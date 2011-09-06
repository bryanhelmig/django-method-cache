from datetime import datetime, timedelta

from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType

from django.core.urlresolvers import reverse

from django.test import TestCase
from django.test.client import Client

from django.conf import settings
from django.core.management import call_command
from django.db.models.loading import load_app

from method_cache.tests.mcthings.models import Thing

from time import sleep

class MethodCacheTest(TestCase):
    def _setUp_test_app(self):
        app_name = 'method_cache.tests.mcthings'
        
        self.old_INSTALLED_APPS = settings.INSTALLED_APPS 
        settings.INSTALLED_APPS = settings.INSTALLED_APPS + [app_name]
        
        load_app(app_name)
        call_command('syncdb', verbosity=0, interactive=False)
        
    def setUp(self):
        self._setUp_test_app()
        
        now = datetime.now()
        
        # create one thing for each hour previous
        for x in range(2):
            Thing.objects.create(date=now-timedelta(hours=x, minutes=15), number=100)
        
    def tearDown(self): 
        settings.INSTALLED_APPS = self.old_INSTALLED_APPS
    
    def test_on_model_cache(self):
        thing = Thing.objects.all()[0]
        cached_time = thing.less_intinsive_process()
        sleep(1)
        
        # datetimes should be equal, as it has been cached
        self.assertEqual(cached_time, thing.less_intinsive_process())
        
        # get a new instance of the same object, which should have a different datetime
        same_thing = Thing.objects.all()[0]
        self.assertNotEqual(cached_time, same_thing.less_intinsive_process())
    
    def test_memory_cache(self):
        thing = Thing.objects.all()[0]
        fairly_cached_time = thing.fairly_intinsive_process()
        super_cached_time = thing.super_intinsive_process()
        
        sleep(1)
        
        # datetimes should be equal, as it has been cached
        self.assertEqual(fairly_cached_time, thing.fairly_intinsive_process())
        self.assertEqual(super_cached_time, thing.super_intinsive_process())
        
        # get a new instance of the same object, which should have THE SAME datetime
        same_thing = Thing.objects.all()[0]
        self.assertEqual(fairly_cached_time, same_thing.fairly_intinsive_process())
        self.assertEqual(super_cached_time, same_thing.super_intinsive_process())
        
        # save this instance, which should invalidate the BOTH caches
        same_thing.save()
        sleep(1)
        
        also_same_thing = Thing.objects.all()[0]
        # now that the cache is cleared for this model, should NOT be equal
        new_fairly_cached_time = also_same_thing.fairly_intinsive_process()
        self.assertNotEqual(fairly_cached_time, new_fairly_cached_time)
        self.assertNotEqual(super_cached_time, also_same_thing.super_intinsive_process())
        
        # now lets save another, DIFFERENT record and ensure our original isn't cleared
        something_else = Thing.objects.all()[1]
        something_else.save()
        
        # go back and ensure the cache is still there, even on another instance
        the_original_thing = Thing.objects.all()[0]
        self.assertEqual(new_fairly_cached_time, the_original_thing.fairly_intinsive_process())
    
    def test_unsaved_models(self):
        # for new records not put into db, lets make sure they dont cache
        new_thing = Thing()
        
        the_time = new_thing.fairly_intinsive_process()
        sleep(1)
        
        self.assertNotEqual(the_time, new_thing.fairly_intinsive_process())