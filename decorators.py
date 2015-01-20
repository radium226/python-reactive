def extensionmethod(base, decorator = None, name = None):
    def anonymous(decored_function):
        method_name = decored_function.__name__ if name is None else name
        def anonymous(*args, **kwargs):
            return decored_function(*args, **kwargs)
        setattr(base, method_name, decorator(anonymous) if decorator else anonymous)
        return anonymous
    return anonymous