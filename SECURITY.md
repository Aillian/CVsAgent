# Security Policy

## Reporting a Vulnerability

If you discover a security issue, **please do not open a public GitHub issue**.
Instead, contact the maintainer directly (via the email address on the GitHub
profile) or open a **private** security advisory on the repository.

Please include as much information as possible so we can reproduce and fix the
issue quickly:

- A description of the vulnerability
- Steps to reproduce
- The version of CVsAgent you are running
- Any proof-of-concept exploit code, if applicable

We aim to respond within **72 hours** and to ship a fix or mitigation within
**14 days** for high-severity issues.

## Handling Personal Data (PII)

CVsAgent processes résumé content, which is inherently personal data.

- **OpenAI / cloud providers**: When using any cloud LLM provider, CV text is
  transmitted to that provider for inference. Review the provider's data
  processing and retention policy before using CVsAgent on real candidates.
- **Local models**: Use `--provider ollama` to run extraction entirely on your
  own infrastructure.
- **Cache files**: The `.cvsagent_cache/` directory stores extracted JSON keyed
  by file hash. Treat it as sensitive data and delete it when no longer needed
  (`python main.py --clear-cache`).
- **Logs**: The `--log-file` option writes structured logs; make sure the
  destination is access-controlled.

## Supported Versions

Only the latest released version of CVsAgent receives security updates.
