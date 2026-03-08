# Project Command Center

Scans all top-level folders in `git_project_folder` and collects structured project data for the dashboard.

## What it does

1. **Discovers projects** — iterates top-level dirs in `git_project_folder`
2. **Validates** — looks for `doc/project.json` in each repo and validates it against `project_json_schema.json` (requires `id`, `name`, `description` strings); skips repos without it or with invalid files
3. **Exports JSON** — copies valid `doc/project.json` to `project_output_data_folder/$id.json`
4. **Exports image** — finds the first local image reference in `README.md` (`![](path)` syntax), converts it to WebP, saves as `project_data_output_img_folder/$id.webp`; projects without an image are excluded from the dashboard pool
5. **Dashboard** — picks a random project that has an image and surfaces `random_project_name` + `random_project_image_path` for display on the wallpaper

## Config keys

| Key | Description |
|-----|-------------|
| `git_project_folder` | Root folder containing git repos as direct subdirectories |
| `project_output_data_folder` | Where validated `$id.json` files are written |
| `project_data_output_img_folder` | Where `$id.webp` images are written |

## Schema

`project_json_schema.json` — JSON Schema (draft 2020-12). Required fields: `id`, `name`, `description` (all strings). Additional properties allowed.
