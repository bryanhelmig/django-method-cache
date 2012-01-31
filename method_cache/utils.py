def create_master_key(instance):    
    from hashlib import sha224
    
    key = type(instance).__name__
    if hasattr(instance, "id"):
        key += str(instance.id)
    
    master_key = sha224( key ).hexdigest()
    #print "MASTERKEY:", instance, master_key
    
    return master_key

def cache_method(seconds=None):
    """
    A `seconds` value of `None` means that we will not cache it.
    
    `0` is the same as `None`, unless the backend supports 0 second timeouts (forever),
    this functionality is designed with Redis in mind, it may fail with memcached.
    
    Generates two SHA224_HASH's, one is a master key, and it exists to cache a list of method hashes.
    
    Caches on instance first, to save from redundant cache hits. So, if a result is cached on instance 
    (instance.SHA224_HASH), return that first.  
    
    If that fails, it checks django's cache backed for the same SHA224_HASH. If all else fails, hit 
    the method and save on instance and in cache. 
    
    ** NOTE: Methods that return None are always "recached".
    """
    
    from hashlib import sha224
    from django.core.cache import cache
    
    def inner_cache(method):
        
        def x(instance, *args, **kwargs):
            if hasattr(instance, "id") and not instance.id:
                # isn't a saved model yet
                return method(instance, *args, **kwargs)
            
            # primary
            master_key = create_master_key(instance)
            
            # create method key
            method_key = master_key + method.__name__ + str(args) + str(kwargs)
            
            if hasattr(instance, "lastchanged"):
                method_key += str(instance.lastchanged)
            
            method_key = sha224(method_key).hexdigest()
            
            # in order to keep the cache valid, we create a "master key" which is 
            # instance specific and contains a list of current method keys.
            keys = cache.get(master_key)
        
            if keys is None:
                keys = [method_key, ]
                if isinstance(seconds, int):
                    cache.set(master_key, keys, seconds*2)
            else:
                if not method_key in keys and isinstance(seconds, int):
                    keys.append(method_key)
                    cache.set(master_key, keys, seconds*2)
            
            if hasattr(instance, method_key):
                # has on class cache, return that
                result = getattr(instance, method_key)
            else:
                result = cache.get(method_key)
                
                if result is None:
                    # all caches failed, call the actual method
                    result = method(instance, *args, **kwargs)
                    
                    # save to cache and class attr
                    if isinstance(seconds, int): 
                        # only if integer, IE: 0 caches forever, 30*60 caches for 30 minutes
                        cache.set(method_key, result, seconds)
                    setattr(instance, method_key, result)
            
            return result
        
        return x
    
    return inner_cache


def clear_methods(instance):
    """
    Utilizing our master key scheme, we retrieve a list of method keys
    and then clear them all.
    """
    
    if hasattr(instance, "id"):
        from django.core.cache import cache
        master_key = create_master_key(instance)
        
        keys = cache.get(master_key)
        
        if not keys is None:
            cache.delete_many(keys)
        cache.delete(master_key)
        
        return True
    
    return False



from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save)
def clear_all_cache(sender, instance, created, **kwargs):
    clear_methods(instance)