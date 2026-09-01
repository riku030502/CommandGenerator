#!/usr/bin/env python3
"""Find and test an LLM endpoint for the GPSR interface's 'Rephrase' button.

With no arguments it probes the usual local ports for an OpenAI compatible
server, then actually rephrases a sample command through the same code path the
web interface uses.  What comes back is either a working ``llm.conf`` line or
the reason it failed and what to change.

Usage:
  python3 tools/check_llm.py                      probe localhost, test what it finds
  python3 tools/check_llm.py --host HOST --port PORT [-a KEY] [-m MODEL]
  python3 tools/check_llm.py -u URL [-a KEY] [-m MODEL]
"""

import argparse
import sys
import time

import requests

SAMPLE = "Tell me what is the heaviest dish on the shelf"

# (label, port) - servers that speak the OpenAI API on a well known local port.
KNOWN_PORTS = [
    ("Ollama", 11434),
    ("vLLM", 8000),
    ("LM Studio", 1234),
    ("llama.cpp", 8081),
    ("text-generation-webui", 5000),
]


def chat_url(host: str, port: int) -> str:
    return f"http://{host}:{port}/v1/chat/completions"


def list_models(url: str, key: str | None) -> list[str]:
    """Ask an OpenAI compatible server which models it serves."""
    base = url.split("/chat/completions")[0]
    headers = {"Authorization": f"Bearer {key}"} if key else {}
    try:
        reply = requests.get(f"{base}/models", headers=headers, timeout=5)
        if reply.status_code != 200:
            return []
        return [m["id"] for m in reply.json().get("data", [])]
    except requests.RequestException:
        return []


def probe(host: str) -> list[tuple[str, int, list[str]]]:
    found = []
    for label, port in KNOWN_PORTS:
        models = list_models(chat_url(host, port), "probe")
        if models:
            found.append((label, port, models))
    return found


def advise(message: str) -> str:
    """Translate the server's complaint into the flag that fixes it."""
    lowered = message.lower()
    if "connection refused" in lowered or "max retries" in lowered:
        return ("nothing is listening there: start the LLM server, or check the\n"
                "     host and port (Ollama defaults to 11434, vLLM to 8000)")
    if "name or service not known" in lowered or "nodename nor servname" in lowered:
        return "the host name does not resolve: use an IP address"
    if "timed out" in lowered:
        return "the server did not answer in time: check that it is reachable from this PC"
    if "model is required" in lowered or "model_not_found" in lowered:
        return "the server needs a model name: add  -m MODEL"
    if "does not support thinking" in lowered:
        return ("this model rejects the reasoning_effort the generator sends with -m.\n"
                "     pick a thinking capable model (e.g. qwen3:8b), or drop -m if the\n"
                "     server serves a single model (vLLM style)")
    if "401" in lowered or "unauthor" in lowered or "invalid_api_key" in lowered:
        return "the API key was rejected: check -a"
    if "404" in lowered:
        return "wrong path or model: check the URL and -m"
    return "check the URL, key and model name"


def test(url: str, key: str | None, model: str | None) -> bool:
    from robocupathome_generator.llm import SimpleOpenaiAPI

    shown_key = "-a " + ("<set>" if key else "<none>")
    print(f"\ntesting {url}  {shown_key}  -m {model or '<none>'}")
    llm = SimpleOpenaiAPI(url, key, model)
    started = time.time()
    try:
        phrasings = llm.alternativePhrasing(SAMPLE)
    except Exception as exc:  # the upstream client raises plain Exceptions
        print(f"  FAILED: {exc}")
        print(f"  -> {advise(str(exc))}")
        return False

    elapsed = time.time() - started
    print(f"  OK ({elapsed:.1f}s for one command, {len(phrasings)} phrasings)")
    print(f"  in : {SAMPLE}")
    for i, phrasing in enumerate(phrasings):
        print(f"  out {i}: {phrasing.strip()}")
    if elapsed > 8:
        print(f"  note: 'Rephrase ALL' on 3 commands will take about "
              f"{elapsed * 3:.0f}s at this speed")
    return True


def conf_line(url: str, host: str | None, port: int | None,
              key: str | None, model: str | None) -> str:
    if host and port:
        args = f"--host {host} --port {port}"
    else:
        args = f"-u {url}"
    if key:
        args += f" -a {key}"
    if model:
        args += f" -m {model}"
    return f'LLM_ARGS="{args}"'


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("-u", "--url", help="full URL to an OpenAI compatible chat API")
    parser.add_argument("--host", help="LLM host")
    parser.add_argument("--port", type=int, help="LLM port")
    parser.add_argument("-a", "--api-key", help="LLM API key")
    parser.add_argument("-m", "--model", help="LLM model name")
    args = parser.parse_args()

    if args.url and (args.host or args.port):
        parser.error("use either --url or --host/--port, not both")

    # ---- an endpoint was given: test exactly that ----
    if args.url or args.host:
        if args.host and not args.port:
            parser.error("--host also needs --port")
        url = args.url or chat_url(args.host, args.port)
        models = list_models(url, args.api_key)
        if models:
            print(f"server reports {len(models)} model(s): {', '.join(models)}")
            if not args.model:
                print("no -m given; the server may require one")
        if not test(url, args.api_key, args.model):
            return 1
        print("\nadd this line to llm.conf:")
        print("  " + conf_line(url, args.host, args.port, args.api_key, args.model))
        return 0

    # ---- nothing given: look around this machine ----
    print("no endpoint given - probing localhost")
    found = probe("localhost")
    if not found:
        ports = ", ".join(str(p) for _, p in KNOWN_PORTS)
        print(f"\nno OpenAI compatible server answered on: {ports}")
        print("\nOn a PC without a local LLM you have three options:")
        print("  1. install Ollama and pull a thinking capable model:")
        print("       curl -fsSL https://ollama.com/install.sh | sh")
        print("       ollama pull qwen3:8b")
        print("       python3 tools/check_llm.py")
        print("  2. point at a team server that already runs one:")
        print("       python3 tools/check_llm.py --host 192.168.0.5 --port 11434 -a KEY -m MODEL")
        print("  3. use OpenAI:")
        print("       python3 tools/check_llm.py -u https://api.openai.com/v1/chat/completions "
              "-a sk-... -m gpt-5")
        print("\nRephrase is optional - command generation works without any of this.")
        return 1

    for label, port, models in found:
        print(f"\nfound {label} on port {port}: {', '.join(models)}")

    label, port, models = found[0]
    key = args.api_key or "local"
    for model in models:
        url = chat_url("localhost", port)
        if test(url, key, model):
            print("\nadd this line to llm.conf:")
            print("  " + conf_line(url, "localhost", port, key, model))
            others = [m for m in models if m != model]
            if others:
                print(f"\nother models on this server: {', '.join(others)}")
                print("  to compare them:  python3 tools/check_llm.py "
                      f"--host localhost --port {port} -a {key} -m MODEL")
            return 0
        print("  trying the next model...")

    print("\nno model on this server worked with the generator's request format.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
