# Copying projects and migrating data

A copy preserves the source unless the user explicitly requests a move or subsequent sync.
Define the source and destination projects before any write. Do not migrate an entire workspace
when the user asked for one project. Reuse an existing destination when instructed; inspect it
and avoid overwriting unrelated work.

## Snapshot and map

1. Enumerate every source page, including closed/archived items when the requested scope is a
   complete copy. Fetch full descriptions when list responses truncate them. Include requested
   comments, attachments/links, labels, milestones, cycles, parents, and dependencies.
2. Keep a task-local snapshot and a durable mapping/checkpoint for the import. Store no token
   in those files. Keep private snapshots out of public repositories and skill packages.
3. Map source workflow groups, priorities, identities, dates, and feature groupings to the
   target's native fields. Resolve assignees by verified identity, not fuzzy names alone.
4. List the destination before writes. Use stable `external_source` and source UUID `external_id`
   where the resource supports them. Do not assume the API enforces uniqueness. Retain a human
   source identifier and original URL plus the source-to-destination UUID/code mapping.

Create prerequisite workflow resources, then work items, then parents, comments, links, and
relations. Enable only the project features necessary for the requested representation. Linear
project milestones can be represented as Plane modules when that is the intended grouping;
state this mapping rather than implying native equivalence for every milestone feature.

## Preserve meaning

- Existing native assignees must be active and, where required, project members. Preserve the
  original name/ID in explicit metadata when an account is not yet assignable. Do not assign
  their tasks to the importer's account as a substitute.
- Native author and creation fields usually belong to the importing account/time. Retain source
  author, timestamps and reply references in the body when they cannot be represented natively.
  Do not claim original authorship was preserved in the destination's native fields.
- Preserve external PR/design links as links, not copied binary attachments. For actual files,
  transfer bytes only through approved download/upload routes and verify the uploaded result.
  Do not send a Plane API key to a third-party attachment host.
- A relation to an item outside the selected source project can remain an explicit original
  link. Do not silently enlarge the migration to unrelated projects.
- If native pages or estimates are unavailable, preserve documents or point values through an
  explicitly labelled representation and disclose it. If that changes an explicit requirement
  for native fidelity, ask the user before substituting it.

## Resume and audit

Respect rate limits and checkpoint after confirmed writes. Never blindly repeat a POST after a
timeout; reconcile the destination first. A bulk import should survive interruption without
creating duplicate tasks, comments, or links. For relationships, group targets by source and type
and record confirmed edges; do not reconstruct their direction from a title.

Validate source/destination counts and identities, full description content, status, priority,
label sets, deadlines, assignees, parent links, group membership, comments and relation direction.
Choose verification proportional to scale: complete field comparison for copied tasks and
explicit reconciliation of successful resource/relationship writes. Report any fields not
verified, missing accounts, adaptations, and out-of-scope references. Do not say “100% copied”
when native timestamps, authorship, or unsupported resource types were adapted.
