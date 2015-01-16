from decorators import extensionmethod
import collections
from abc import ABCMeta, abstractmethod
from queue import Queue
from executors import Executors
from threading import current_thread
from time import sleep

class Processor(metaclass=ABCMeta):
    
    def __init__(self):
        pass
    
    @abstractmethod
    def __call__(self, subscriber):
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
        class AnonymousSubscriber(Subscriber):
            def on_begin(self):
                pass
            
            def on_next(self, item):
                queue.put(item, block=True)
            
            def on_end(self):
                queue.put(None, block=True)
                
        executor = None
        try:
            executor = Executors.thread()
            self.publish_with(executor).subscribe(AnonymousSubscriber())
            while True: 
                item = queue.get(block=True)
                if item is None:
                    break
                yield item
        finally:
            if executor is not None:
                executor.shutdown()
    
    def publish_with(self, executor):
        class AnonymousProcessor(Processor):
            
            def __call__(self, subscriber):
                class AnonymousSubscriber(Subscriber):
                    def on_begin(self):
                        pass # ??
                    def on_next(self, item):
                        def anonymous_task():
                            subscriber.on_next(item)
                        executor.execute(anonymous_task)
                    def on_end(self):
                        def anonymous_task():
                            subscriber.on_end()
                        executor.execute(anonymous_task)
                return AnonymousSubscriber()
        return self.lift(AnonymousProcessor())

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

@extensionmethod(Publisher)
def delay(publisher, duration):
    class AnonymousProcessor():
        
        def __call__(self, subscriber):
            class AnonymousSubscriber(Subscriber):
                def on_begin(self):
                    subscriber.on_begin()
                def on_next(self, item):
                    sleep(duration)
                    subscriber.on_next(item)
                def on_end(self):
                        subscriber.on_end()
            return AnonymousSubscriber()
    return publisher.lift(AnonymousProcessor())
    
if __name__ == "__main__":
    executor = Executors.thread_pool(pool_size=5)
    for item in Publisher.just(["Hello", "World"]).delay(1).iterate():
        print(item)
    print("GoodBy!")
    executor.shutdown()