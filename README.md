# Teacher Copilot

A multi-agent assistant for high school teachers. Pick a class and ask a question. A **Copilot Lead** agent passes the work to three specialists:

- **Triage Analyst**: who needs attention today, and why
- **Family Outreach Writer**: keeps positive family contact near 5:1 and drafts messages in the family's language for the teacher to review
- **Graduation Advisor**: flags seniors at risk and lists what to verify with the counselor

The app shows which agents worked, the tokens and dollar cost of every question, and any student note that was hidden because it looked like a prompt injection. Nothing is ever sent automatically.

Built with PydanticAI + Dash, model `gpt-6-luna`. MGT 409 final project, Kanushri Wadhwa.

## Run it (about 3 minutes)

Requires Python 3.10 or newer.

```bash
git clone https://github.com/KANUSHRI1947/teacher-copilot2.git
cd teacher-copilot2
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

**API key.** The app looks for a `.env` file in this folder first, then in the folder **above** it. Either location works. The file needs one of:

```
PORTKEY_API_KEY=...     # course key, gpt-6-luna through Portkey (used if present)
OPENAI_API_KEY=...      # otherwise your own OpenAI key
```

See `.env.example`.

**Start the app:**

```bash
python app.py
```

Then open **http://127.0.0.1:8050**.

## Try these

1. Click **◎ Daily Triage**, then **Ask Teacher Copilot**. The Triage Analyst ranks the class.
2. Click **✉ Positive Outreach**, then Ask. The Family Outreach Writer finds students due for positive contact and drafts a message (Alejandra Cruz's family prefers Spanish).
3. Type *"Draft a message to Jordan Lee's family about his progress."* Jordan's record contains a planted prompt injection. The **Safety check** panel shows that note was hidden from the AI.
4. Set **Budget per question** to `0.0005` and ask anything. The run is stopped by the budget limit.

## Tests (no API key needed)

```bash
python tests/test_safety.py
```

23 checks cover prompt-injection redaction, false positives, the cost math, the per-question budget cap and the daily cap.

`python scripts/run_evidence.py` (uses the API, under $0.10 total) re-runs the token, cost and live-attack measurements used in the report and saves them to `docs/`.

## Files

| File | What it does |
|---|---|
| `app.py` | Dash web app: question panel, agent trace, cost meter, safety panel |
| `agent.py` | Copilot Lead and the 3 specialist agents, budget limits, audit log |
| `Tools.py` | Read-only student-data tools (triage scoring, 5:1 outreach math, message and graduation context) |
| `safety.py` | Prompt-injection scanner that runs on every record before any agent sees it |
| `pricing.py` | Token-to-dollar math, budget-to-token cap, daily spend cap |
| `Data/students.json` | Synthetic class of 9 students (no real student data) |
| `audit_log.jsonl` | Created at run time: every question, answer, agent trace, tokens and cost |

## Safety limits

- **Per question:** $0.01 by default (converted to a hard token cap), 12 model calls and 12 tool calls.
- **Per day:** $1.00 for the whole app. After that it refuses until the next day.
- **Data:** read-only. No tool can send, edit or delete anything.
