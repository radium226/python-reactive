from decorators import extensionmethod
import collections
from abc import ABCMeta, abstractmethod
from queue import Queue
from executors import Executors

class Processor(metaclass=ABCMeta):
    
    def __init__(self):
        pass
    
    @abstractmethod
    def __call__(self, item):
        pass
    
class Publisher:

    def __init__(self, on_subscribe):
        self.on_subscribe = on_subscribe
    
    def subscribe(self, subscriber):
        subscriber.on_begin()
        self.on_subscribe(subscriber)
  
    def lift(self, processor):
        on_subscribe = self.on_subscribe
        def anonymous(subscriber):
            lifted_subscriber = processor(subscriber);
            lifted_subscriber.on_begin()
            on_subscribe(lifted_subscriber)
        return Publisher(anonymous)
    
    def iterate(self):
        queue = Queue()
        class Anonymous(Subscriber):
            def on_begin(self):
                pass
            
            def on_next(self, item):
                queue.put(item)
            
            def on_end(self):
                queue.put(None)
                
        executor = None
        try:
            executor = Executors.thread()
            self.subscribe_with(executor).subscribe(Anonymous())
            while True: 
                item = queue.get()
                if item is None:
                    break
                yield item
        finally:
            if executor is not None:
                executor.shutdown()

class Subscriber(metaclass=ABCMeta):
  
    def __init__(self):
        pass
    
    @abstractmethod
    def on_begin(self):
        pass

    @abstractmethod
    def on_next(self, item):
        pass

    @abstractmethod
    def on_end(self):
        pass

@extensionmethod(Publisher, decorator = staticmethod)
def just(items):
    def anonymous(subscriber):
        for item in items:
            subscriber.on_next(item)
        subscriber.on_end()
    return Publisher(anonymous)

if __name__ == "__main__":
    for item in Publisher.just(["Hello", "World"]).iterate():
        print(item)