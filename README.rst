===================
django-method-cache
===================

A simple app for caching resource intensive methods on models. Automatic invalidation of the cache when the underlying data changes is backed in.

How It Works
===================

django-method-cache has two different ways of caching, the first layer is instance specific as it is on class as a new property or attribute. The second involves memcached (or whatever cache layer you have set for Django). The "method keys" are a sha224 hash of the Model name, Model's database ID, method name as well as any *args or **kwargs.

django-method-cache also invalidates all data in the Django persistent cache for that specific model instance (tied to the ID) when you save. It does this by keeping an updated list of "method keys" under a "master key". Please note that if your method uses data from ForeignKey fields or ManyToMany fields, changes on those respective Models will not result in a cache purge (unless you are mindless to call .save() on the original model instance).


Examples
===================

Generally, this is a very simple app to use. If you wanted to store the result in a more persistent cache like memcached, you would pass the seconds to cache::

    from method_cache.utils import cache_method
    
    class Profile(models.Model):
        user = models.OneToOneField(User)
        
        ...
        
        @cache_method(3600)
        def some_intensive_method(self):
            ...
            return 'cache me!'

If you'd rather not cache persistently (for example, you use this method many times in a request, but the data resides off model), you can signify it by leaving out the seconds argument::

    @cache_method()
    def some_intensive_method(self):
        ...
        return 'cache me!'