# Contributing to CVsAgent

Thanks for your interest! CVsAgent is an open-source project and contributions
are very welcome — from bug reports and documentation fixes to new features.

## Quick start

```bash
git clone https://github.com/<your-fork>/CVsAgent.git
cd CVsAgent
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env   # add your OPENAI_API_KEY
```

Run the test suite (no API key required — tests mock the LLM):

```bash
pip install pytest
pytest -q
```

## Development workflow

1. **Fork** the repo and create a topic branch: `git checkout -b feat/my-feature`.
2. **Make your change.** Keep commits focused; include tests when you add or
   change behavior.
3. **Run the tests** and make sure the CLI still works: `python main.py --help`.
4. **Open a Pull Request** with a clear description of *what* changed and *why*.

## Coding guidelines

- Target **Python 3.10+**.
- Prefer `pathlib` over `os.path`.
- Use the shared `cvs_agent.console.console` for all user-facing output — no
  bare `print()`.
- Add type hints for public functions.
- Keep modules small and focused — see the existing layout in `cvs_agent/`.
- Don't commit anything under `CVs/`, `output/`, or `.cvsagent_cache/` — those
  are user data directories.

## Reporting bugs / requesting features

Please use the GitHub issue tracker and the relevant template. For security
issues, see [SECURITY.md](SECURITY.md) and do **not** open a public issue.

## License

By contributing, you agree that your contributions will be licensed under the
project's [MIT License](LICENSE).
