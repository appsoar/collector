def print_function_name(func):
    def wrapperFunction(*args,**kwargs):
        print "="*10,func.__name__," start","="*10
        result = func(*args,**kwargs)
        print "="*10,func.__name__," end","="*10
        return result
    return wrapperFunction