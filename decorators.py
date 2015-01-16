def extensionmethod(base, decorator = None):
    def anonymous(decored_function):
        name = decored_function.__name__
        def anonymous(*args, **kwargs):
            return decored_function(*args, **kwargs)
        setattr(base, name, decorator(anonymous) if decorator else anonymous)
        return anonymous
    return anonymous