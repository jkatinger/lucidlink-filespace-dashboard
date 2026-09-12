# MCP recipe: building snapshot.json from LucidLink MCP Server calls

Use this when the only route to the filespace is the MCP Server. Each field of
`snapshot.json` (schema in `snapshot-schema.md`) is listed with the tool call
that fills it. Calls are grouped by budget so you spend what the user chose.
Tool names are the MCP Server's default `core` and full toolsets as of the
0.14 line; check `tools/list` if a name differs.

Write the result to `out/snapshot.json`, then run `scripts/render.py`.

## lite, about 5 calls, 7-day window

| Field | Call |
|---|---|
| `stats.*` | `filespace_stats` (entries, data size, storage size, external files) |
| `stats.files`, `stats.dirs` | `count_files` with `path_prefix="/"` (one tree walk, totals only) |
| `folders[].path`, `folders[].files` | `tree` with `max_depth=1`, `max_entries_per_dir=50`, then one `count_files` per top-level folder if the user named folders; otherwise leave `files` as `null` |
| `activity.by_action` | `read_audit_trail` `mode=aggregate` `group_by=action` `time_range=7d` |
| `activity.by_actor` | `read_audit_trail` `mode=aggregate` `group_by=user` `time_range=7d`. Classify `kind` as `human` when the name contains `@`, else `service`, unless the config says otherwise. `reads`, `writes`, `deletes`, `last_seen` may be `null` at this budget. |
| `activity.by_day` | `read_audit_trail` `mode=search` `limit=200` `time_range=7d` gives the newest 200 rows; bucket what you have by day and set a note that days are sampled from the newest 200 events. Or leave `by_day` empty and let the tile say so. |
| `recent` | the same 200 rows filtered to FileWritten, FileCreate, FileDelete, Move, DirectoryCreate, DirectoryDelete, newest 25, collapsed per path and second |
| `cold`, `extensions`, `largest` | leave `cold.buckets` empty, `extensions` empty, `largest` empty. The tiles show their empty states. Add a note. |
| `activity.events` | total from the action aggregate |
| `notes` | say which tiles were skipped for budget and that `by_day` is sampled |

## standard, 20 to 40 calls, 7-day window

Everything in lite, plus:

| Field | Call |
|---|---|
| `folders[].reads`, `writes`, `deletes`, `last_write`, `writers` | one `read_audit_trail` `mode=aggregate` `group_by=action` with `path_prefix=<folder>` per top-level folder, plus `group_by=user` with the same prefix for `writers`. Two calls per folder; cap at the ten busiest folders by `files`. |
| `activity.by_day` | seven calls of `read_audit_trail` `mode=aggregate` `group_by=action` with `time_range='<day>/<next day>'`, one per day. Exact, not sampled. |
| `activity.by_hour` | leave `null`. Hourly buckets need the raw rows. |
| `cold.buckets` | `find_files` with `name_pattern="*"` `limit=1000` gives paths without sizes; call `get_entry` on the largest folders' entries only if the user asked for archive candidates. Otherwise leave buckets empty and note it. |
| `extensions` | `find_files` per extension the user cares about (`*.mov`, `*.mxf`, `*.exr`, `*.wav`), `count_files` for counts. Sizes need `get_entry` per file, so report counts and leave `bytes` as `null`. |
| `locks` | `list_locks_held` if available; list as `[{"path", "holder"}]` |
| `flags` | derive from what you have: an actor with deletes over 100 in the window, no service accounts, a single actor. Keep to the rules in `snapshot.py`. |

## deep, 100 or more calls, 30-day window

Everything in standard with `time_range=30d`, plus:

| Field | Call |
|---|---|
| `activity.by_day` | 30 daily aggregates |
| `activity.by_hour` | `read_audit_trail` `mode=search` `limit=1000` paged by day; bucket by UTC hour |
| `cold.candidates` | `get_entry` on every file in the folders the user named, keep those over the size floor and older than the age floor |
| `extensions[].bytes`, `largest` | `get_entry` per file under the named folders |
| `activity.by_actor[].reads/writes/deletes` | `read_audit_trail` `mode=user_activity` `user=<name>` per actor |

## Rules while collecting

- Never call `read_file`, `read_lines` or `grep_files` for this skill. Metadata and audit only.
- Scope every audit call with `time_range`; logs are month-partitioned and pruned before I/O.
- One desktop save fans out into create, write, move, move, delete of a temp sibling. Read the sequence when building `recent`; do not count the rows as five changes.
- A change made seconds ago may not be in the trail yet. Do not report it as missing.
- If a walk-based tool reports a clamped budget or partial results, copy that sentence into `notes`.
- Skip `/.lucid_audit` paths and the dashboard's own folder when counting activity, or the dashboard inflates its own numbers.
