# Security Policy

## Reporting a Vulnerability
If you believe you have found a security vulnerability in this repository, please do not open a public issue. Instead, responsibly disclose it to Microsoft Security Response Center (MSRC).

1. Visit https://aka.ms/opensource/security/report
2. Provide as much detail as possible: steps to reproduce, potential impact, and any proof-of-concept code.
3. Allow reasonable time for investigation and remediation before public disclosure.

## Supported Versions
This is a hackathon accelerator and may evolve rapidly. Security fixes will be applied on a best-effort basis. Please always use the latest commit on `main` unless a tagged release is provided.

## Security Best Practices
- Rotate API keys, secrets, and credentials regularly.
- Never commit secrets to the repository. Use Azure Key Vault or environment variables.
- Enable logging and monitoring for suspicious activity.
- Keep dependencies updated (`dependabot` or similar tooling recommended).

## Data Protection
If you process user or conversational data with Azure AI services:
- Avoid storing unnecessary transcripts.
- Redact personally identifiable information (PII) where possible.
- Comply with your organization's data governance policies.

## Cryptography
Use platform-managed keys or Azure Key Vault-backed keys for any encryption at rest or in transit where applicable. Do not implement custom cryptographic primitives.

## Contact
For general questions about security practices in this project, open a discussion thread. For sensitive issues, always use the MSRC reporting link above.
