from __future__ import annotations

from pathlib import Path
import shutil
import subprocess
from typing import Any

from .base import Automation
from ..context import AutomationContext
from ..models import AutomationResult, AutomationSpec, ReportElement


class WallpaperFromReportAutomation(Automation):
    spec = AutomationSpec(
        id="wallpaper_from_report",
        title="Wallpaper from Report",
        description="Render the HTML report to an image and set the Ubuntu wallpaper.",
        default_enabled=True,
        stage="post_report",
    )

    def run(self, ctx: AutomationContext) -> dict[str, Any]:
        settings = ctx.settings_for(self.spec.id, default_enabled=self.spec.default_enabled)
        html_path = _resolve_html_path(ctx)

        output_path = _resolve_output_path(settings.config, ctx)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        renderer = settings.config.get("renderer")
        renderer = str(renderer) if renderer else "auto"

        _render_html_to_image(
            html_path=html_path,
            output_path=output_path,
            screen_width=ctx.config.report.screen_width,
            screen_height=ctx.config.report.screen_height,
            renderer=renderer,
        )

        set_wallpaper = settings.config.get("set_wallpaper", True)
        if set_wallpaper:
            picture_options = settings.config.get("picture_options", "zoom")
            _set_wallpaper(output_path, picture_options=str(picture_options))

        return {
            "html_path": str(html_path),
            "image_path": str(output_path),
            "renderer": renderer,
            "set_wallpaper": bool(set_wallpaper),
        }

    def build_report(self, result: AutomationResult) -> list[ReportElement]:
        return []


def _resolve_html_path(ctx: AutomationContext) -> Path:
    html_path = ctx.report_path or ctx.config.report.output_html
    if not html_path.exists():
        raise FileNotFoundError(f"Report HTML not found: {html_path}")
    return html_path


def _resolve_output_path(config: dict[str, Any], ctx: AutomationContext) -> Path:
    raw = config.get("output_image") or config.get("output_path") or "output/wallpaper.png"
    path = Path(str(raw)).expanduser()
    if not path.is_absolute():
        path = ctx.config.project_root / path
    return path


def _render_html_to_image(
    html_path: Path,
    output_path: Path,
    screen_width: int,
    screen_height: int,
    renderer: str,
) -> None:
    html_uri = html_path.resolve().as_uri()

    if renderer != "auto":
        _run_renderer(renderer, html_uri, output_path, screen_width, screen_height)
        return

    for candidate in ("wkhtmltoimage", "chromium", "chromium-browser", "google-chrome", "google-chrome-stable"):
        if shutil.which(candidate):
            _run_renderer(candidate, html_uri, output_path, screen_width, screen_height)
            return

    raise RuntimeError(
        "No HTML renderer available. Install wkhtmltoimage or chromium/google-chrome for headless rendering."
    )


def _run_renderer(
    renderer: str,
    html_uri: str,
    output_path: Path,
    screen_width: int,
    screen_height: int,
) -> None:
    if renderer == "wkhtmltoimage":
        cmd = [
            renderer,
            "--width",
            str(screen_width),
            "--height",
            str(screen_height),
            html_uri,
            str(output_path),
        ]
    elif renderer in {"chromium", "chromium-browser", "google-chrome", "google-chrome-stable"}:
        cmd = [
            renderer,
            "--headless",
            "--disable-gpu",
            "--hide-scrollbars",
            "--force-device-scale-factor=1",
            f"--window-size={screen_width},{screen_height}",
            f"--screenshot={output_path}",
            html_uri,
        ]
    else:
        raise RuntimeError(f"Unsupported renderer: {renderer}")

    result = subprocess.run(cmd, check=False, capture_output=True, text=True)
    if result.returncode != 0:
        stderr = result.stderr.strip() or result.stdout.strip()
        raise RuntimeError(f"Renderer '{renderer}' failed: {stderr}")


def _set_wallpaper(image_path: Path, picture_options: str) -> None:
    gsettings = shutil.which("gsettings")
    if not gsettings:
        raise RuntimeError("gsettings not available to set wallpaper")

    uri = image_path.resolve().as_uri()
    _run_gsettings(
        [gsettings, "set", "org.gnome.desktop.background", "picture-options", picture_options]
    )
    _run_gsettings([gsettings, "set", "org.gnome.desktop.background", "picture-uri", uri])
    _run_gsettings(
        [gsettings, "set", "org.gnome.desktop.background", "picture-uri-dark", uri],
        allow_fail=True,
    )


def _run_gsettings(cmd: list[str], allow_fail: bool = False) -> None:
    result = subprocess.run(cmd, check=False, capture_output=True, text=True)
    if result.returncode != 0:
        stderr = result.stderr.strip() or result.stdout.strip()
        if allow_fail:
            return
        raise RuntimeError(f"gsettings failed: {stderr}")
