===================
django-method-cache
===================

A simple app for caching resource intensive methods on models. Baked in is automatic invalidation of the cache when the underlying data changes.


Examples
===================

Generally, this is a very simple app to use:

 from method_cache.utils import cache_method
 
 class Profile(models.Model):
     user = models.OneToOneField(User)
     
     ...
     
     @cache_method(3600)
     def some_intensive_method(self):
         ...
         return 'cache me!'