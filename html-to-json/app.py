"""ThreatConnect Playbook App"""

import json

from tcex import TcEx

from html_to_dict import html_string_to_dict
from playbook_app import PlaybookApp  # Import default Playbook App Class (Required)


class App(PlaybookApp):
    """Playbook App"""

    def __init__(self, _tcex: TcEx):
        """Initialize class properties.

        This method can be OPTIONALLY overridden.
        """
        super().__init__(_tcex)
        self.pretty_json: str

    def run(self):
        """Run the App main logic.

        This method should contain the core logic of the App.
        """
        html = self.in_.html
        if not isinstance(html, str):
            self.tcex.exit.exit(1, 'HTML input must be a string.')

        tree = html_string_to_dict(html)

        try:
            self.pretty_json = json.dumps(
                tree, indent=self.in_.indent, sort_keys=self.in_.sort_keys
            )
        except (TypeError, ValueError):
            self.tcex.exit.exit(1, 'Failed serializing HTML tree to JSON.')

        self.exit_message = 'HTML converted to JSON.'

    def write_output(self):
        """Write the Playbook output variables.

        This method should be overridden with the output variables defined in the install.json
        configuration file.
        """
        self.log.info('Writing Output')
        self.playbook.create.string('json.pretty', self.pretty_json)
