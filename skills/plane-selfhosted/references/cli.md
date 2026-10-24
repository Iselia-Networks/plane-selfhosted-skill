# CLI route

The reference CLI is the community project
[`@ysicing/plane-cli`](https://github.com/ysicing/plane-cli), not an official Plane product.
Version 1.2.1 was tested with a Community 1.4.2 deployment for read-only project/task listings,
members, modules, comments, issue-key resolution, and legacy relations. This is a compatibility
observation, not a guarantee for other releases or all write commands.

## Identify and configure

Inspect `plane --help` and the installed package identity. Several unrelated Plane clients use
the executable name `plane`; do not mix their flags or overwrite an existing executable blindly.
If installation is requested, inspect package metadata, pin the chosen release, and account for
installation hooks. In 1.2.1, the postinstall adds agent skills; installing just the CLI can use:

```sh
npm install --global @ysicing/plane-cli@1.2.1 --ignore-scripts
```

Node.js 22+ is required by that release. Choose an installation scope appropriate to the user's
system. Do not assume `npm -g`, Homebrew, a Unix home directory, or admin access is available.

Environment variables for this implementation:

| Variable | Value |
|---|---|
| `PLANE_BASE_URL` | User-selected instance origin, such as `https://plane.example.com`; the CLI adds `/api/v1`. |
| `PLANE_API_KEY` | Existing authorized API key; never embed it in published examples or command text. |
| `PLANE_WORKSPACE` | Workspace slug, not the MCP variable `PLANE_WORKSPACE_SLUG`. |
| `PLANE_CLI_CONFIG_PATH` | Optional explicit local configuration path. |

Use the host's environment mechanism. For example, POSIX shells use `export NAME=value` and
PowerShell uses `$env:NAME = 'value'`; fetch the key from a secret source without echoing it.
`plane config set --base-url ... --workspace ...` stores nonsecret defaults. Persist an API key
only as part of authorized connection setup and protect the local file with appropriate file
permissions or Windows ACLs. Version 1.2.1 does not itself establish restrictive file permissions.
Do not modify shell startup files or unrelated agent configurations automatically.

## Commands to inspect

```text
plane project ls --json
plane project get <project-uuid> --json
plane issue ls --project <project-uuid> --limit 100 --json
plane issue get <PROJECT-123> --json
plane project members workspace --json
plane project members ls --project <project-uuid> --json
plane project modules ls --project <project-uuid> --json
plane issue comments ls <PROJECT-123> --json
plane issue links ls <PROJECT-123> --json
plane issue relations ls <PROJECT-123> --json
```

Use `--help` for the actual installed version before writes. Examples for this implementation:

```text
plane project members add --project <project-uuid> --member <user-uuid> --role member
plane issue update --project <project-uuid> <item-uuid> --assignees <user-uuid>
plane issue relations add <PROJECT-123> --relation-type blocking --issues <target-uuid-1,target-uuid-2>
```

`--assignees` replaces the set; preserve existing assignments when adding someone. For member
updates/deletes, distinguish a user UUID from a project-member record UUID; some list endpoints
return only user profiles. Do not guess the record ID.

Machine-readable output does not imply automatic pagination or retry. Inspect `next_cursor` and
`next_page_results`; pass `--cursor` explicitly as needed. For resumable imports and structured
bodies unsupported by flags, use REST. The CLI uses API v1: a v2-only feature needs a different
route and cannot be inferred from a similarly named command.
