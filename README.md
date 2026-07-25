# sheetsai

A natural-language agent for Google Sheets. You ask a question in plain English inside a
sheet, and it reads the sheet, decides what to do, and writes formulas, charts, or new
data back.

## Why I built it

I kept watching people rebuild the same spreadsheet by hand, and I wanted to know whether
an LLM could do it reliably. The interesting part turned out not to be generating formulas.
Models are fine at that. The hard part is that a model asked to write `=VLOOKUP(...)` will
happily produce something syntactically perfect and completely wrong, because it guessed
at where the data actually lives.

That failure mode is what most of this codebase is about.

## The problem: confidently wrong formulas

An early version inferred sheet structure from the first few rows. It worked on clean
sheets and broke on real ones — merged headers, blank spacer rows, a stray total row at
the bottom, two tables side by side on the same tab. The agent would emit a formula
against a range that looked right and silently returned garbage. Nothing errored. The
user just got a wrong number.

So the model no longer guesses. Before any tool runs, the system builds an explicit
picture of the workbook and the agent is given that instead of raw cells:

- `context/spreadsheet_native.py` — finds real data regions, headers, and boundaries
  rather than assuming row 1 is the header and the table starts at A1
- `context/profiling.py` — types each column from its actual values
- `context/formula_parsing.py` — parses existing formulas rather than treating them as text
- `context/dependency.py` — builds a `networkx` DiGraph of cell dependencies, so the agent
  knows what a write would break; also detects circular references
- `context/evaluation.py` — evaluates candidate expressions before they are committed

The tradeoff is latency. Building context costs a round of analysis on every request, and
for a trivial question that is wasted work. I took it anyway: a wrong answer that looks
right is far more expensive than a slow one, because the user has no way to notice it.

## How the agent works

A hand-rolled multi-turn tool-calling loop in `sheetsai/quadratic_engine.py` — no agent
framework. It calls an OpenAI-compatible endpoint (routed through OpenRouter), gets back
tool calls, executes them, feeds results back, and repeats up to `max_turns` (default 8)
until the model stops requesting tools.

I wrote the loop directly because I wanted to control what went into the context window on
each turn. The whole design depends on feeding the model a structured view of the workbook
instead of raw cells, and that is exactly the part a framework abstracts away.

Tools available to the model include reading and writing ranges, setting formulas, sorting,
find-and-replace, cell and conditional formatting, creating sheets and tables, creating
charts, and running Python for anything the other tools cannot express. The Python tool
executes under `RestrictedPython` with a restricted globals dictionary, since the model
writes that code.

## Stack

FastAPI backend (`app.py`), containerized and deployed on AWS App Runner. Google Sheets
access via `gspread` and the Sheets API with OAuth2. Frontend is a Google Apps Script
add-on so it runs inside the sheet rather than in a separate tab. pandas/numpy for column
profiling, networkx for the dependency graph.

## Running it locally

```bash
pip install -r requirements.txt
cp environment.example .env      # fill in your own credentials
./setup_env.sh
python app.py
```

See `ENVIRONMENT_SETUP.md` for the Google service account and OAuth2 setup, and
`QUICK_DEPLOYMENT_GUIDE.md` for App Runner deployment.

No credentials are committed to this repository. `OPENROUTER_API_KEY` and the Google
service account JSON are read from the environment.

## Tests

The A1-notation layer (`sheetsai/a1_notation.py`) — parsing, ranges, offsets, and
round-tripping between A1 strings and `(row, col)` — is covered by unit tests that run in
CI on every push:

```bash
pip install -r requirements-dev.txt
pytest -q
```

## Status

A working prototype, not a product. It has not been run against a large user base, and the
context builder still has gaps — deeply nested formulas and cross-workbook references
are handled poorly. Circular-reference detection works but the recovery path is crude.
