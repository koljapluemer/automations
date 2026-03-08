# Project Command Center

Reads project definitions from `project_output_data_folder`, cross-references repo membership via `doc/projects.json`, and generates a browsable project overview HTML page.

## Data model

**Projects** are defined by hand-maintained `*.json` files in `project_output_data_folder` with `"type": "project"`. The automation reads these as the authoritative source — it never writes to this folder.

**Images** are pre-existing `.webp` files in `project_data_output_img_folder`, named `$id.webp`. The automation reads them — it never writes to this folder either.

**Repo membership** is declared in each repo via `doc/projects.json`:
```json
{ "my-project": "runs the data transformation", "other-project": "provides the CMS" }
```
Relationships are many-to-many — a repo can belong to multiple projects, a project can have multiple repos.

**Issues** are markdown files in `doc/issues/*.md`. The first heading in each file is used as the issue name. These are not GitHub issues.

## What it does

1. Counts top-level dirs in `git_project_folder` → feeds "Active Repos" on the dashboard
2. Reads all `*.json` files with `"type": "project"` from `project_output_data_folder`, validates against schema
3. For each project, checks if `$id.webp` exists in the img folder
4. Picks a random project with an image for the dashboard wallpaper
5. Generates the overview HTML (if `project_overview_html` is configured)

## Overview HTML

Two sections:
- **Projects** — collapsible cards (thumbnail + name when collapsed; full image, description, and repo list when expanded). Each repo shows its role and issue count.
- **Repos without projects** — repos not referenced in any `doc/projects.json`.

## Config keys

| Key | Description |
|-----|-------------|
| `git_project_folder` | Root folder containing git repos as direct subdirectories |
| `project_output_data_folder` | Source-of-truth folder for `*.json` project definitions (read-only) |
| `project_data_output_img_folder` | Folder containing `$id.webp` project images (read-only) |
| `project_overview_html` | *(optional)* Output path for the generated overview HTML |

## Schema

`project_json_schema.json` — JSON Schema (draft 2020-12). Required fields: `id`, `name`, `description` (all strings). `type` must be `"project"`. Additional properties allowed.
