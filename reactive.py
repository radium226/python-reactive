from decorators import extensionmethod
import collections
from abc import ABCMeta, abstractmethod
from queue import Queue
from executors import Executors
from threading import current_thread
from time import sleep
from functools import partial

class Processor(metaclass=ABCMeta):
    
    def __init__(self):
        pass
    
    @abstractmethod
    def __call__(self, subscriber):
        pass

class Publisher:
    
    def __init__(self, on_subscribe):
        self.__on_subscribe = on_subscribe
    
    def subscribe(self, subscriber):
        subscriber.on_subscribe()
        self.__on_subscribe(subscriber)
  
    def lift(self, processor):
        __on_subscribe = self.__on_subscribe
        def anonymous(subscriber):
            lifted_subscriber = processor(subscriber);
            lifted_subscriber.on_subscribe()
            __on_subscribe(lifted_subscriber)
        return Publisher(anonymous)
    
    def iterate(self):
        queue = Queue()
        class AnonymousSubscriber(Subscriber):
            def on_subscribe(self):
                pass
            
            def on_next(self, item):
                queue.put(item, block=True)
            
            def on_completed(self):
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
                    def on_subscribe(self):
                        pass # ??
                    def on_next(self, item):
                        def anonymous_task():
                            subscriber.on_next(item)
                        executor.execute(anonymous_task)
                    def on_completed(self):
                        def anonymous_task():
                            subscriber.on_completed()
                        executor.execute(anonymous_task)
                return AnonymousSubscriber()
        return self.lift(AnonymousProcessor())
    
    def nest(self):
        return Publisher.just(self)

    def subscribe_with(self, executor):
        class SubscribeWithProcessor(Processor):
            
            def __call__(self, subscribed_with_subscriber):
                class SubscribedWithSubscriber(Subscriber):
                    
                    def on_next(self, publisher):
                        def task():
                            class SubscribeWithSubscriber(Subscriber):
                                
                                def on_next(self, element):
                                    subscribed_with_subscriber.on_next(element)
                                    
                                def on_completed(self):
                                    subscribed_with_subscriber.on_completed()
                                    
                            publisher.subscribe(SubscribeWithSubscriber())
                        executor.execute(task)
                    
                    def on_completed(self):
                        pass # We ignore it
                    
                return SubscribedWithSubscriber()
        return self.nest().lift(SubscribeWithProcessor())

class Subscriber(metaclass=ABCMeta):
  
    def __init__(self):
        pass
    
    def on_subscribe(self):
        pass

    @abstractmethod
    def on_next(self, item):
        pass

    @abstractmethod
    def on_completed(self):
        pass

@extensionmethod(Publisher, decorator = staticmethod)
def just(*elements):
    class JustPublisher(Publisher):
        
        def __init__(self, elements):
            def on_subscribe(subscriber):
                for element in elements:
                    subscriber.on_next(element)
                subscriber.on_completed()
            super().__init__(on_subscribe)
        
        def __repr__(self):
            return "JustPublisher(" + elements.__repr__() + ")"
        
    just_publisher = JustPublisher(elements)
    return just_publisher

@extensionmethod(Publisher, decorator = staticmethod)
def defer(create_observable):
    def on_subscribe(subscriber):
        create_observable().subscribe(subscriber)
    return Publisher(on_subscribe)

@extensionmethod(Publisher)
def apply(publisher, function):
    class ApplyProcessor(Processor):
        
        def __call__(self, applyped_element_subscriber):
            class ElementSubscriber(Subscriber):
                
                def on_next(self, element):
                    applyped_element = function(element)
                    applyped_element_subscriber.on_next(applyped_element)
                
                def on_completed(self):
                    applyped_element_subscriber.on_completed()
                
            return ElementSubscriber()
    
    apply_processor = ApplyProcessor()
    return publisher.lift(apply_processor)
    

@extensionmethod(Publisher)
def upper_text(publisher):
    return publisher.apply(lambda text: text.upper())

@extensionmethod(Publisher, decorator = staticmethod)
def merge(publisher):
    class MergeProcessor(Processor):
        
        def __call__(self, publisher_subscriber):
            
            class PublisherPublisherSubscriber(Subscriber):
                
                def on_next(self, publisher_publisher):
                    class PublisherSubscriber(Subscriber):
                        
                        def on_next(self, element):
                            publisher_subscriber.on_next(element)

                        def on_completed(self):
                            pass

                    publisher_publisher.subscribe(PublisherSubscriber())
                
                def on_completed(self):
                    publisher_subscriber.on_completed()
                    
            return PublisherPublisherSubscriber()

    return publisher.lift(MergeProcessor())

@extensionmethod(Publisher)
def delay(publisher, duration):
    class AnonymousProcessor():
        
        def __call__(self, subscriber):
            class AnonymousSubscriber(Subscriber):
                def on_subscribe(self):
                    subscriber.on_subscribe()
                def on_next(self, item):
                    sleep(duration)
                    subscriber.on_next(item)
                def on_completed(self):
                        subscriber.on_completed()
            return AnonymousSubscriber()
    return publisher.lift(AnonymousProcessor())
    
@extensionmethod(Publisher)
def flat_apply(publisher, function):
    return Publisher.merge(publisher.apply(function))
    
def huge_process(text, executor):
    def defer():
        sleep(1)
        return Publisher.just(text.upper())
    return Publisher.defer(defer).subscribe_with(executor)
    
if __name__ == "__main__":
    class PrintSubscriber(Subscriber):
        
        def on_subscribe(self):
            pass
        
        def on_next(self, item):
            print(item)
        
        def on_completed(self):
            print("on_completed()")
            
        def __repr__(self):
            return "PrintSusbcriber()"
        
    executor = Executors.thread_pool(pool_size=5)
    
    abc_publisher = Publisher.just("a", "b", "c").upper_text()
    def_publisher = Publisher.just("d", "e", "f")
    abc_def_publisher_publisher = Publisher.just(abc_publisher, def_publisher)
    
    Publisher.merge(abc_def_publisher_publisher).subscribe(PrintSubscriber())
    
    
    Publisher.just("h4x0r", "l33t", "suxXx3r").flat_apply(partial(huge_process, executor=executor)).subscribe(PrintSubscriber())
    
    executor.shutdown()