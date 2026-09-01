#!/usr/bin/env python3
"""Launcher for the RoboCup@Home GPSR NiceGUI interface.

``athome-generator-gpsr-ui`` hard-codes ``ui.run(show=False)``: the port is
always 8080 and the uvicorn auto-reloader is left on, which makes the process
parse its arguments twice and watch the whole working directory for changes.
This launcher patches ``ui.run`` before importing the upstream module so the
port and host can be chosen and the reloader stays off.

Every option that is not consumed here is forwarded untouched to the upstream
argument parser (-d/--data-dir, -u/--url, --host, --port, -a/--api-key,
-m/--model).  Note that upstream's --host/--port refer to the *LLM* server;
the web interface is configured with --ui-host/--ui-port.

Usage:  python3 tools/gpsr_ui.py -d DATA_DIR [--ui-port 8080] [LLM options]
"""

import argparse
import sys


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        add_help=False,
    )
    parser.add_argument("--ui-host", default="0.0.0.0",
                        help="address the web interface binds to (default 0.0.0.0)")
    parser.add_argument("--ui-port", type=int, default=8080,
                        help="port of the web interface (default 8080)")
    parser.add_argument("--ui-title", default="RoboCup@Home GPSR",
                        help="browser tab title")
    parser.add_argument("--ui-show", action="store_true",
                        help="open the default browser on start")
    parser.add_argument("--ui-reload", action="store_true",
                        help="keep NiceGUI's auto-reloader on (development only)")
    args, passthrough = parser.parse_known_args()

    if not {"-u", "--url", "--host"} & set(passthrough):
        print(
            "NOTE: no LLM configured - 'Rephrase' will fail (command generation works).\n"
            "      local server:  --host HOST --port PORT -a KEY -m MODEL\n"
            "      OpenAI:        -a sk-...",
        )

    if {"-h", "--help"} & set(passthrough):
        # Print our own options, then let the upstream parser print its own and exit.
        parser.print_help()
        print("\nUpstream options:")

    from nicegui import ui
    original_run = ui.run

    def patched_run(*run_args, **run_kwargs):
        run_kwargs.update(
            host=args.ui_host,
            port=args.ui_port,
            title=args.ui_title,
            show=args.ui_show,
            reload=args.ui_reload,
        )
        return original_run(*run_args, **run_kwargs)

    ui.run = patched_run

    # The upstream module parses sys.argv and starts the server on import.
    sys.argv = [sys.argv[0]] + passthrough
    import robocupathome_generator.ui.gpsr_ui  # noqa: F401


if __name__ == "__main__":
    main()
