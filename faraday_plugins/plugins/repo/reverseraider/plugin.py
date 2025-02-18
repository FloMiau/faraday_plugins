"""
Faraday Penetration Test IDE
Copyright (C) 2013  Infobyte LLC (http://www.infobytesec.com/)
See the file 'doc/LICENSE' for the license information

"""
from faraday_plugins.plugins.plugin import PluginBase
import re



__author__ = "Francisco Amato"
__copyright__ = "Copyright (c) 2013, Infobyte LLC"
__credits__ = ["Francisco Amato"]
__license__ = ""
__version__ = "1.0.0"
__maintainer__ = "Francisco Amato"
__email__ = "famato@infobytesec.com"
__status__ = "Development"


class ReverseraiderParser:
    """
    The objective of this class is to parse an xml file generated by the reverseraider tool.

    @param reverseraider_filepath A proper simple report generated by reverseraider
    """

    def __init__(self, output):

        lists = output.split("\r\n")
        self.items = []

        if re.search("ReverseRaider domain scanner|Error opening", output) is not None:
            return

        for line in lists:
            if line != "":
                print(f"({line})")
                info = line.split("\t")
                if info.__len__() > 0:
                    item = {'host': info[0], 'ip': info[1]}
                    print(f"host = {info[0]}, ip = {info[1]}")
                    self.items.append(item)


class ReverseraiderPlugin(PluginBase):
    """
    Example plugin to parse reverseraider output.
    """

    def __init__(self, *arg, **kwargs):
        super().__init__(*arg, **kwargs)
        self.id = "Reverseraider"
        self.name = "Reverseraider XML Output Plugin"
        self.plugin_version = "0.0.1"
        self.version = "0.7.6"
        self.options = None
        self._command_regex = re.compile(r'^(sudo \.\/reverseraider|\.\/reverseraider)\s+.*?')
        self._completition = {
            "": "reverseraider -d domain | -r range [options]",
            "-r": "range of ipv4 or ipv6 addresses, for reverse scanning",
            "-d": "domain, for wordlist scanning (example google.com)",
            "-w": "wordlist file (see wordlists directory...)",
            "-t": "requests timeout in seconds",
            "-P": "enable numeric permutation on wordlist (default off)",
            "-D": "nameserver to use (default: resolv.conf)",
            "-T": "use TCP queries instead of UDP queries",
            "-R": "don't set the recursion bit on queries",
        }


    def parseOutputString(self, output):
        parser = ReverseraiderParser(output)
        for item in parser.items:
            h_id = self.createAndAddHost(item['ip'])
        del parser



def createPlugin(ignore_info=False, hostname_resolution=True):
    return ReverseraiderPlugin(ignore_info=ignore_info, hostname_resolution=hostname_resolution)
