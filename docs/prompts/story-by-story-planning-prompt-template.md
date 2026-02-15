# Story-by-Story Planning Prompt Template

Use this prompt in a new chat whenever you want a plan for exactly one story.

```md
You are my implementation planning agent for this repository.

MODE:
- PLAN ONLY for one story.
- Do not write implementation code, do not commit
- write plan output into docs/prompts/story-<EPIC-STORYNUMBER>-<STORYTITLE>.md

TARGET STORY:
- <EPIC-NUMBER>: <STORYTITLE>


READ THESE FILES FIRST (in order):
1) @_bmad-output/implementation-artifacts/<story-file>.md
2) @_bmad-output/implementation-artifacts/<direct-dependency-story-files>.md
3) @_bmad-output/planning-artifacts/epics.md
4) @_bmad-output/planning-artifacts/architecture.md
5) @project-context.md
6) @_bmad-output/implementation-artifacts/sprint-status.yaml


PLANNING POLICY (MANDATORY):
- One story only, no future story implementation.
- Hard gate is backend/API/ML (blocking).
- Frontend is soft gate (non-blocking, but must be validated and logged).
- Use deterministic checks where possible.
- Ask questions only if truly blocking, and include a recommended default.

DELIVERABLES:
1) Story scope summary (what is in/out)
2) Acceptance Criteria -> implementation mapping table
3) File-level change plan (likely files to touch)
4) Test plan (unit/integration/API)
5) HARD GATE commands + explicit pass/fail criteria
6) SOFT GATE frontend checks
7) Risks, dependencies, and rollback plan
8) Open questions (max 3, only blockers)

OUTPUT FORMAT (use exactly, reference  story-by-story-planning-response-template.md):
- Section 1: Scope and assumptions
- Section 2: AC mapping table
- Section 3: Implementation plan (task list)
- Section 4: Hard gate (commands + pass criteria)
- Section 5: Soft gate (frontend)
- Section 6: Risks and rollback
- Section 7: Blockers/questions (if any)
```
