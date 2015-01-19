from abc import ABCMeta, abstractmethod
from queue import Queue
from threading import Thread
from time import sleep
from multiprocessing.pool import ThreadPool
from multiprocessing import Pool as ProcessPool

class Executors():

    @staticmethod
    def current_thread():
        return CurrentThreadExecutor()
    
    @staticmethod
    def thread():
        return ThreadExecutor()
        
    @staticmethod
    def thread_pool(pool_size):
        return ThreadPoolExecutor(pool_size)
        
    @staticmethod
    def process_pool(pool_size):
        return ProcessPoolExecutor(pool_size)

class Executor(metaclass=ABCMeta):
    
    @abstractmethod
    def execute(self, target):
        pass
    @abstractmethod
    def shutdown(self):
        pass

class ProcessPoolExecutor(Executor):
    
    def __init__(self, pool_size):
        super().__init__()
        self.__process_pool = ProcessPool(processes = pool_size)
    
    def execute(self, task):
        self.__process_pool.apply_async(task)
    
    def shutdown(self):
        self.__process_pool.close()
        self.__process_pool.join()
        
class ThreadPoolExecutor(Executor):
    
    def __init__(self, pool_size):
        super().__init__()
        self.__thread_pool = ThreadPool(processes = pool_size)
    
    def execute(self, task):
        self.__thread_pool.apply_async(task)
    
    def shutdown(self):
        self.__thread_pool.close()
        self.__thread_pool.join()

class CurrentThreadExecutor(Executor):

    def __init__(self):
        super().__init__()
        
    def execute(self, task):
        task()
    
    def shutdown(self):
        pass

class ThreadExecutor(Executor):
    
    def __init__(self):
        super().__init__()
        self.__queue = Queue()
        def anonymous_target():
            while True:
                task = self.__queue.get()
                if task is None:
                    break
                task()
        self.__thread = Thread(target=anonymous_target)
        self.__thread.start()

    def execute(self, task):
        self.__queue.put(task)
    
    def shutdown(self):
        self.__queue.put(None)
        self.__thread.join()

if __name__ == "__main__":
    def sleep_n_print(duration, text):
        def anonymous():
            sleep(duration)
            print(text)
        return anonymous
    executor = Executors.thread_pool(1)
    executor.execute(sleep_n_print(2, "A"))
    print(" --> 1")
    executor.execute(sleep_n_print(3, "B"))
    print(" --> 3")
    executor.execute(sleep_n_print(2, "C"))
    print(" --> 2")
    executor.shutdown()
