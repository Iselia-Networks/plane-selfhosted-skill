# MCP route

Use a Plane MCP already provided by the host when it supports the requested operation. Discover
the actual tool names; prefixes and invocation APIs differ across Claude Code, Codex, OpenCode,
and other clients. Tool descriptions are the source of truth for arguments, not names copied
from another agent session.

The official server is [`makeplane/plane-mcp-server`](https://github.com/makeplane/plane-mcp-server).
For self-hosted Community deployments, the stdio/PAT route is generally the appropriate starting
point. OAuth availability depends on edition and deployment; do not create an OAuth application
or change edition merely to connect a Community instance.

Typical server process configuration (adapt to the client's format):

```text
command: uvx
arguments: [plane-mcp-server, stdio]
environment:
  PLANE_BASE_URL: https://plane.example.com
  PLANE_WORKSPACE_SLUG: example-workspace
  PLANE_API_KEY: <provided by the user's secret mechanism>
```

The official SDK version 0.3.1 appends `/api/v1` to `PLANE_BASE_URL`: use the origin, not a URL
already ending in `/api/v1`. Other servers/versions may differ; inspect their configuration
contract. If `PLANE_INTERNAL_BASE_URL` is present, check whether it overrides the public base.

## Claude Code setup

For Claude Code, register the process in the requested scope after making the three environment
variables above available to the client process through its private launch environment:

```sh
claude mcp add --transport stdio --scope user plane -- uvx plane-mcp-server stdio
claude mcp list
```

This command registers the process; it does not save the environment variables. They must still
be available when Claude starts the server. If the user's setup requires persisted MCP `env`
configuration, use their private user configuration or secret wrapper and restrict access. Never
put a real token in project `.mcp.json`, a shell command argument or committed documentation.
Inspect `claude mcp add --help` if the installed CLI has a different contract. Verify a real Plane
read in Claude after reconnecting, not just registration output. Avoid printing persisted `env`
values while diagnosing the connection.

## Other clients

Codex uses `codex mcp add ...`; OpenCode has its own MCP configuration format. Inspect the
installed client's help or current official documentation before writing its configuration.
Register only the requested client/scope and preserve existing settings. Keep credentials out
of shared repository configuration. Reconnect the server after changing its environment.

## Verify capabilities, not just discovery

- A real project read proves more than an environment-only `workspace.retrieve` response.
- A `project.list` tool may call `projects-lite/`, whereas a REST `projects/` read uses another
  endpoint. On an older Community deployment, the former can fail while the latter works.
- The official server 0.3.5 advertises features that a given Community deployment may not expose.
  In one Community 1.4.2 deployment, project reads worked but relation definitions, pages, and
  estimate operations returned `404`. Treat this as a probe hint, not a universal support matrix.
- If an MCP exposes only member reads, adding an active workspace member to a project needs
  a compatible CLI or the appropriate REST membership endpoint.
- The official relation tool's dependency/custom-definition contract can differ from the v1
  legacy relation contract. Switch to the verified route rather than changing payload names by guesswork.

For a partial failure, preserve the confirmed working connection and fall back per operation.
Do not restart the application server or rewrite a correct base URL to fix one missing endpoint.

Official references:
- https://developers.plane.so/dev-tools/mcp-server
- https://developers.plane.so/dev-tools/mcp-server-self-host
