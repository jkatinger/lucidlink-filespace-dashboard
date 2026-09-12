---
name: lucidlink-filespace-dashboard
description: >-
  Build a shareable dashboard for a LucidLink filespace and place it inside the
  filespace so the whole team sees it. Tiles cover the activity pulse (reads,
  writes, deletes per day), who is working in which folder, humans versus
  agents (service accounts), cold data and archive candidates, storage mix by
  file type, and the newest changes. Data comes from the filespace audit trail
  and directory tree through the LucidLink MCP Server, a mounted filespace, or
  the Python SDK. Use when someone asks for a filespace dashboard, storage or
  usage report, activity overview, "who touched what", cold-data or archive
  candidates, or wants to see what agents did in a filespace.
---

# LucidLink filespace dashboard

You produce a single self-contained `index.html` plus the `snapshot.json` it was
rendered from, styled as a LucidLink Lab app, and place both inside the
filespace (default `/Dashboards/<name>/`). Anyone with the filespace mounted
opens the page from the drive. No server, no build step, no external calls.

The interesting tiles are the ones a plain file listing cannot give: every read
and write with its actor, agents as first-class actors, and locks. That is what
to lead with when you present the result.

## Before you start

1. Confirm the audit trail is on. Through the MCP Server: `read_audit_trail`
   with `mode=aggregate`, `group_by=action`, `time_range=7d`. On a mount: the
   folder `/.lucid_audit` exists and has `.log` files. If it is off, say so
   plainly: activity tiles will be empty until an admin enables it, and only
   events after that point are recorded.
2. Pick a source (table below). Prefer the script over hand-built JSON when a
   mount or the SDK is reachable; it costs no tokens and is repeatable.
3. Stay read-only. This skill never modifies, moves or deletes filespace
   content. The only write is the dashboard folder, and only after the user
   has agreed to the location.

| Source | When | Cost | Stored size available |
|---|---|---|---|
| `mount` | filespace is mounted on this machine | one script run, seconds | no (pass it from MCP `filespace_stats`) |
| `sdk` | you have a service-account token and Python | one script run | yes |
| `mcp` | only the MCP Server is reachable | 5 to 100+ tool calls by budget | yes |

## Interview, three questions

Ask all three at once, numbered, with the defaults shown. Do not ask anything else.

1. **Who reads this first?** Production lead (who is working where), storage
   admin (cold data, cost), or developer (agent activity). Default: all three,
   one tile row each.
2. **Which folders matter?** Top-level folders by default. Name a subtree to
   focus on, or a grouping depth of 2 for per-show or per-client folders.
3. **How much to spend?** `lite`, `standard` (default) or `deep`. Explain in one
   line each: lite is a handful of calls and a 7-day window; standard adds an
   hourly profile and flags; deep widens to 30 days and walks everything.

Also confirm the output location. Default `/Dashboards/<filespace name>/`
inside the filespace. Offer a local folder if they do not want it in the
filespace yet.

## Procedure, mount or sdk source

1. Copy `config.example.yaml` to `config.yaml`, set `filespace.root` (mount) or
   `filespace.name` and the token env var (sdk), the budget, and
   `output.publish_to`.
2. If the MCP Server is also available, call `filespace_stats` once and pass
   the stored size through, so the header shows what the customer pays for:
   ```
   python3 scripts/snapshot.py --config config.yaml --stats '{"data_bytes": <n>, "storage_bytes": <n>, "external_files": <n>, "external_bytes": <n>}'
   ```
   Otherwise run it without `--stats`.
3. Render and publish:
   ```
   python3 scripts/render.py --snapshot out/snapshot.json --publish "<mounted root>/Dashboards/<name>"
   ```
   `--publish` also appends a dated copy under `history/` for later trends.
4. Open `out/index.html` or the published copy and check it renders. If a
   browser is available to you, look at it; otherwise confirm the file exists
   and is over 50 KB (the template alone is about 50 KB).

## Procedure, mcp source

Follow `references/mcp-recipe.md`. It maps every field of `snapshot.json` to
the MCP call that fills it, grouped by budget, so you spend exactly what the
user chose. Then write the JSON to `out/snapshot.json` and run
`scripts/render.py` as above. If Python is unavailable, paste the JSON into the
`<script id="ll-snapshot">` block of `templates/dashboard.html` by hand and
save it as `index.html`.

Two audit-trail facts that change how you count. One user-visible save fans
out into several rows (create, write, move, delete of a temp sibling), so read
sequences rather than counting rows. Events can appear a short while after the
operation, so a missing just-made change is lag, not absence.

## Presenting the result

Lead with the path to the dashboard. Then at most three findings from the
data, each one line, drawn from the flags and the folder table. Then the
limits, always, as bullets:

- Snapshot, not live. Say when it was taken and how to refresh.
- Audit covers only the period since it was enabled.
- Tree tiles are a sample if the walk budget clamped (the page says so under Flags).
- Stored size needs MCP or SDK; a mount cannot see it.
- The page opens from the drive or a local server. There is no hosted URL for filespace content.

## Refresh

`refresh: manual` in the config means you regenerate when asked, which spends
tokens each time. `refresh: script` means the user schedules the two scripts
(cron, launchd, Task Scheduler) and spends none. Offer the script route to
anyone who asks for a second refresh.

## Customizing

Everything the customer might change is in `references/customizing.md`: adding
a tile, regrouping folders, renaming actors, swapping the Lab style for their
own, and the schema in `references/snapshot-schema.md`. Ideas for further
tiles, including ones that need MCP-only data such as locks and live change
subscriptions, are in `references/tile-catalog.md`.

## Guardrails

- Never write anywhere in the filespace other than the agreed dashboard folder.
- Never read file contents for this skill. Metadata and the audit trail are enough.
- Never paste tokens or credentials into config files that are committed. The
  sdk source reads the token from an environment variable for that reason.
- Actor names are personal data. Keep them inside the customer's filespace;
  do not copy the snapshot elsewhere without asking.
