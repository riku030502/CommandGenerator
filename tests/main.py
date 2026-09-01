"""NiceGUI entry point used by the tests.

The NiceGUI test fixture imports this file itself, so the upstream module must
be imported here (it parses sys.argv and calls ui.run() on import) and nowhere
else.  The data directory can be overridden with GPSR_DATA_DIR.
"""

import os
import sys

DATA_DIR = os.environ.get(
    "GPSR_DATA_DIR",
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data"),
)

sys.argv = ["gpsr_ui", "-d", DATA_DIR]

import robocupathome_generator.ui.gpsr_ui  # noqa: E402,F401
