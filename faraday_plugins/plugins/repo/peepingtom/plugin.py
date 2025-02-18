"""
Faraday Penetration Test IDE
Copyright (C) 2013  Infobyte LLC (http://www.infobytesec.com/)
See the file 'doc/LICENSE' for the license information
"""
import re
from os import path
from urllib.parse import urlparse

__author__ = "Andres Tarantini"
__copyright__ = "Copyright (c) 2015 Andres Tarantini"
__credits__ = ["Andres Tarantini"]
__license__ = "MIT"
__version__ = "0.0.1"
__maintainer__ = "Andres Tarantini"
__email__ = "atarantini@gmail.com"
__status__ = "Development"

from faraday_plugins.plugins.plugin import PluginBase


class PeepingTomPlugin(PluginBase):
    """
    Handle PeepingTom (https://bitbucket.org/LaNMaSteR53/peepingtom) output
    """

    def __init__(self, *arg, **kwargs):
        super().__init__(*arg, **kwargs)
        self.id = "peepingtom"
        self.name = "PeepingTom"
        self.plugin_version = "0.0.1"
        self.version = "02.19.15"
        self._command_regex = re.compile(
            r'^(python peepingtom.py|\./peepingtom.py)\s+.*?')
        self._path = None

    def parseOutputString(self, output):
        # Find data path
        data_path_search = re.search(r"in '(.*)\/'", output)
        print(data_path_search)
        if not data_path_search:
            # No data path found
            return True

        # Parse "peepingtom.html" report and extract results
        data_path = data_path_search.groups()[0]
        html = open(path.join(self._path, data_path, "peepingtom.html")).read()
        for url in re.findall(r'href=[\'"]?([^\'" >]+)', html):
            if "://" in url:
                url_parsed = urlparse(url)
                address = self.resolve_hostname(url_parsed.netloc)
                host = self.createAndAddHost(address)
                service = self.createAndAddServiceToHost(host, "http", protocol="tcp", ports=[80])
                self.createAndAddNoteToService(
                    host,
                    service,
                    'screenshot',
                    path.join(
                        self._path,
                        data_path_search.groups()[0],
                        "{}.png".format(url.replace(
                            "://", "").replace("/", "").replace(".", ""))
                    )
                )

        return True

    def processCommandString(self, username, current_path, command_string):
        super().processCommandString(username, current_path, command_string)
        self._path = current_path


def createPlugin(ignore_info=False, hostname_resolution=True):
    return PeepingTomPlugin(ignore_info=ignore_info, hostname_resolution=hostname_resolution)
