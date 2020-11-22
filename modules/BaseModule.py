import argparse
from abc import ABC, abstractmethod


class BaseModule(ABC):
    @staticmethod
    @abstractmethod
    def register_args(parser: argparse.ArgumentParser):
        pass

    @abstractmethod
    def configure(self, args):
        pass

    @abstractmethod
    def start(self):
        pass

    @abstractmethod
    def status(self):
        pass

    @abstractmethod
    def stop(self):
        pass
