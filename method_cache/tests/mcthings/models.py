from datetime import datetime

from django.db import models

from method_cache.utils import cache_method

class Thing(models.Model):
    "A dummy model to use for tests."
    date = models.DateTimeField()
    
    number = models.PositiveIntegerField()
    
    @cache_method() # no cache backend, stay on model
    def less_intinsive_process(self):
        return datetime.now()
    
    @cache_method(60) # 60 seconds
    def fairly_intinsive_process(self):
        return datetime.now()
    
    @cache_method(60 * 60) # 1 hour
    def super_intinsive_process(self):
        return datetime.now()