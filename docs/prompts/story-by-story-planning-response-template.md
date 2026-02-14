# Story-by-Story Planning Response Template

Use this as the required output shape from the planning agent.

```md
# Story <id> Plan

## Section 1: Scope and assumptions
- In scope:
- Out of scope:
- Dependencies:

## Section 2: AC mapping table
| AC | Planned change | Tests | Evidence at gate |
|----|----------------|-------|------------------|

## Section 3: Implementation plan (task list)
1. ...
2. ...
3. ...

Likely files:
- `...`
- `...`

## Section 4: Hard gate (commands + pass criteria)
```bash
# exact commands
```
Pass criteria:
- [ ] ...
- [ ] ...

## Section 5: Soft gate (frontend)
Checks:
- [ ] ...
- [ ] ...
Follow-ups if failing:
- ...

## Section 6: Risks and rollback
- Risks:
- Rollback steps:

## Section 7: Blockers/questions (if any)
1) <question> (Recommended: <default>)
```
