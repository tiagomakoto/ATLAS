## Project
Delta Chaos is a quantitative volatility-selling system for Brazilian options markets (B3),
trading CSP, Bull Put Spread and Bear Call Spread on VALE3, PETR4, BOVA11 and BBAS3 via a
modular Python architecture. ATLAS is its operational interface: React frontend + FastAPI
backend + WebSocket pipeline, replacing Google Colab as the primary control surface.
The sole operator is the CEO — no team. Current phase: paper trading.

## Architecture
Pipeline: TAPE (market data ingestion) → ORBIT (regime classification: ALTA/BAIXA/
LATERAL_BULL/LATERAL_BEAR/LATERAL/RECUPERACAO/PANICO) → TUNE (TP/STOP optimization
via Optuna, 200 trials TPE) → GATE (historical validation, 8 criteria) → FIRE (strategy
selection and order sizing) → BOOK (trade registry) → REFLECT (edge quality monitoring,
states A–E, sizing multiplier).
ATLAS integrates with Delta Chaos exclusively via dc_runner.py: subprocess per module,
events emitted over WebSocket, consumed by React frontend in real time.
Changes in upstream modules (TAPE, ORBIT) can cascade. Always trace impact downstream
before implementing.

## Financial Safety
This system sends real orders to B3. Never modify FIRE or GATE modules without explicit
instruction. When in doubt, do nothing — a missed trade is safer than an unintended one.

## Model Strategy
Use Opus for all thinking-heavy work. Use Sonnet as default executor.
Reserve Haiku only for grunt work with zero ambiguity.

### Opus (thinking, planning, reviewing)
- First contact with any new task: always analyze before touching code
- Architecture decisions and system design
- Debugging complex or non-obvious issues
- Code review before marking a task done
- Any time you're uncertain — escalate to Opus reasoning, don't guess

### Sonnet (default executor)
- Feature implementation once plan exists
- Refactors with clear scope
- Writing tests based on existing patterns
- Documentation

### Haiku (fast, zero-ambiguity only)
- Renaming, formatting, moving files
- Boilerplate generation from a template
- Simple find-and-replace across files

## Workflow Rule
For any non-trivial task:
1. Think first (Opus) — understand the problem, identify risks, produce a plan
2. Execute (Sonnet) — implement the plan step by step
3. Review (Opus) — verify correctness, catch edge cases, check for regressions

Never jump straight to execution on tasks that involve architecture,
cross-cutting concerns, or anything you haven't done before in this codebase.

## Before Coding
If the task is ambiguous or you lack context, ask clarifying questions
before writing any code. Never assume intent.

## Tests
Always run existing tests before and after changes.
Never delete or skip tests to make the suite pass.

## Commits
Never commit unless explicitly asked.
When committing, write descriptive messages (what changed and why).

## Git
Never create worktrees. Make all changes directly on the current branch.