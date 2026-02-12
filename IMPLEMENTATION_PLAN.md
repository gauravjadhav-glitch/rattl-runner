# Rattl Runner AI Upgrade - Implementation Plan

## Phase 1: Foundation & AI Services
**Goal**: Enable LLM capabilities and set up the new directory structure.

- [ ] **Infrastructure**: Create new folders:
    - `backend/services/`
    - `backend/agents/`
    - `backend/analysis/` (for crash/improvement logic)
- [ ] **Dependency**: Add `openai` to `requirements.txt`.
- [ ] **LLM Service**: Create `backend/services/llm_service.py`.
    - Function: `ask_llm(context, system_prompt)`
    - Config: Read `OPENAI_API_KEY` from env.

## Phase 2: Failure Analysis Agent (The "Bot")
**Goal**: Move from simple text-diff healing to intelligent root cause analysis.

- [ ] **Failure Analyzer**: Create `backend/ai_bot.py` (or `backend/agents/failure_analyzer.py`).
    - Logic: Build prompt with Step + Error + XML + History.
    - Output: Structured JSON (Failure Type, Root Cause, Suggested Fix).
- [ ] **Integration**: Update `backend/healer.py` to use `FailureAnalyzer` as a fallback or primary analyzer when simple rules fail.

## Phase 3: Crash Detection & Improvement
**Goal**: Add specific analyzers for app health and test quality.

- [ ] **Crash Analyzer**: Create `backend/crash_analyzer.py`.
    - Logic: Regex parse logcat/stacktrace to identify package/module.
- [ ] **Improver Engine**: Create `backend/improver.py`.
    - Logic: Post-run analysis of `intelligent_memory.json` to find flaky steps.

## Phase 4: Agent Orchestration (The "Vision")
**Goal**: Wire it all together into the `runner.py` loop.

- [ ] **Update Runner**:
    - On Exception:
        1. Capture Screenshot & XML.
        2. Call `CrashAnalyzer` (is it a crash?).
        3. Call `FailureAnalyzer` (why did it fail?).
        4. If fixable, Call `Healer` (apply fix).
        5. Update Memory.

## Execution Steps (Immediate)
1. Install `openai`.
2. Create `backend/services/llm_service.py`.
3. Create `backend/ai_bot.py`.
4. Create `backend/crash_analyzer.py`.
