"""
Faraday Penetration Test IDE
Copyright (C) 2017  Infobyte LLC (http://www.infobytesec.com/)
See the file 'doc/LICENSE' for the license information
"""
from faraday_plugins.plugins.plugin import PluginBase
import re

__author__ = "Roberto Focke"
__copyright__ = "Copyright (c) 2017, Infobyte LLC"
__license__ = ""
__version__ = "1.0.0"


class hping3(PluginBase):

    def __init__(self, *arg, **kwargs):
        super().__init__(*arg, **kwargs)
        self.id = "Hping3"
        self.name = "hping3"
        self.plugin_version = "0.0.1"
        self.version = "1.0.0"
        self.srv = {'21': ' ftp', '80': 'http', '143': 'imap', '1433': 'mssql',
                    '3306': 'mysql', '524': 'ncp', '119': 'nntp',
                    '5631': 'pcanywhere', '110': 'pop3', '5432': 'postgres',
                    '512': 'rexec', '513': 'rlogin', '514': 'rsh',
                    '25': 'smtp', '161': 'snmp', '22': 'ssh', '3690': 'svn',
                    '23': 'telnet', '5900': 'vnc'}

        self._command_regex = re.compile(r'^(sudo hping3|hping3)\s+.*$')

    def parseOutputString(self, output):

        regex_ipv4 = re.search(r"(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}"
                               r"|2[0-4][0-9]|25[0-5])\)\:", output)
        if regex_ipv4:
            ip_address = regex_ipv4.group(0).rstrip("):") # Regex pls
        else:
            # Exit plugin, ip address not found. bad output
            self.logger.warning("Abort plugin: Ip address not found", "INFO")
            return

        hostname = output.split(" ")[1]
        host_id = self.createAndAddHost(ip_address, hostnames=[hostname])

        if re.match("HPING", output):

            sport = re.search(r"sport=(\d{1,6})", output)
            ssport = [sport.group(1)]
            reci = re.search(r"flags=(\w{2,3})", output)
            service = self.srv[sport.group(1)]

            if reci.group(1) == "SA":
                s_id = self.createAndAddServiceToHost(
                    host_id, service, protocol="tcp", ports=ssport, status="open")

        lineas = output.split("\n")

        for linea in lineas:
            if (re.match(" ", linea)):

                list = re.findall(r"\w+", linea)
                service = list[1]
                port = [list[0]]

                if list[2] == "S" and list[3] == "A":
                    s_id = self.createAndAddServiceToHost(
                        host_id, service, protocol="tcp", ports=port, status="open")


def createPlugin(ignore_info=False, hostname_resolution=True):
    return hping3(ignore_info=ignore_info, hostname_resolution=hostname_resolution)
