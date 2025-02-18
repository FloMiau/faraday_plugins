"""
Faraday Penetration Test IDE
Copyright (C) 2013  Infobyte LLC (http://www.infobytesec.com/)
See the file 'doc/LICENSE' for the license information

"""
import re
import xml.etree.ElementTree as ET

from faraday_plugins.plugins.plugin import PluginBase

__author__ = "Francisco Amato"
__copyright__ = "Copyright (c) 2013, Infobyte LLC"
__credits__ = ["Francisco Amato"]
__license__ = ""
__version__ = "1.0.0"
__maintainer__ = "Francisco Amato"
__email__ = "famato@infobytesec.com"
__status__ = "Development"


class DnsenumXmlParser:
    """
    The objective of this class is to parse an xml file generated by the dnsenum tool.

    TODO: Handle errors.
    TODO: Test dnsenum output version. Handle what happens if the parser doesn't support it.
    TODO: Test cases.

    @param dnsenum_xml_filepath A proper xml generated by dnsenum
    """

    def __init__(self, xml_output):
        tree = self.parse_xml(xml_output)

        if tree:
            self.items = [data for data in self.get_items(tree)]
        else:
            self.items = []

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
            print(f"SyntaxError: {err}. {xml_output}")
            return None

        return tree

    def get_items(self, tree):
        """
        @return items A list of Host instances
        """

        node = tree.findall('testdata')[0]
        for hostnode in node.findall('host'):
            yield Item(hostnode)


def get_attrib_from_subnode(xml_node, subnode_xpath_expr, attrib_name):
    """
    Finds a subnode in the item node and the retrieves a value from it

    @return An attribute value
    """

    node = xml_node.find(subnode_xpath_expr)

    if node is not None:
        return node.get(attrib_name)

    return None


class Item:
    """
    An abstract representation of a Item

    TODO: Consider evaluating the attributes lazily
    TODO: Write what's expected to be present in the nodes
    TODO: Refactor both Host and the Port clases?

    @param item_node A item_node taken from an dnsenum xml tree
    """

    def __init__(self, item_node):
        self.node = item_node

        self.hostname = self.get_text_from_subnode('hostname')
        self.ip = self.node.text

    def do_clean(self, value):
        myreturn = ""
        if value is not None:
            myreturn = re.sub("\n", "", value)
        return myreturn

    def get_text_from_subnode(self, subnode_xpath_expr):
        """
        Finds a subnode in the host node and the retrieves a value from it.

        @return An attribute value
        """
        sub_node = self.node.find(subnode_xpath_expr)
        if sub_node is not None:
            return sub_node.text

        return None


class DnsenumPlugin(PluginBase):
    """
    Example plugin to parse dnsenum output.
    """

    def __init__(self, *arg, **kwargs):
        super().__init__(*arg, **kwargs)
        self.id = "Dnsenum"
        self.name = "Dnsenum XML Output Plugin"
        self.plugin_version = "0.0.1"
        self.version = "1.2.2"
        self.options = None
        self._current_output = None
        self._use_temp_file = True
        self._temp_file_extension = "txt"
        self._command_regex = re.compile(
            r'^(sudo dnsenum|dnsenum|sudo dnsenum\.pl|dnsenum\.pl|perl dnsenum\.pl|\.\/dnsenum\.pl)\s+.*?')
        self.xml_arg_re = re.compile(r"^.*(-o\s*[^\s]+).*$")

    def parseOutputString(self, output):
        """
        This method will discard the output the shell sends, it will read it from
        the xml where it expects it to be present.

        NOTE: if 'debug' is true then it is being run from a test case and the
        output being sent is valid.
        """

        parser = DnsenumXmlParser(output)

        for item in parser.items:
            self.createAndAddHost(item.ip, hostnames=[item.hostname])

        del parser

    def processCommandString(self, username, current_path, command_string):
        """
        Adds the -oX parameter to get xml output to the command string that the
        user has set.
        """
        super().processCommandString(username, current_path, command_string)
        arg_match = self.xml_arg_re.match(command_string)

        if arg_match is None:
            return re.sub(r"(^.*?dnsenum(\.pl)?)", r"\1 -o %s" % self._output_file_path, command_string)
        else:
            return re.sub(arg_match.group(1), r"-o %s" % self._output_file_path, command_string)


def createPlugin(ignore_info=False, hostname_resolution=True):
    return DnsenumPlugin(ignore_info=ignore_info, hostname_resolution=hostname_resolution)
