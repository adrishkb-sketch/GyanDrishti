import abc
import time

class BaseCapture(abc.ABC):
    @abc.abstractmethod
    def read_frame(self):
        pass
    
    @abc.abstractmethod
    def release(self):
        pass
