# RoboCup@Home GPSR Command Generator (2026)

Ready-to-run packaging of the official
[RoboCupAtHome/CommandGenerator](https://github.com/RoboCupAtHome/CommandGenerator),
including its NiceGUI web interface, seeded with the 2026 world championship
arena data ([RoboCupAtHome/Incheon2026](https://github.com/RoboCupAtHome/Incheon2026)).

日本語の説明書 → **[README_ja.md](README_ja.md)**

This repository is used as a submodule of the robot repository `hma`, so clone
it with `--recursive` (or run `git submodule update --init --recursive`
afterwards); it also works standalone.

```bash
./setup.sh          # install (uv + Python 3.12 venv + upstream sources + arena data)
                    #   --competition=NAME  use another event's data
                    #   --recreate          rebuild .venv (after moving this folder)
./run_gpsr_ui.sh    # web interface on http://localhost:8080
./run_cli.sh        # text generator
./run_tests.sh      # verify the installation
```

Edit your arena data in `data/`, then validate it:

```bash
./.venv/bin/python tools/check_data.py data
```

'Rephrase' needs an OpenAI compatible LLM. Find one on this machine and write
the settings to `llm.conf`:

```bash
./.venv/bin/python tools/check_llm.py
cp llm.conf.example llm.conf
```
