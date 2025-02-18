"""
Faraday Penetration Test IDE
Copyright (C) 2013  Infobyte LLC (http://www.infobytesec.com/)
See the file 'doc/LICENSE' for the license information

"""
import re
import os
import json
import random
import shutil
import tempfile

from faraday_plugins.plugins.plugin import PluginBase


__author__ = "Nicolas Rodriguez"
__copyright__ = "Copyright (c) 2013, Infobyte LLC"
__credits__ = ["Nicolas Rodriguez"]
__license__ = ""
__version__ = "1.0.0"
__maintainer__ = "Francisco Amato"
__email__ = "famato@infobytesec.com"
__status__ = "Development"


class SkipfishParser:
    """
    The objective of this class is to parse an xml file generated by
    the skipfish tool.

    TODO: Handle errors.
    TODO: Test skipfish output version. Handle what happens if the parser
    doesn't support it.
    TODO: Test cases.

    @param skipfish_filepath A proper xml generated by skipfish
    """

    def __init__(self, skipfish_filepath):
        self.filepath = skipfish_filepath

        tmp = open(skipfish_filepath + "/samples.js").read()
        data = self.extract_data(
            tmp,
            "var issue_samples =", "];",
            lambda x: x.replace("'", '"'),
            False,
            False)
        # Escape characters not allowed in JSON, repr fix this with double Escape
        # Also remove \n character and space for have a valid JSON.
        issues = json.loads(repr(data[1]).replace("\\n"," ").replace("'","") + "]")

        tmp = open(skipfish_filepath + "/index.html").read()
        err_msg = json.loads(
            self.extract_data(
                tmp,
                "var issue_desc=",
                "};",
                lambda x: self.convert_quotes(x, "'", '"'),
                False,
                False)
            [1] + "}")

        self.err_msg = err_msg
        self.issues = issues

    def convert_quotes(self, text, quote="'", inside='"'):
        start = 0
        while True:
            pos = text.find(quote, start)

            if pos == -1:
                break

            ss = text[:pos - 1]
            quotes = len(ss) - len(ss.replace(inside, ""))

            if quotes % 2 == 0:
                text = text[:pos - 1] + "\\" + quote + text[pos + 1:]

            start = pos + 1
        return text

    def extract_data(self, samples, start_tag, end_tag, fn=lambda x: x, include_start_tag=True, include_end_tag=True):
        start = samples.find(start_tag)

        if start == -1:
            return (-1, None)

        end = samples.find(end_tag, start + 1)

        if end == -1:
            return (-2, None)

        data = samples[start:end + len(end_tag)]
        data = fn(data)

        if not include_start_tag:
            data = data[len(start_tag) + 1:]

        if not include_end_tag:
            data = data[:-1 * len(end_tag)]

        return (0, data)


class SkipfishPlugin(PluginBase):
    """
    Example plugin to parse skipfish output.
    """

    def __init__(self, *arg, **kwargs):
        super().__init__(*arg, **kwargs)
        self.id = "Skipfish"
        self.name = "Skipfish Output Plugin"
        self.plugin_version = "0.0.2"
        self.version = "2.1.5"
        self.options = None
        self.parent = None
        self._command_regex = re.compile(
            r'^(sudo skipfish|skipfish|sudo skipfish\.pl|skipfish\.pl|perl skipfish\.pl|\.\/skipfish\.pl|\.\/skipfish)\s+.*?')

    def _parse_filename(self, filename):
        self.parseOutputString(filename)
        if self._delete_temp_file:
            try:
                if os.path.isfile(filename):
                    os.remove(filename)
                elif os.path.isdir(filename):
                    shutil.rmtree(filename)
            except Exception as e:
                self.logger.error("Error on delete file: (%s) [%s]", filename, e)

    def parseOutputString(self, output):
        """
        This method will discard the output the shell sends, it will read it
        from the xml where it expects it to be present.

        NOTE: if 'debug' is true then it is being run from a test case and the
        output being sent is valid.
        """

        if not os.path.isdir(self._output_file_path):
            return False

        p = SkipfishParser(self._output_file_path)

        hostc = {}
        for issue in p.issues:
            for sample in issue["samples"]:
                if not sample["url"] in hostc:
                    reg = re.search(
                        "(http|https|ftp)\\://([a-zA-Z0-9\\.\\-]+(\\:[a-zA-Z0-9\\.&amp;%\\$\\-]+)*@)*((25[0-5]|2[0-4][0-9]|[0-1]{1}[0-9]{2}|[1-9]{1}[0-9]{1}|[1-9])\\.(25[0-5]|2[0-4][0-9]|[0-1]{1}[0-9]{2}|[1-9]{1}[0-9]{1}|[1-9]|0)\\.(25[0-5]|2[0-4][0-9]|[0-1]{1}[0-9]{2}|[1-9]{1}[0-9]{1}|[1-9]|0)\\.(25[0-5]|2[0-4][0-9]|[0-1]{1}[0-9]{2}|[1-9]{1}[0-9]{1}|[0-9])|localhost|([a-zA-Z0-9\\-]+\\.)*[a-zA-Z0-9\\-]+\\.(com|edu|gov|int|mil|net|org|biz|arpa|info|name|pro|aero|coop|museum|[a-zA-Z]{2}))[\\:]*([0-9]+)*([/]*($|[a-zA-Z0-9\\.\\,\\?\'\\\\+&amp;%\\$#\\=~_\\-]+)).*?$", sample["url"])

                    protocol = reg.group(1)
                    host = reg.group(4)
                    if reg.group(11) is not None:
                        port = reg.group(11)
                    else:
                        port = 443 if protocol == "https" else 80

                    ip = self.resolve_hostname(host)

                    h_id = self.createAndAddHost(ip, hostnames=[host])
                    s_id = self.createAndAddServiceToHost(h_id, "http", "tcp", ports=[port], status="open")

                    hostc[sample["url"]] = {
                        'h_id': h_id,
                        'ip': ip,
                        'port': port,
                        'host': host,
                        'protocol': protocol,
                        's_id': s_id}

                d = hostc[sample["url"]]
                self.createAndAddVulnWebToService(
                    d['h_id'],
                    d['s_id'],
                    name=p.err_msg[str(issue["type"])],
                    desc="Extra: " + sample["extra"],
                    website=d['host'],
                    path=sample["url"],
                    severity=issue["severity"])


    xml_arg_re = re.compile(r"^.*(-o\s*[^\s]+).*$")

    def processCommandString(self, username, current_path, command_string):
        """
        Adds the -o parameter to get report of the command string that the
        user has set.
        """
        super().processCommandString(username, current_path, command_string)
        arg_match = self.xml_arg_re.match(command_string)
        self._output_file_path = os.path.join(tempfile.gettempdir(), "faraday_plugin_skipfish_%d" % random.randint(1, 999999))
        self._delete_temp_file = True
        if arg_match is None:
            return re.sub(r"(^.*?skipfish)", r"\1 -o %s" % self._output_file_path, command_string, 1)
        else:
            return re.sub(arg_match.group(1), r"-o %s" % self._output_file_path, command_string, 1)




def createPlugin(ignore_info=False, hostname_resolution=True):
    return SkipfishPlugin(ignore_info=ignore_info, hostname_resolution=hostname_resolution)
