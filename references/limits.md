# Limits and gotchas

State these to the user when presenting a dashboard. A gap named plainly beats
a smooth page that hides it.

## Audit trail

- **It must be enabled**, per filespace, by an admin. Only events after that moment exist. A filespace that turned audit on last week has one week of history, however old the files are.
- **Recording lag.** An event can take a short while to appear in the trail. A just-made change that is missing is lag, not loss.
- **Fan-out.** One save in a desktop app can emit create, write, move, move, delete on a temp sibling. The ticker collapses rows by path and second; the pulse counts raw rows. Say "audit events", not "file changes", when quoting the pulse.
- **Renames break history.** A moved file's earlier events sit under its old path. Folder totals after a large reorganization undercount.
- **Reads include the dashboard's own reads** if it lives in the filespace and someone opens it. `snapshot.py` skips `/.lucid_audit`; add the dashboard folder to `folders.exclude` if it becomes visible in the numbers.
- **Timestamps are UTC.** The hourly profile is UTC. Convert before calling anything "off hours".

## Tree walk

- **Budgets clamp.** `lite` stops at 3,000 entries, `standard` at 40,000, `deep` at 400,000, or at the time limit. When clamped, tree-derived tiles (cold and hot, what the bytes are, folder file counts) are a sample. The page says so under Flags.
- **Excluded names.** `.git`, `.venv`, `node_modules`, `__pycache__`, `.DS_Store` and system folders are skipped by default. Counts will be lower than the MCP `filespace_stats` entry count for that reason.
- **Stored size is invisible through a mount.** Pass it with `--stats` from the MCP `filespace_stats` tool or use the `sdk` source.
- **mtime is modification, not access.** Cold-and-hot buckets use modification time. Data that is read daily but never written looks cold. Combine with audit reads at the deep budget for a true "nobody opens this" list.

## The page

- **A snapshot.** Not live. The header shows when it was taken.
- **No hosted URL.** Filespace content has no remote-fetchable URL. The page is opened from the mounted drive or served locally by the customer. A direct link launches the desktop client for people who already have access.
- **Google Fonts.** The template loads Inter from Google Fonts. Offline it falls back to the system font. Remove the link for fully offline use.
- **Personal data.** Actor names are people. Keep the page inside the filespace unless the customer says otherwise.

## Honest framing

Anyone could build this on S3 plus a log pipeline plus a metadata index.
What LucidLink adds is that the audit trail, the shared namespace, locks and
service accounts already exist, so the dashboard is zero setup and lives next
to the files it describes. Say that, and do not claim more.
