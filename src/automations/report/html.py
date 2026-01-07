from __future__ import annotations

from ..models import ReportElement, ReportModel


def render_report(model: ReportModel) -> str:
    timestamp = model.generated_at.strftime("%Y-%m-%d %H:%M")
    warning_html = ""
    if model.warnings:
        warning_html = f"""
        <div class=\"mt-10 rounded-2xl border border-amber-400/40 bg-amber-500/10 px-6 py-4 text-sm text-amber-100\">
          <p class=\"text-xs font-semibold uppercase tracking-[0.3em] text-amber-300\">Attention</p>
          <p class=\"mt-2 text-base font-semibold\">Partial data available ({len(model.warnings)} issue(s))</p>
          <p class=\"mt-1 text-amber-200/80\">Review runtime logs for details.</p>
        </div>
        """

    elements_html = "\n".join(_render_element(element) for element in model.elements)

    return f"""<!DOCTYPE html>
<html lang=\"en\">
  <head>
    <meta charset=\"UTF-8\" />
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\" />
    <title>Automation Snapshot</title>
    <script src=\"https://cdn.tailwindcss.com\"></script>
    <style>
      html,
      body {{
        width: {model.screen_width}px;
        height: {model.screen_height}px;
        margin: 0;
        padding: 0;
        overflow: hidden;
        background: #0f172a;
      }}

      body {{
        font-family: ui-sans-serif, system-ui, -apple-system, "Segoe UI", sans-serif;
        color: #e2e8f0;
      }}

      .glass-panel {{
        background: #111827;
        border: 1px solid #1f2937;
      }}

      .stat-card {{
        border-radius: 12px;
        padding: 16px;
        position: relative;
        overflow: hidden;
      }}

      .stat-label {{
        font-size: 10px;
        letter-spacing: 0.15em;
        text-transform: uppercase;
      }}

      .stat-value {{
        font-family: ui-sans-serif, system-ui, -apple-system, "Segoe UI", sans-serif;
        font-size: 32px;
        line-height: 1;
        font-weight: 600;
      }}

      .panel-error {{
        border-color: rgba(248, 113, 113, 0.6);
        background: #2a1318;
      }}

      .panel-warn {{
        border-color: rgba(251, 191, 36, 0.6);
        background: #2a1f10;
      }}

    </style>
  </head>
  <body>
    <div class=\"relative w-full h-full overflow-hidden\">
      <main class=\"relative z-10 flex h-full w-full flex-col px-20 py-16\">
        <div class=\"flex justify-end text-xs text-slate-400\">
          <span class=\"uppercase tracking-[0.35em]\">Generated</span>
          <span class=\"ml-4 text-sm font-semibold text-slate-100\">{timestamp}</span>
        </div>

        <section class=\"mt-8 grid grid-cols-4 gap-6 auto-rows-auto\">
          {elements_html}
        </section>

        {warning_html}
      </main>
    </div>
  </body>
</html>
"""


def _render_element(element: ReportElement) -> str:
    col_span = max(1, int(element.col_span))
    row_span = max(1, int(element.row_span))
    style = f"grid-column: span {col_span}; grid-row: span {row_span};"
    status_class = ""
    if element.status == "error":
        status_class = " panel-error"
    elif element.status == "warn":
        status_class = " panel-warn"

    if element.kind == "image":
        src = element.data.get("src")
        alt = element.data.get("alt") or element.title or ""
        if src:
            title_html = ""
            if element.title:
                title_html = f'<p class="stat-label text-slate-300">{element.title}</p>'
            return f"""
            <div class=\"glass-panel stat-card{status_class}\" style=\"{style}\">
              {title_html}
              <div class=\"mt-6 flex h-full items-center justify-center\">
                <img src=\"{src}\" alt=\"{alt}\" class=\"max-h-full max-w-full rounded-2xl\" />
              </div>
            </div>
            """

    title = element.title or "Untitled"
    value = element.value or "N/A"

    return f"""
    <div class=\"glass-panel stat-card{status_class}\" style=\"{style}\">
      <p class=\"stat-label text-slate-300\">{title}</p>
      <div class=\"mt-3 flex items-end\">
        <span class=\"stat-value text-slate-50\">{value}</span>
      </div>
    </div>
    """
