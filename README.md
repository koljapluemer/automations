# automations

Personal automation runner.

## Quick start

- Copy `config.yaml.demo` to `config.yaml` and fill in values.
- Run with `uv run automations`.

## Ubuntu dependencies

Install the system packages needed for rendering HTML to an image and setting the wallpaper:

```bash
sudo apt update
sudo apt install -y wkhtmltopdf
```

`wkhtmltoimage` ships with `wkhtmltopdf` on Ubuntu. If you prefer Chromium instead:

```bash
sudo apt update
sudo apt install -y chromium-browser
```

For GNOME wallpaper updates, `gsettings` comes with GNOME. Make sure you are running GNOME on Ubuntu.

## Notes

- Per-automation logs are stored in `runtime/logs/YYYY-MM-DD/`.
- Use `uv run automations --list` to see available automations.
- The wallpaper automation needs `wkhtmltoimage` or `chromium`/`google-chrome` installed for HTML rendering.

## Manual runs

Run just the portfolio publisher automation:

```bash
uv run automations --only publish_portfolio_from_obs
```

Ensure `publish_portfolio_from_obs` is listed under `enabled_automations` in `config.yaml` when running it manually.
