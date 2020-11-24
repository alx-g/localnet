import argparse
from abc import ABC, abstractmethod


class BaseModule(ABC):
    """
    Abstract baseclass for all modules
    """

    @staticmethod
    @abstractmethod
    def register_args(parser: argparse.ArgumentParser):
        """
        Allows a module to register more cmdline arguments.
        """
        pass

    @abstractmethod
    def configure(self, args):
        """
        This function is called to forward cmdline settings to the module.
        """
        pass

    @abstractmethod
    def start(self):
        """
        Function to start/setup.
        """
        pass

    @abstractmethod
    def status(self):
        pass

    @abstractmethod
    def stop(self):
        """
        Funtcion to stop/clean up.
        """
        pass
