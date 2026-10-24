# Self-hosted Plane agent skill

Manage any self-hosted [Plane](https://plane.so/) instance through the route that actually
supports the requested operation: connected MCP tools, a compatible CLI, or the public REST API.
Uses the open [Agent Skills format](https://agentskills.io/specification), with plain instructions,
relative references and an optional Python REST helper. No instance URL, workspace or credential
is bundled. This is a community skill, not an official Plane product.

## Install

Requires Node.js 22.20+ for the Skills installer:

```sh
npx skills add Iselia-Networks/plane-selfhosted-skill --skill plane-selfhosted
```

Select your agent interactively, or choose explicitly:

```sh
npx skills add Iselia-Networks/plane-selfhosted-skill --skill plane-selfhosted --agent claude-code
npx skills add Iselia-Networks/plane-selfhosted-skill --skill plane-selfhosted --agent codex
npx skills add Iselia-Networks/plane-selfhosted-skill --skill plane-selfhosted --agent opencode
```

Installation defaults to the current project. Add `--global` for user scope. The installer supports
other agents using the same format. Alternatively, copy `skills/plane-selfhosted` into the skill
directory supported by your agent. Installation does not configure Plane credentials or install a CLI.

## Use

Examples:

- “List the projects in my self-hosted Plane workspace.”
- “Create project Example with code EXM and verify it was created.”
- “Assign these tasks to the existing member; add project membership if required.”
- “Copy this Linear project into Plane, preserving descriptions, dependencies and assignees.”
- “Diagnose why the Plane MCP returns 404, then use the API for unsupported operations.”

Provide the target instance and workspace through your agent's configuration. Keep tokens in a
secret mechanism or environment, never in prompts, committed files or command arguments.
The skill checks the actual edition, release, endpoint and permissions before assuming support.
It respects existing project settings and user changes, including time zones.

## Included

- [Skill instructions](skills/plane-selfhosted/SKILL.md): routing and operation workflow.
- [CLI guidance](skills/plane-selfhosted/references/cli.md): community CLI setup and verified commands.
- [MCP guidance](skills/plane-selfhosted/references/mcp.md): official MCP configuration and compatibility checks, including Claude Code.
- [REST guidance](skills/plane-selfhosted/references/rest.md): versioned URLs, memberships, legacy relations and diagnostics.
- [Migration guidance](skills/plane-selfhosted/references/migrations.md): identity mapping, provenance, fidelity and reconciliation.
- [REST helper](skills/plane-selfhosted/scripts/plane_api.py): Python 3.10+, standard library only; optional.

The helper requires `PLANE_BASE_URL` and `PLANE_API_KEY`. It supports HTTPS, retains reverse-proxy
prefixes, accepts explicit API v1/v2 roots, blocks redirects, guards pagination, and does not retry
writes. Run `python3 skills/plane-selfhosted/scripts/plane_api.py --help` for options.

## Compatibility and validation

The skill itself has no dependency on a specific agent's tools, configuration paths or runtime.
The same skill can be installed for Claude Code, Codex and OpenCode. Actual actions require that
agent to have an authorized MCP connection or terminal access to the CLI/API. Other agents that
support Agent Skills can use the same files; this is not a claim that every agent or Plane release
has been tested.

The documented operational examples originate from read checks and actual operations against
one Plane Community 1.4.2 deployment, official MCP server 0.3.5 (SDK 0.3.1), and community
`@ysicing/plane-cli` 1.2.1. They are evidence for that combination, not universal compatibility
guarantees. Unit tests exercise the helper's URL, pagination, retry and credential boundaries.

```sh
python3 -m unittest discover -s tests -v
```

Public GitHub hosting makes this repository installable through the Skills CLI. [skills.sh](https://skills.sh/)
discovery and rankings are generated from installation telemetry; publication does not guarantee
immediate indexing or a leaderboard position. See the [Skills FAQ](https://skills.sh/docs/faq).

## Contributing

Keep changes generic, free of credentials and compatible with the Agent Skills specification.
Record the tested Plane edition/version for new endpoint examples. Do not infer support merely
from upstream source or a CLI help entry. Run the tests before proposing helper changes.

MIT licensed. See [LICENSE](LICENSE).
