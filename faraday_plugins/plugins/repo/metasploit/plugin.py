"""
Faraday Penetration Test IDE
Copyright (C) 2013  Infobyte LLC (http://www.infobytesec.com/)
See the file 'doc/LICENSE' for the license information
"""
import xml.etree.ElementTree as ET

from faraday_plugins.plugins.plugin import PluginXMLFormat

__author__ = "Francisco Amato"
__copyright__ = "Copyright (c) 2013, Infobyte LLC"
__credits__ = ["Francisco Amato"]
__license__ = ""
__version__ = "1.0.0"
__maintainer__ = "Francisco Amato"
__email__ = "famato@infobytesec.com"
__status__ = "Development"


class MetasploitXmlParser:
    """
    The objective of this class is to parse an xml file generated by the metasploit tool.

    TODO: Handle errors.
    TODO: Test metasploit output version. Handle what happens if the parser doesn't support it.
    TODO: Test cases.

    @param metasploit_xml_filepath A proper xml generated by metasploit
    """

    def __init__(self, xml_output):
        tree = self.parse_xml(xml_output)
        if tree:
            servicesByWebsite = {}
            for site in tree.findall('web_sites/web_site'):
                servicesByWebsite[site.find('id').text] = site.find('service-id').text
            webVulnsByService = {}
            for v in [data for data in self.get_vulns(tree, servicesByWebsite)]:
                if v.service_id not in webVulnsByService:
                    webVulnsByService[v.service_id] = []
                webVulnsByService[v.service_id].append(v)

            self.hosts = [data for data in self.get_items(
                tree,
                webVulnsByService)]
        else:
            self.hosts = []

    def parse_xml(self, xml_output):
        """
        Open and parse an xml file.

        TODO: Write custom parser to just read the nodes that we need instead of
        reading the whole file.

        @return xml_tree An xml tree instance. None if error.
        """
        try:
            tree = ET.fromstring(xml_output)
        except SyntaxError as err:
            print("SyntaxError: %s. %s" % (err, xml_output))
            return None

        return tree

    def get_items(self, tree, webVulns):
        """
        @return items A list of Host instances
        """

        for node in tree.findall('hosts/host'):
            yield Host(node, webVulns)

    def get_vulns(self, tree, services):
        """
        @return items A list of WebVuln instances
        """
        for node in tree.findall('web_vulns/web_vuln'):
            yield WebVuln(node, services)


def get_attrib_from_subnode(xml_node, subnode_xpath_expr, attrib_name):
    """
    Finds a subnode in the item node and the retrieves a value from it

    @return An attribute value
    """

    node = xml_node.find(subnode_xpath_expr)

    if node is not None:
        return node.get(attrib_name)

    return None


class Host:

    def __init__(self, item_node, webVulnsByService):
        self.node = item_node
        self.id = self.get_text_from_subnode('id')
        self.host = self.get_text_from_subnode('name')
        self.ip = self.get_text_from_subnode('address')
        self.os = self.get_text_from_subnode('os-name')

        self.services = []
        self.vulnsByService = {}
        self.vulnsByHost = []
        self.notesByService = {}
        self.credsByService = {}
        for s in self.node.findall('services/service'):
            service = {'id': None, 'port': None, 'proto': None,
                       'state': None, 'name': None, 'info': None}
            for attr in service:
                service[attr] = s.find(attr).text
            if not service['name']:
                service['name'] = 'unknown'
            if not service['state']:
                service['state'] = 'unknown'
            if not service['info']:
                service['info'] = 'unknown'

            self.services.append(service)
            self.vulnsByService[service['id']] = []
            self.notesByService[service['id']] = []
            if service['id'] in webVulnsByService:
                self.vulnsByService[service['id']] += webVulnsByService[service['id']]

        for v in self.node.findall('vulns/vuln'):
            vuln = HostVuln(v)
            if vuln.service_id:
                self.vulnsByService[vuln.service_id].append(vuln)
            else:
                self.vulnsByHost.append(vuln)

        for n in self.node.findall('notes/note'):
            note = HostNote(n)
            key = self.id + "_" + note.service_id
            if key not in self.notesByService:
                self.notesByService[key] = []

            self.notesByService[key].append(note)

        for c in self.node.findall('creds/cred'):
            cred = HostCred(c)
            key = cred.port
            if key not in self.credsByService:
                self.credsByService[key] = []

            self.credsByService[key].append(cred)

    def get_text_from_subnode(self, subnode_xpath_expr):
        """
        Finds a subnode in the host node and the retrieves a value from it.

        @return An attribute value
        """
        sub_node = self.node.find(subnode_xpath_expr)
        if sub_node is not None:
            if sub_node.text is not None:
                return sub_node.text

        return None


class WebVuln:

    def __init__(self, item_node, services):
        self.node = item_node
        self.name = self.get_text_from_subnode('name')
        self.desc = self.get_text_from_subnode('description')
        self.host = self.get_text_from_subnode('vhost')
        self.port = self.get_text_from_subnode('port')
        self.ip = self.get_text_from_subnode('host')
        self.path = self.get_text_from_subnode('path')
        self.method = self.get_text_from_subnode('method')
        self.params = self.get_text_from_subnode('params')
        self.pname = self.get_text_from_subnode('pname')
        self.risk = self.get_text_from_subnode('risk')
        self.confidence = self.get_text_from_subnode('confidence')
        self.query = self.get_text_from_subnode('query')
        self.request = self.get_text_from_subnode('request')
        self.category = self.get_text_from_subnode('category-id')
        web_id = self.get_text_from_subnode('web-site-id')
        self.service_id = None
        if web_id:
            self.service_id = services[web_id]

        self.isWeb = True

    def get_text_from_subnode(self, subnode_xpath_expr):
        """
        Finds a subnode in the host node and the retrieves a value from it.

        @return An attribute value
        """

        sub_node = self.node.find(subnode_xpath_expr)
        if sub_node is not None:
            if sub_node.text is not None:
                return sub_node.text

        return ""


class HostNote:
    """
    An abstract representation of a HostNote


    @param item_node A item_node taken from an metasploit xml tree
    """

    def __init__(self, item_node):
        self.node = item_node
        self.service_id = self.get_text_from_subnode(
            'service-id') if not None else ""
        self.host_id = self.get_text_from_subnode('host-id')
        self.ntype = self.get_text_from_subnode('ntype')
        self.data = self.get_text_from_subnode('data')

    def get_text_from_subnode(self, subnode_xpath_expr):
        """
        Finds a subnode in the host node and the retrieves a value from it.

        @return An attribute value
        """
        sub_node = self.node.find(subnode_xpath_expr)
        if sub_node is not None:
            if sub_node.text is not None:
                return sub_node.text

        return ""


class HostCred:
    """
    An abstract representation of a HostNote


    @param item_node A item_node taken from an metasploit xml tree
    """

    def __init__(self, item_node):
        self.node = item_node
        self.port = self.get_text_from_subnode('port')
        self.user = self.get_text_from_subnode('user')
        self.passwd = self.get_text_from_subnode('pass')
        self.ptype = self.get_text_from_subnode('ptype')
        self.sname = self.get_text_from_subnode('sname')

    def get_text_from_subnode(self, subnode_xpath_expr):
        """
        Finds a subnode in the host node and the retrieves a value from it.

        @return An attribute value
        """
        sub_node = self.node.find(subnode_xpath_expr)
        if sub_node is not None:
            if sub_node.text is not None:
                return sub_node.text

        return ""


class HostVuln:
    """
    An abstract representation of a HostVuln


    @param item_node A item_node taken from an metasploit xml tree
    """

    def __init__(self, item_node):
        self.node = item_node
        self.service_id = self.get_text_from_subnode('service-id')
        self.name = self.get_text_from_subnode('name')
        self.desc = self.get_text_from_subnode('info')
        self.refs = [r.text for r in self.node.findall('refs/ref')]
        self.cve = [r.text for r in self.node.findall('refs/ref') if r.text.startswith('CVE')]
        self.exploited_date = self.get_text_from_subnode('exploited-at')
        self.exploited = (self.exploited_date is not None)
        self.isWeb = False

    def get_text_from_subnode(self, subnode_xpath_expr):
        """
        Finds a subnode in the host node and the retrieves a value from it.

        @return An attribute value
        """
        sub_node = self.node.find(subnode_xpath_expr)
        if sub_node is not None:
            if sub_node.text is not None:
                return sub_node.text

        return ""


class MetasploitPlugin(PluginXMLFormat):
    """
    Example plugin to parse metasploit output.
    """

    def __init__(self, *arg, **kwargs):
        super().__init__(*arg, **kwargs)
        self.identifier_tag = ["MetasploitV4", "MetasploitV5"]
        self.id = "Metasploit"
        self.name = "Metasploit XML Output Plugin"
        self.plugin_version = "0.0.1"
        self.version = "4.7.2"
        self.framework_version = "1.0.0"
        self.options = None
        self.target = None

    def parseOutputString(self, output):
        """
        This method will discard the output the shell sends, it will read it from
        the xml where it expects it to be present.
        """

        parser = MetasploitXmlParser(output)

        for item in parser.hosts:
            self.hostnames = []
            if item.host:
                self.hostnames = [item.host]

            h_id = self.createAndAddHost(item.ip, os=item.os, hostnames=self.hostnames)

            if item.id + "_" in item.notesByService:
                for n in item.notesByService[item.id + "_"]:
                    self.createAndAddNoteToHost(h_id, n.ntype, n.data)

            for v in item.vulnsByHost:
                self.createAndAddVulnToHost(
                    h_id, v.name, v.desc, ref=v.refs, cve=v.cve)

            for s in item.services:
                s_id = self.createAndAddServiceToHost(h_id, s['name'],
                                                      protocol=s['proto'],
                                                      ports=[s['port']],
                                                      status=s['state'],
                                                      description=s['info'])

                if item.id + "_" + s['id'] in item.notesByService:
                    for n in item.notesByService[item.id + "_" + s['id']]:
                        self.createAndAddNoteToService(
                            h_id, s_id, n.ntype, n.data)
                if s['port'] in item.credsByService:
                    for c in item.credsByService[s['port']]:
                        self.createAndAddCredToService(
                            h_id, s_id, c.user, c.passwd)
                        self.createAndAddVulnToService(h_id, s_id, "Weak Credentials",
                                                       "[metasploit found the following credentials]\nuser:%s\npass:%s" % (
                                                           c.user, c.passwd), severity="high")

                for v in item.vulnsByService[s['id']]:
                    if v.isWeb:
                        self.createAndAddVulnWebToService(h_id, s_id, v.name, v.desc,
                                                                 severity=v.risk, website=v.host,
                                                                 path=v.path, request=v.request, method=v.method,
                                                                 pname=v.pname, params=v.params, query=v.query,
                                                                 category=v.category)
                    else:
                        self.createAndAddVulnToService(
                            h_id, s_id, v.name, v.desc, ref=v.refs, cve=v.cve)

        del parser

    @staticmethod
    def _isIPV4(ip):
        if len(ip.split(".")) == 4:
            return True
        else:
            return False


def createPlugin(ignore_info=False):
    return MetasploitPlugin(ignore_info=ignore_info)
