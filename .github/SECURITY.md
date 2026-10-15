# Security

## Scope

Comic Chaos is built for **trusted local use**: one person or a few people on
their own computer, with their own OpenAI key. It has **no authentication**, and
it binds to `127.0.0.1` by default. Running it on a public network without
adding authentication, HTTPS and an API budget limit is outside what it's
designed for. See [docs/self-hosting.md](../docs/self-hosting.md#exposing-it-beyond-your-computer).

Within that scope, we care about anything that could leak an API key, read or
write files outside `output/`, run code from untrusted input, or let one
browser tamper with another's session.

## Reporting a vulnerability

Please report privately through GitHub: **Security → Report a vulnerability** on
this repository. Don't open a public issue for security problems. Development
is on pause and the project is maintained on a best-effort basis, so there's no
guaranteed response time.

## If you exposed your API key

If you committed or shared an OpenAI key, revoke it at
<https://platform.openai.com/api-keys> and create a new one. Deleting the
file or rewriting git history isn't enough.
