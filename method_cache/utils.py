
def create_master_key(instance):    
    from hashlib import sha224
    
    if hasattr(instance, "id"):
        return sha224(type(instance).__name__ + str(instance.id)).hexdigest()
    return None

def cache_method(seconds=0):
    """
    A `seconds` value of `0` means that we will not memcache it.
    
    If a result is cached on instance, return that first.  If that fails, check 
    memcached. If all else fails, hit the db and cache on instance and in memcache. 
    
    ** NOTE: Methods that return None are always "recached".
    """
    
    from hashlib import sha224
    from django.core.cache import cache
    
    def inner_cache(method):
        
        def x(instance, *args, **kwargs):
            if not hasattr(instance, "id"):
                # isn't a saved model yet
                return method(instance, *args, **kwargs)
            
            # primary
            master_key = create_master_key(instance)
            
            method_key = sha224(master_key + method.__name__ + str(args) + str(kwargs)).hexdigest()
            
            # in order to keep the cache valid, we create a "master key" which is instance specific
            # and contains a list of current method keys.
            keys = cache.get(master_key)
        
            if keys is None:
                keys = [method_key, ]
                cache.set(master_key, keys, seconds)
            else:
                if not key in keys:
                    keys.append(method_key)
                    cache.set(master_key, keys, seconds)
            
            
            if hasattr(instance, method_key):
                # has on class cache, return that
                result = getattr(instance, method_key)
            else:
                result = cache.get(method_key)
                
                if result is None:
                    # all caches failed, call the actual method
                    result = method(instance, *args, **kwargs)
                    
                    # save to memcache and class attr
                    if seconds and isinstance(seconds, int):
                        cache.set(method_key, result, seconds)
                    setattr(instance, method_key, result)
            
            return result
        
        return x
    
    return inner_cache



from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save)
def clear_all_cache(sender, instance, created, **kwargs):
    
    if hasattr(instance, "id"):
        from django.core.cache import cache
        master_key = create_master_key(instance)
    
        keys = cache.get(master_key)
    
        if not keys is None:
            for method_key in keys:
                cache.delete(method_key)
        cache.delete(master_key)