# REST route and compatibility

Plane's public API uses JSON and `X-Api-Key` authentication. Resolve the API version supported
by the actual deployment. Community and older self-hosted instances commonly expose v1;
newer editions may expose v2. Do not automatically turn a failed v1 write into a v2 write:
schemas, permissions, relationships, and pagination can differ.

## Target and authentication

Keep the origin and API root distinct:

```text
Origin:      https://plane.example.com
v1 API root: https://plane.example.com/api/v1
v2 API root: https://plane.example.com/api/v2
```

A reverse-proxy deployment can include an application path prefix; preserve it when constructing
the API URL and verify the proxy actually serves that prefix. Never append the version twice.
Do not send the key to a different host after an HTTP redirect or to a URL copied from issue text.
Use the user's approved origin and keep TLS certificate verification enabled.

The bundled `scripts/plane_api.py` uses environment variables:

- `PLANE_BASE_URL`: instance origin, optional proxy prefix, or an explicit v1/v2 API root.
- `PLANE_API_KEY`: authorized token. It is not accepted on the command line or saved to disk.
- `PLANE_API_VERSION`: `v1` or `v2` (default `v1`). When the base already includes a version,
  it is used unless an explicit version selection conflicts, in which case the helper fails.

Examples, after setting the environment through the agent's secret mechanism:

```text
python3 <skill-directory>/scripts/plane_api.py GET users/me/
python3 <skill-directory>/scripts/plane_api.py GET workspaces/<slug>/projects/ --paginate
python3 <skill-directory>/scripts/plane_api.py GET workspaces/<slug>/projects/<project-uuid>/work-items/ --paginate
python3 <skill-directory>/scripts/plane_api.py POST workspaces/<slug>/projects/<project-uuid>/members/ --body-file member.json
```

`--body-file -` reads JSON from stdin. For structured writes, create the JSON using the host's
file tools rather than interpolating issue descriptions into shell commands. Output goes to
stdout as JSON; failures go to stderr as JSON with a nonzero exit code. No request payload is
logged. GET/HEAD may be retried for transient failures; writes are sent once, including on `429`.
The caller must reconcile an uncertain write before retrying it. `--paginate` is GET-only,
follows the observed cursor/offset envelope, and has a page limit. It rejects unsupported shapes
instead of silently returning an incomplete list. Large responses may contain private data;
keep exports local and scoped to the task.

## Useful v1 contracts

All paths below are relative to the selected `/api/v1/` root. They are examples verified against
a Community 1.4.2 deployment; inspect the actual server schema or test reads before using them
on another version.

| Operation | Method and path | Important fields |
|---|---|---|
| Projects | `GET workspaces/{slug}/projects/` | Resolve `identifier` to `id`. |
| Workspace members | `GET workspaces/{slug}/members/` | Resolve identity and role; verify active membership if this response omits it. |
| Project members | `GET/POST workspaces/{slug}/projects/{project}/members/` | POST: `member` is the user UUID, `role` is the project role. |
| Tasks | `GET/POST .../projects/{project}/work-items/` | `name`, `description_html`, `state`, `priority`, `assignees`, `labels`. |
| Task update | `PATCH .../work-items/{item}/` | `parent`, `target_date`, and other supported fields. Arrays replace existing values. |
| Comments | `GET/POST .../work-items/{item}/comments/` | `comment_html`; use `external_source`/`external_id` when supported. |
| Links | `GET/POST .../work-items/{item}/links/` | `url`, `title`. |
| Legacy relations | `GET/POST .../work-items/{item}/relations/` | POST: `relation_type`, `issues` (target UUID array). |
| Module membership | `GET/POST .../modules/{module}/module-issues/` | POST: `issues`. Enable modules before creating them. |

In the tested v1 role model, `15` means project contributor/member; `20` means admin. Resolve
the target's actual role contract and use the least role needed. An assignment request does not
justify making someone a workspace administrator or inviting an unrelated person.

Legacy relations include `blocking`, `blocked_by`, `relates_to`, and `duplicate`. With
`blocking`, the work item in the URL blocks the targets. Example JSON:

```json
{"relation_type":"blocking","issues":["<target-work-item-uuid>"]}
```

The field is `issues`, not the newer MCP argument `workitem_ids`. Group writes by origin and
type. Deduplicate symmetric relations; preserve the direction of dependencies.

## Diagnose failures

| Result | Next check |
|---|---|
| HTML/redirect instead of API JSON | Verify the origin, application prefix, reverse proxy, and version without following redirects with the key. |
| `401` | Token/header/expiration; avoid dumping configuration or regenerating credentials unasked. |
| `403` | Workspace/project membership and permission for this action. |
| `404` on one resource only | Compare with a known working API read; investigate edition, release, endpoint and object scope. |
| `400`/`422` | Use the selected endpoint's schema; do not randomly alternate field names between v1/v2. |
| `429` | Respect `Retry-After`, keep retrying bounded, and reconcile writes before resuming. |

Pages and estimates were absent from both the MCP and public REST routes tested on one
Community 1.4.2 installation. An upstream source file or newer documentation is not proof that
the running image serves a route. Conversely, do not hardcode that all Community versions lack
these resources. Prefer an explicit capability result for the current deployment.

Sources:
- https://developers.plane.so/api-reference/introduction
- https://developers.plane.so/api-reference/v2/introduction
- https://github.com/makeplane/plane/tree/v1.4.2/apps/api/plane/api/urls
