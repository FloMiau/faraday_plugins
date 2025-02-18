"""
Faraday Penetration Test IDE
Copyright (C) 2013  Infobyte LLC (http://www.infobytesec.com/)
See the file 'doc/LICENSE' for the license information

"""
from urllib.parse import urlsplit

from lxml import etree

from faraday_plugins.plugins.plugin import PluginJsonFormat
from faraday_plugins.plugins.repo.acunetix.DTO import Acunetix, Scan
from json import loads

__author__ = "Francisco Amato"
__copyright__ = "Copyright (c) 2013, Infobyte LLC"
__credits__ = ["Francisco Amato"]
__version__ = "1.0.0"
__maintainer__ = "Francisco Amato"
__email__ = "famato@infobytesec.com"
__status__ = "Development"

from faraday_plugins.plugins.repo.acunetix_json.DTO import AcunetixJsonParser, Vulnerabilities, \
    VulnerabilityTypes


class AcunetixXmlParser:
    """
    The objective of this class is to parse an xml file generated by
    the acunetix tool.

    TODO: Handle errors.
    TODO: Test acunetix output version. Handle what happens if
    the parser doesn't support it.
    TODO: Test cases.

    @param acunetix_xml_filepath A proper xml generated by acunetix
    """

    def __init__(self, xml_output):

        tree = self.parse_xml(xml_output)
        self.acunetix = Acunetix(tree)

    @staticmethod
    def parse_xml(xml_output):
        """
        Open and parse an xml file.

        TODO: Write custom parser to just read the nodes that we need instead
        of reading the whole file.

        @return xml_tree An xml tree instance. None if error.
        """

        try:
            parser = etree.XMLParser(recover=True)
            tree = etree.fromstring(xml_output, parser=parser)
        except SyntaxError as err:
            print("SyntaxError: %s. %s", err, xml_output)
            return None

        return tree


class AcunetixJsonPlugin(PluginJsonFormat):

    def __init__(self, *arg, **kwargs):
        super().__init__(*arg, **kwargs)
        self.id = "Acunetix_Json"
        self.name = "Acunetix JSON Output Plugin"
        self.plugin_version = "0.1"
        self.version = "9"
        self.json_keys = {'export'}
        self.framework_version = "1.0.0"
        self._temp_file_extension = "json"
    """
    Example plugin to parse acunetix output.
    """

    def parseOutputString(self, output):
        """
        This method will discard the output the shell sends, it will read it
        from the xml where it expects it to be present.

        NOTE: if 'debug' is true then it is being run from a test case and the
        output being sent is valid.
        """
        parser = AcunetixJsonParser(loads(output))
        for site in parser.export.scans:
            self.new_structure(site)

    def new_structure(self, site: Scan):
        start_url = site.info.host
        url_data = urlsplit(start_url)
        site_ip = self.resolve_hostname(url_data.hostname)
        ports = '443' if (url_data.scheme == 'https') else '80'
        vulnerability_type = {i.vt_id: i for i in site.vul_types}
        h_id = self.createAndAddHost(site_ip, None, hostnames=[url_data.hostname])
        s_id = self.createAndAddServiceToHost(
            h_id,
            "http",
            "tcp",
            ports=[ports],
            version=None,
            status='open')
        for i in site.vulnerabilities:
            vul_type = vulnerability_type[i.info.vt_id]
            self.create_vul(i, vul_type, h_id, s_id, url_data)

    def create_vul(self, vul: Vulnerabilities, vul_type: VulnerabilityTypes, h_id, s_id, url_data):
        self.createAndAddVulnWebToService(
            h_id,
            s_id,
            vul_type.name,
            vul_type.description,
            website=url_data.hostname,
            severity=vul_type.severity,
            resolution=vul_type.recommendation,
            request=vul.info.request,
            response=vul.response)

    @staticmethod
    def get_domain(scan: Scan):
        url = scan.start_url
        if not url.startswith('http'):
            url = f'http://{url}'
        url_data = urlsplit(url)
        if not url_data.scheme:
            url_data = urlsplit(scan.crawler.start_url_attr)
        return url_data


def createPlugin(ignore_info=False, hostname_resolution=True):
    return AcunetixJsonPlugin(ignore_info=ignore_info, hostname_resolution=hostname_resolution)
