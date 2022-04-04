"""
Simple Configuration system for save controller options
"""
import json
from prettytable import PrettyTable
from libs.core.Log import Log
from libs.Exceptions import ConfigurationNotFound


class Configuration:
    """
    This class implements a simple configuration system
    using a key value storage
    """
    settings = {}

    @staticmethod
    def get(name, default=None):
        """
        Get configuration with given name
        If name is not a valid configuration name, a
        ConfigurationNotFound exception will be raised
        :param name: configuration name
        :return:
        """
        value = Configuration.settings.get(name, None)

        if default is None and value is None:
            raise ConfigurationNotFound(name)
        elif default is not None and value is None: 
            return default

        return value

    @staticmethod
    def set(name, value):
        """
        Set a configuration with name and value
        :param name: name of the configuration
        :param value: value of the configuration
        :return:
        """
        Configuration.settings[name] = value

    @staticmethod
    def load(config):
        """
        Load configuration from configuration json
        """
        with open(config) as d_file:
            data = json.load(d_file)

        return data

    @staticmethod
    def init(args):
        """
        Initialize configuration based on command line arguments
        :param args: command line arguments
        :return:
        """
        for arg in vars(args):
            Configuration.set(arg, vars(args).get(arg))

        Configuration.load_config(vars(args).get("config"))

    @staticmethod 
    def load_config(config):
        with open(config) as d_file:
            data = json.load(d_file)

        for key in data: 
            Configuration.set(key, data[key])
