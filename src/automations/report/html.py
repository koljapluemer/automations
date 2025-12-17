from __future__ import annotations

from ..models import ReportElement, ReportModel


def render_report(model: ReportModel) -> str:
    timestamp = model.generated_at.strftime("%Y-%m-%d %H:%M")
    warning_html = ""
    if model.warnings:
        warning_html = f"""
        <div class=\"mt-10 rounded-2xl border border-amber-200/70 bg-amber-50/70 px-6 py-4 text-sm text-amber-900\">
          <p class=\"text-xs font-semibold uppercase tracking-[0.3em] text-amber-700\">Attention</p>
          <p class=\"mt-2 text-base font-semibold\">Partial data available ({len(model.warnings)} issue(s))</p>
          <p class=\"mt-1 text-amber-800/80\">Review runtime logs for details.</p>
        </div>
        """

    elements_html = "\n".join(_render_element(element) for element in model.elements)

    return f"""<!DOCTYPE html>
<html lang=\"en\">
  <head>
    <meta charset=\"UTF-8\" />
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\" />
    <title>Automation Snapshot</title>
    <link rel=\"preconnect\" href=\"https://fonts.googleapis.com\" />
    <link rel=\"preconnect\" href=\"https://fonts.gstatic.com\" crossorigin />
    <link
      href=\"https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=Instrument+Serif:ital@0;1&display=swap\"
      rel=\"stylesheet\"
    />
    <script src=\"https://cdn.tailwindcss.com\"></script>
    <style>
      :root {{
        --screen-width: {model.screen_width}px;
        --screen-height: {model.screen_height}px;
        --ink: #0b0f1a;
        --mist: #e6ecef;
        --accent: #f3b34c;
        --panel: rgba(255, 255, 255, 0.72);
        --panel-stroke: rgba(15, 23, 42, 0.12);
      }}

      html,
      body {{
        width: var(--screen-width);
        height: var(--screen-height);
        margin: 0;
        padding: 0;
      }}

      body {{
        font-family: "Space Grotesk", "Segoe UI", sans-serif;
        color: var(--ink);
        background: radial-gradient(circle at 15% 20%, #f7ead8 0%, transparent 45%),
          radial-gradient(circle at 80% 15%, #d8eef7 0%, transparent 50%),
          linear-gradient(120deg, #fef7ec 0%, #ecf4fb 55%, #f4f6ff 100%);
      }}

      .glass-panel {{
        background: var(--panel);
        border: 1px solid var(--panel-stroke);
        box-shadow: 0 30px 70px rgba(15, 23, 42, 0.18);
        backdrop-filter: blur(18px);
      }}

      .stat-card {{
        border-radius: 26px;
        padding: 30px;
        position: relative;
        overflow: hidden;
        animation: floatIn 900ms ease both;
      }}

      .stat-card::after {{
        content: "";
        position: absolute;
        inset: auto -30% -60% -30%;
        height: 120%;
        background: radial-gradient(circle at 50% 10%, rgba(243, 179, 76, 0.35), transparent 55%);
        opacity: 0.7;
      }}

      .stat-label {{
        font-size: 14px;
        letter-spacing: 0.3em;
        text-transform: uppercase;
      }}

      .stat-value {{
        font-family: "Instrument Serif", "Times New Roman", serif;
        font-size: 84px;
        line-height: 1;
      }}

      .panel-error {{
        border-color: rgba(244, 63, 94, 0.4);
        background: rgba(255, 228, 230, 0.6);
      }}

      .panel-warn {{
        border-color: rgba(245, 158, 11, 0.4);
        background: rgba(254, 243, 199, 0.7);
      }}

      @keyframes floatIn {{
        0% {{
          opacity: 0;
          transform: translateY(30px);
        }}
        100% {{
          opacity: 1;
          transform: translateY(0);
        }}
      }}

      @keyframes drift {{
        0% {{
          transform: translateY(0px);
        }}
        50% {{
          transform: translateY(-12px);
        }}
        100% {{
          transform: translateY(0px);
        }}
      }}
    </style>
  </head>
  <body>
    <div class=\"relative w-full h-full overflow-hidden\">
      <div class=\"absolute -top-24 -left-32 h-96 w-96 rounded-full bg-amber-300/40 blur-3xl\" style=\"animation: drift 6s ease-in-out infinite;\"></div>
      <div class=\"absolute bottom-0 right-0 h-[520px] w-[520px] rounded-full bg-sky-300/40 blur-3xl\" style=\"animation: drift 8s ease-in-out infinite;\"></div>

      <main class=\"relative z-10 flex h-full w-full flex-col px-20 py-16\">
        <header class=\"flex items-start justify-between\">
          <div>
            <p class=\"text-xs font-semibold tracking-[0.45em] text-slate-500\">AUTOMATIONS</p>
            <h1 class=\"mt-4 text-5xl font-semibold text-slate-900\">
              Daily Systems Pulse
            </h1>
            <p class=\"mt-3 max-w-xl text-lg text-slate-600\">
              A lightweight snapshot of your knowledge base and developer surface area.
            </p>
          </div>
          <div class=\"text-right text-sm text-slate-500\">
            <p class=\"uppercase tracking-[0.4em]\">Generated</p>
            <p class=\"mt-2 text-lg font-semibold text-slate-800\">{timestamp}</p>
          </div>
        </header>

        <section class=\"mt-14 grid grid-cols-2 gap-10 auto-rows-[1fr]\">
          {elements_html}
        </section>

        {warning_html}

        <footer class=\"mt-auto flex items-end justify-between text-sm text-slate-500\">
          <div>
            <p class=\"uppercase tracking-[0.3em]\">Screen</p>
            <p class=\"mt-2 text-base font-semibold text-slate-800\">{model.screen_width} x {model.screen_height}</p>
          </div>
          <div class=\"text-right\">
            <p class=\"uppercase tracking-[0.3em]\">Next step</p>
            <p class=\"mt-2 text-base font-semibold text-slate-800\">Render to wallpaper</p>
          </div>
        </footer>
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
            return f"""
            <div class=\"glass-panel stat-card{status_class}\" style=\"{style}\">
              <p class=\"stat-label text-slate-500\">{element.title or "Image"}</p>
              <div class=\"mt-6 flex h-full items-center justify-center\">
                <img src=\"{src}\" alt=\"{alt}\" class=\"max-h-full max-w-full rounded-2xl\" />
              </div>
            </div>
            """

    title = element.title or "Untitled"
    value = element.value or "N/A"
    note = element.note or ""

    return f"""
    <div class=\"glass-panel stat-card{status_class}\" style=\"{style}\">
      <p class=\"stat-label text-slate-500\">{title}</p>
      <div class=\"mt-6 flex items-end justify-between\">
        <span class=\"stat-value text-slate-900\">{value}</span>
        <span class=\"text-sm text-slate-500\">{note}</span>
      </div>
    </div>
    """
