#!/bin/env python

from executors import ProcessPoolExecutor

def task():
    sleep(1)
    print("Hello! ")
    
class Function(object, metaclass=ABCMeta):

    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def __call__(self):
        pass
        
class AnonymousFunction(Function):
        
        def __call__(self):
            def test():
                sleep(1)
                print("Coucou! ")
            test()
            
        
if __name__ == "__main__":
    pool = ProcessPool(processes = 5)
    
    pool.apply_async(functools.partial(AnonymousFunction()))
        
    pool.close()
    pool.join()
