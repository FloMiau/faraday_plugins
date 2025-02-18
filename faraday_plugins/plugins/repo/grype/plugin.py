"""
Faraday Penetration Test IDE
Copyright (C) 2013  Infobyte LLC (http://www.infobytesec.com/)
See the file 'doc/LICENSE' for the license information
"""

import json
import re
from faraday_plugins.plugins.plugin import PluginJsonFormat

__author__ = "Joachim Bauernberger"
__license__ = "MIT"
__version__ = "1.0.0"
__maintainer__ = "Joachim Bauernberger"
__email__ = "joachim.bauernberger@protonmail.com"
__status__ = "Development"


class GrypePlugin(PluginJsonFormat):
    def __init__(self, *arg, **kwargs):
        super().__init__(*arg, **kwargs)
        self.id = 'grype'
        self.name = 'Grype JSON Plugin'
        self.plugin_version = '1.0.0'
        self._command_regex = re.compile(r'^grype\s+.*')
        self._use_temp_file = True
        self._temp_file_extension = "json"
        self.json_keys = {"source", "matches", "descriptor"}

    def parseOutputString(self, output, debug=True):
        grype_json = json.loads(output)
        if "userInput" in grype_json["source"]["target"]:
            name = grype_json["source"]["target"]["userInput"]
        else:
            name = grype_json["source"]["target"]
        host_id = self.createAndAddHost(name, description=f"Type: {grype_json['source']['type']}")
        for match in grype_json['matches']:
            name = match.get('vulnerability').get('id')
            cve = name
            references = []
            if match["relatedVulnerabilities"]:
                description = match["relatedVulnerabilities"][0].get('description')
                references.append(match["relatedVulnerabilities"][0]["dataSource"])
                related_vuln = match["relatedVulnerabilities"][0]
                severity = related_vuln["severity"].lower().replace("negligible", "info")
                for url in related_vuln["urls"]:
                    references.append(url)
            else:
                description = match.get('vulnerability').get('description')
                severity = match.get('vulnerability').get('severity').lower().replace("negligible", "info")
                for url in match.get('vulnerability').get('urls'):
                    references.append(url)
            if not match['artifact']['metadata']:
                data = f"Artifact: {match['artifact']['name']}" \
                       f"Version: {match['artifact']['version']} " \
                       f"Type: {match['artifact']['type']}"
            else:
                if "Source" in match['artifact']['metadata']:
                    data = f"Artifact: {match['artifact']['name']} [{match['artifact']['metadata']['Source']}] " \
                           f"Version: {match['artifact']['version']} " \
                           f"Type: {match['artifact']['type']}"
                elif "VirtualPath" in match['artifact']['metadata']:
                    data = f"Artifact: {match['artifact']['name']} [{match['artifact']['metadata']['VirtualPath']}] " \
                           f"Version: {match['artifact']['version']} " \
                           f"Type: {match['artifact']['type']}"
            self.createAndAddVulnToHost(host_id,
                                        name=name,
                                        desc=description,
                                        ref=references,
                                        severity=severity,
                                        data=data,
                                        cve=cve)

    def processCommandString(self, username, current_path, command_string):
        super().processCommandString(username, current_path, command_string)
        command_string += f" -o json --file {self._output_file_path}"
        return command_string


def createPlugin(ignore_info=False, hostname_resolution=True):
    return GrypePlugin(ignore_info=ignore_info, hostname_resolution=hostname_resolution)
