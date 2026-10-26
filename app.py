"""Teacher Copilot - Dash web app.

Run:  python app.py   then open http://127.0.0.1:8050
"""

from __future__ import annotations


from dash import Dash, Input, Output, State, ctx, dcc, html

import pricing
from agent import ask_teacher_copilot

app = Dash(__name__, title="Teacher Copilot")

COLORS = {
    "midnight": "#111827",
    "burgundy": "#6B1D2A",
    "gold": "#C9A227",
    "parchment": "#F4EBD8",
    "cream": "#FFFDF7",
    "ink": "#2C241B",
    "muted": "#6B6257",
    "border": "#D8C8A8",
    "green": "#2F6B3B",
    "red": "#9B2C2C",
}

CARD = {
    "backgroundColor": COLORS["cream"],
    "padding": "26px 30px",
    "borderRadius": "16px",
    "border": f"1px solid {COLORS['border']}",
    "boxShadow": "0 10px 30px rgba(0,0,0,0.22)",
    "marginBottom": "22px",
}
LABEL = {"fontWeight": "bold", "display": "block", "marginBottom": "8px", "color": COLORS["ink"], "fontSize": "16px"}
PILL = {
    "backgroundColor": COLORS["cream"],
    "color": COLORS["burgundy"],
    "border": f"1px solid {COLORS['burgundy']}",
    "padding": "10px 14px",
    "borderRadius": "20px",
    "cursor": "pointer",
    "fontWeight": "bold",
}
SANS = "Arial, sans-serif"

AGENT_ICONS = {
    "Copilot Lead": "✦",
    "Triage Analyst": "◎",
    "Family Outreach Writer": "✉",
    "Graduation Advisor": "★",
}


def card_title(icon, text):
    return html.Div(
        style={"display": "flex", "alignItems": "center", "gap": "10px", "marginBottom": "14px"},
        children=[
            html.Span(icon, style={"color": COLORS["gold"], "fontSize": "22px"}),
            html.H2(text, style={"fontSize": "22px", "color": COLORS["ink"], "margin": "0"}),
        ],
    )


def meter(value, maximum, label, sublabel=""):
    """Thermometer-style bar."""
    pct = 0 if maximum <= 0 else min(100, 100 * value / maximum)
    color = COLORS["green"] if pct < 60 else (COLORS["gold"] if pct < 90 else COLORS["red"])
    return html.Div(
        style={"marginBottom": "12px", "fontFamily": SANS},
        children=[
            html.Div(
                style={"display": "flex", "justifyContent": "space-between", "fontSize": "14px", "color": COLORS["ink"]},
                children=[html.Strong(label), html.Span(sublabel)],
            ),
            html.Div(
                style={"background": "#EDE3CD", "borderRadius": "8px", "height": "12px", "overflow": "hidden", "marginTop": "4px"},
                children=html.Div(style={"width": f"{max(pct, 1.5):.1f}%", "background": color, "height": "100%"}),
            ),
        ],
    )


# ------------------------------------------------------------------ layout
app.layout = html.Div(
    style={
        "background": "linear-gradient(135deg, #111827 0%, #1F2937 45%, #3A1722 100%)",
        "minHeight": "100vh",
        "fontFamily": "Georgia, 'Times New Roman', serif",
        "padding": "42px 20px",
    },
    children=[
        html.Div(
            style={"maxWidth": "900px", "margin": "0 auto"},
            children=[
                html.Div(
                    style={"textAlign": "center", "color": COLORS["cream"], "marginBottom": "30px"},
                    children=[
                        html.Div("✦", style={"fontSize": "28px", "color": COLORS["gold"], "marginBottom": "4px"}),
                        html.H1("Teacher Copilot", style={"fontSize": "46px", "margin": "0", "letterSpacing": "1px"}),
                        html.P(
                            "A little intelligence for the everyday magic of teaching",
                            style={"fontSize": "17px", "color": "#E8DDBF", "marginTop": "10px"},
                        ),
                    ],
                ),
                # ---- ask panel
                html.Div(
                    style={**CARD, "backgroundColor": COLORS["parchment"], "border": f"1px solid {COLORS['gold']}"},
                    children=[
                        html.Div(
                            style={"display": "flex", "gap": "20px", "flexWrap": "wrap", "marginBottom": "22px"},
                            children=[
                                html.Div(
                                    style={"flex": "2", "minWidth": "220px"},
                                    children=[
                                        html.Label("Course", style=LABEL),
                                        dcc.Dropdown(
                                            id="course-dropdown",
                                            options=[
                                                {"label": "Algebra I", "value": "Algebra I"},
                                                {"label": "Algebra II", "value": "Algebra II"},
                                            ],
                                            value="Algebra I",
                                            clearable=False,
                                            style={"fontFamily": SANS},
                                        ),
                                    ],
                                ),
                                html.Div(
                                    style={"flex": "1", "minWidth": "180px"},
                                    children=[
                                        html.Label("Budget per question (USD)", style=LABEL),
                                        dcc.Input(
                                            id="budget-input",
                                            type="number",
                                            min=0.0005,
                                            step="any",
                                            value=pricing.DEFAULT_RUN_BUDGET_USD,
                                            style={
                                                "width": "100%", "height": "44px", "padding": "0 10px", "lineHeight": "44px", "fontSize": "16px",
                                                "borderRadius": "6px", "border": f"1px solid {COLORS['border']}",
                                                "boxSizing": "border-box", "fontFamily": SANS,
                                            },
                                        ),
                                    ],
                                ),
                            ],
                        ),
                        html.Label("Quick Consultations", style=LABEL),
                        html.Div(
                            style={"display": "flex", "gap": "10px", "flexWrap": "wrap", "marginBottom": "24px"},
                            children=[
                                html.Button("◎ Daily Triage", id="triage-button", n_clicks=0, style=PILL),
                                html.Button("✉ Positive Outreach", id="outreach-button", n_clicks=0, style=PILL),
                                html.Button("★ Graduation Support", id="graduation-button", n_clicks=0, style=PILL),
                            ],
                        ),
                        html.Label("Ask Teacher Copilot", style=LABEL),
                        dcc.Textarea(
                            id="teacher-question",
                            placeholder="What would you like to know about your students today?",
                            style={
                                "width": "100%", "height": "110px", "padding": "14px", "fontSize": "16px",
                                "fontFamily": SANS, "backgroundColor": COLORS["cream"], "color": COLORS["ink"],
                                "borderRadius": "9px", "border": f"1px solid {COLORS['border']}",
                                "boxSizing": "border-box", "resize": "vertical",
                            },
                        ),
                        html.Button(
                            "Ask Teacher Copilot  ✦",
                            id="ask-button",
                            n_clicks=0,
                            style={
                                "marginTop": "18px", "backgroundColor": COLORS["burgundy"], "color": COLORS["cream"],
                                "border": f"1px solid {COLORS['gold']}", "padding": "13px 24px", "fontSize": "16px",
                                "fontWeight": "bold", "borderRadius": "8px", "cursor": "pointer", "fontFamily": "Georgia, serif",
                            },
                        ),
                    ],
                ),
                dcc.Loading(
                    type="circle",
                    color=COLORS["gold"],
                    children=html.Div(
                        id="results",
                        children=html.Div(
                            style=CARD,
                            children=[
                                card_title("✦", "Teacher Copilot Response"),
                                dcc.Markdown(
                                    "*Your consultation will appear here. The Copilot Lead will ask the right "
                                    "specialist, and you will see which agents worked, what it cost, and any safety flags.*",
                                    style={"lineHeight": "1.75", "color": COLORS["ink"], "fontFamily": SANS},
                                ),
                            ],
                        ),
                    ),
                ),
                html.Div(
                    style={
                        "backgroundColor": "#2A2025", "border": f"1px solid {COLORS['gold']}", "padding": "20px 24px",
                        "borderRadius": "12px", "color": "#EFE5CF", "fontSize": "14px", "lineHeight": "1.6",
                    },
                    children=[
                        html.Div(
                            "✦ Evidence before enchantment",
                            style={"fontWeight": "bold", "color": COLORS["gold"], "fontSize": "16px", "marginBottom": "5px"},
                        ),
                        html.Span(
                            "Teacher Copilot bases recommendations on documented student information, distinguishes "
                            "evidence from interpretation, and requires teacher review. It never sends messages, does "
                            "not diagnose students, and hides any note that tries to give the AI instructions."
                        ),
                    ],
                ),
                html.P(
                    "Teacher Copilot • Built for thoughtful, human-centered teaching",
                    style={"textAlign": "center", "color": "#D7C9AC", "fontSize": "13px", "marginTop": "24px"},
                ),
            ],
        )
    ],
)


# ------------------------------------------------------------------ result panels
def render_response(r):
    color = {"ok": COLORS["ink"], "stopped_budget": COLORS["red"], "blocked_daily_budget": COLORS["red"]}.get(r["status"], COLORS["red"])
    return html.Div(
        style=CARD,
        children=[
            card_title("✦", "Teacher Copilot Response"),
            dcc.Markdown(r["text"], style={"lineHeight": "1.7", "color": color, "fontFamily": SANS}),
        ],
    )


def render_trace(r):
    rows = [
        html.Div(
            style={"fontFamily": SANS, "fontSize": "14px", "marginBottom": "10px", "color": COLORS["ink"]},
            children=[html.Strong("✦ Copilot Lead"), " read your question and chose who to ask."],
        )
    ]
    if not r["trace"]:
        rows.append(html.Div("No specialist was called.", style={"fontFamily": SANS, "fontSize": "14px", "color": COLORS["muted"]}))
    for i, step in enumerate(r["trace"], 1):
        tools = step.get("tools") or []
        tool_text = " → ".join(t["tool"] for t in tools) or "(no tools)"
        u = step.get("usage") or {}
        rows.append(
            html.Div(
                style={
                    "borderLeft": f"3px solid {COLORS['gold']}", "padding": "8px 12px", "margin": "0 0 10px 10px",
                    "background": "#FBF6EA", "fontFamily": SANS, "fontSize": "14px", "color": COLORS["ink"],
                },
                children=[
                    html.Div([
                        html.Strong(f"{i}. {AGENT_ICONS.get(step['agent'], '•')} {step['agent']}"),
                        html.Span(f"  ·  {step.get('status')}  ·  {step.get('seconds', '?')}s", style={"color": COLORS["muted"]}),
                    ]),
                    html.Div([html.Em("Asked: "), step["request"]], style={"marginTop": "4px"}),
                    html.Div([html.Em("Tools: "), html.Code(tool_text)], style={"marginTop": "4px"}),
                    html.Div(
                        f"{u.get('input_tokens', 0):,} in · {u.get('cache_read_tokens', 0):,} cached · "
                        f"{u.get('output_tokens', 0):,} out · ${step.get('cost_usd', 0):.5f}",
                        style={"marginTop": "4px", "color": COLORS["muted"]},
                    ),
                ],
            )
        )
    rows.append(
        html.Div(
            style={"fontFamily": SANS, "fontSize": "14px", "color": COLORS["ink"]},
            children=[html.Strong("✦ Copilot Lead"), " combined the specialist reports into the answer above."
                      if r["status"] == "ok" else " stopped the run safely. No answer was produced."],
        )
    )
    return html.Div(style=CARD, children=[card_title("⇄", "How the team worked"), *rows])


def render_cost(r, budget):
    u = r["usage"]
    per_month = pricing.monthly_projection(r["cost_usd"])
    agent_rows = [
        meter(v["cost_usd"], budget, f"{AGENT_ICONS.get(name, '•')} {name}", f"${v['cost_usd']:.5f}")
        for name, v in r["by_agent"].items()
    ]
    return html.Div(
        style=CARD,
        children=[
            card_title("$", "Cost meter"),
            meter(r["cost_usd"], budget, "This question", f"${r['cost_usd']:.5f} of ${budget:.4f} budget"),
            *agent_rows,
            meter(r.get("spent_today", 0), pricing.DAILY_BUDGET_USD, "Today (all questions)",
                  f"${r.get('spent_today', 0):.4f} of ${pricing.DAILY_BUDGET_USD:.2f} daily cap"),
            html.Table(
                style={"width": "100%", "fontFamily": SANS, "fontSize": "14px", "marginTop": "10px", "color": COLORS["ink"]},
                children=[
                    html.Tr([html.Td("Input tokens"), html.Td(f"{u['input_tokens']:,}", style={"textAlign": "right"})]),
                    html.Tr([html.Td("  of which cached"), html.Td(f"{u['cache_read_tokens']:,}", style={"textAlign": "right"})]),
                    html.Tr([html.Td("Cache-write tokens"), html.Td(f"{u['cache_write_tokens']:,}", style={"textAlign": "right"})]),
                    html.Tr([html.Td("Output tokens"), html.Td(f"{u['output_tokens']:,}", style={"textAlign": "right"})]),
                    html.Tr([html.Td("Model calls / tool calls"), html.Td(f"{u['requests']} / {u['tool_calls']}", style={"textAlign": "right"})]),
                    html.Tr([html.Td("Time"), html.Td(f"{r.get('seconds', 0)} s", style={"textAlign": "right"})]),
                    html.Tr([
                        html.Td(html.Strong("At this rate, 8 questions/day for a month")),
                        html.Td(html.Strong(f"${per_month:.3f} per teacher"), style={"textAlign": "right"}),
                    ]),
                ],
            ),
            html.Div(
                f"gpt-6-luna · reasoning effort {r.get('reasoning_effort', 'low')} · $0.10 / $0.01 cached / $0.50 per 1M "
                "input / cached / output tokens",
                style={"fontSize": "12px", "color": COLORS["muted"], "marginTop": "8px", "fontFamily": SANS},
            ),
        ],
    )


def render_safety(r):
    flags = r["safety_flags"]
    if not flags:
        body = [html.Div("✓ No suspicious instructions found in the student records used for this answer.",
                         style={"fontFamily": SANS, "fontSize": "14px", "color": COLORS["green"]})]
    else:
        body = [
            html.Div(
                f"⚠ {len(flags)} note(s) looked like instructions to the AI. They were hidden from every agent. "
                "Please review them yourself:",
                style={"fontFamily": SANS, "fontSize": "14px", "color": COLORS["red"], "marginBottom": "8px", "fontWeight": "bold"},
            )
        ]
        for f in flags:
            body.append(
                html.Div(
                    style={"background": "#FBECEC", "border": f"1px solid {COLORS['red']}", "borderRadius": "8px",
                           "padding": "10px 12px", "marginBottom": "8px", "fontFamily": SANS, "fontSize": "13px"},
                    children=[
                        html.Strong(f"{f['name']} ({f['student_id']}) · {f['field']}"),
                        html.Div([html.Em("Hidden text: "), f"“{f['original_text']}”"], style={"marginTop": "4px"}),
                        html.Div([html.Em("Triggered by: "), html.Code(f["matched"])], style={"marginTop": "4px"}),
                    ],
                )
            )
    return html.Div(style=CARD, children=[card_title("⛨", "Safety check"), *body])


# ------------------------------------------------------------------ callbacks
@app.callback(
    Output("teacher-question", "value"),
    Input("triage-button", "n_clicks"),
    Input("outreach-button", "n_clicks"),
    Input("graduation-button", "n_clicks"),
    prevent_initial_call=True,
)
def fill_quick_prompt(*_):
    return {
        "triage-button": "Who needs my attention today, and why?",
        "outreach-button": "Which students would be good candidates for positive family outreach today? Draft a message for the top one.",
        "graduation-button": "Which students may need graduation support, and what should I review?",
    }.get(ctx.triggered_id, "")


@app.callback(
    Output("results", "children"),
    Input("ask-button", "n_clicks"),
    State("teacher-question", "value"),
    State("course-dropdown", "value"),
    State("budget-input", "value"),
    prevent_initial_call=True,
)
def answer_question(_, question, course, budget):
    if not question or not question.strip():
        return html.Div(style=CARD, children=[dcc.Markdown("Please enter a question or choose a quick consultation.")])
    try:
        budget = float(budget) if budget else pricing.DEFAULT_RUN_BUDGET_USD
    except (TypeError, ValueError):
        budget = pricing.DEFAULT_RUN_BUDGET_USD
    r = ask_teacher_copilot(f"{question.strip()}\nThe selected course is {course}.", budget_usd=budget)
    return [render_response(r), render_trace(r), render_cost(r, budget), render_safety(r)]


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8050, debug=False, use_reloader=False)
