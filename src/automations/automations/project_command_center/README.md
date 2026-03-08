# Project Command Center

Scans all top-level folders in `git_project_folder`, integrates GitHub repo metadata, and collects structured project data for the dashboard.

## What it does

### 1. GitHub fetch (once per day, cached)
Fetches all owned GitHub repos. For repos that have **both** a description **and** a homepage URL set on GitHub, and have a matching local folder in `git_project_folder`:
- If `doc/project.json` **doesn't exist**: creates it with `id`, `name`, `description`, and `url` from GitHub
- If it **exists** but is missing `description` or `url`: fills in the missing fields from GitHub

If `vault_repo_folder` is configured, also writes Obsidian-style markdown notes for all repos.

### 2. Local scan
For each repo dir that has a valid `doc/project.json`:
1. **Validates** against `project_json_schema.json` (requires `id`, `name`, `description` strings)
2. **Exports JSON** to `project_output_data_folder/$id.json` (as `{type, name, description, rows, cols}`)
3. **Exports image** — finds the first local image in `README.md` (`![](path)` syntax), converts to WebP, saves as `project_data_output_img_folder/$id.webp`; repos without an image are excluded from the dashboard pool
4. **Dashboard** — picks a random project with an image and surfaces `random_project_name` + `random_project_image_path`; also exposes `active_count` from GitHub for the stats panel

## Config keys

| Key | Description |
|-----|-------------|
| `git_project_folder` | Root folder containing git repos as direct subdirectories |
| `project_output_data_folder` | Where validated `$id.json` files are written |
| `project_data_output_img_folder` | Where `$id.webp` images are written |
| `github_username` | GitHub username for API auth |
| `github_token` | GitHub personal access token |
| `vault_repo_folder` | *(optional)* Obsidian folder to write repo notes into |

## Force re-fetch

```bash
uv run automations --force-github
```

## Schema

`project_json_schema.json` — JSON Schema (draft 2020-12). Required fields: `id`, `name`, `description` (all strings). Additional properties allowed.
