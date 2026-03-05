# AUGGIE.md

## Purpose
- This file defines how Auggie (AI assistant) should operate when working in this repository
- Ensures consistent, safe, and predictable development workflow
- Minimizes risk while maximizing productivity through clear boundaries and checklists
- Works in conjunction with TASKS.md (task definitions) and CONTEXT.md (architecture context)

## ⚠️ CRITICAL: Git Commit Policy

**DO NOT commit code to git without explicit approval from Brandon.**

See `AI_COMMIT_POLICY.md` for full details.

**Before running `git commit`, `git push`, or any destructive git command:**
1. **STOP**
2. **ASK**: "Should I commit/push these changes?"
3. **WAIT** for explicit approval
4. **ONLY THEN** proceed

## 🔒 CRITICAL: Security and Sensitive Information

**NEVER include sensitive information in code, documentation, or any tracked files.**

See `SECURITY.md` for full security guidelines.

**Protected Information:**
- ❌ Passwords, API keys, tokens, secrets
- ❌ Database credentials (usernames, passwords, connection strings)
- ❌ Redis Cloud URIs with credentials (host, port, password)
- ❌ Private endpoints or internal URLs
- ❌ Any real credentials or production configuration

**Safe Practices:**
- ✅ Use environment variables (`.env` file, gitignored)
- ✅ Use placeholders in examples (`YOUR_PASSWORD`, `YOUR_HOST`)
- ✅ Use localhost for development examples
- ✅ Redact real endpoints in documentation (`[REDACTED]`)
- ✅ Provide `.env.example` templates with safe placeholders

**Before creating or modifying files:**
1. **CHECK**: Does this file contain or reference credentials?
2. **VERIFY**: Are all credentials loaded from environment variables?
3. **CONFIRM**: Are examples using placeholders or localhost?
4. **ENSURE**: Real credentials are only in `.env` (gitignored)

## Operating Principles

**Low blast radius:**
- Make the smallest change that works
- Touch as few files as possible
- Prefer editing existing files over creating new ones

**Plan-first:**
- Propose a brief plan before coding when task isn't trivial
- Get confirmation on approach for non-obvious changes

**No drive-by refactors:**
- Don't refactor code unrelated to the current task
- Don't fix formatting/style issues outside the scope
- Don't "improve" working code unless explicitly asked

**Respect constraints:**
- Always check TASKS.md for active tasks and scope boundaries
- Always check CONTEXT.md before starting work
- Honor architectural decisions and conventions
- Stay within defined non-goals

**When blocked:**
- Output "BLOCKED: <what's needed>" and ask for clarification
- Do not guess at requirements, APIs, or infrastructure details
- Do not invent product features or capabilities

## Before Starting Work

**Pre-flight checklist:**

1. **Check ACTIVE_TASK** in TASKS.md Execution Gate
   - If ACTIVE_TASK is NONE → you may only edit TASKS.md to propose tasks
   - If ACTIVE_TASK is set → you may only work on that task

2. **Restate scope** (in/out)
   - What files will you touch?
   - What is explicitly out of scope?

3. **Confirm understanding**
   - What is the definition of done?
   - What tests will you run?
   - What are the acceptance criteria?

4. **Check doc alignment**
   - README.md = external overview (what users see)
   - CONTEXT.md = current truth architecture (what exists today)
   - TASKS.md = execution gate + backlog (what's next)
   - notes/ = history and deep reports (what happened)

## Task Gating Rules

**Only execute ACTIVE task scope; otherwise BLOCKED.**

- If ACTIVE_TASK is set in TASKS.md → work ONLY on that task
- If ACTIVE_TASK is NONE → do NOT make code changes (only propose tasks)
- If scope is unclear → output "BLOCKED: <reason>" and stop
- If you need to work on something else → ask to change ACTIVE_TASK first

**Scope discipline:**
- Respect "Scope (In)" and "Scope (Out)" strictly
- Do NOT make drive-by refactors
- Do NOT touch files outside "Files Likely Touched"
- Do NOT add features not in acceptance criteria

## Doc Alignment Rule

**Each doc file has a specific role:**

- **README.md** = External overview
  - What users see first
  - High-level features and status
  - Quick start and installation
  - Roadmap (completed + future)

- **CONTEXT.md** = Current truth architecture
  - What exists today (present tense)
  - Module layout and conventions
  - Runtime assumptions
  - Non-goals and constraints

- **TASKS.md** = Execution gate + backlog
  - ACTIVE_TASK (what's being worked on now)
  - Task definitions with acceptance criteria
  - Completion notes (3-6 bullets + link to notes/)

- **notes/** = History and deep reports
  - Phase completion summaries
  - Research findings
  - Detailed test results
  - Architecture decisions

**When updating docs:**
- Keep README.md user-facing and high-level
- Keep CONTEXT.md present-tense (no history)
- Keep TASKS.md focused on execution (trim completion notes)
- Move detailed reports to notes/

## Standard Workflow

1. **Restate the task** - Confirm understanding and define success criteria
2. **Identify files** - List files likely to touch and explain why each is needed
3. **Implement** - Make minimal changes to achieve the goal
4. **Verify** - Add/update tests OR provide a deterministic smoke-check command
5. **Run checks** - Execute lint/type/tests if available in the project
6. **Summarize** - Report what changed, commands run, files touched, risks, next steps

## Definition of Done

Before marking any task complete, verify:

- [ ] Code builds/runs without errors
- [ ] Tests pass (existing + new if applicable)
- [ ] No new lint or type errors introduced
- [ ] No unrelated formatting or style churn
- [ ] Documentation updated if public APIs changed
- [ ] CONTEXT.md updated if architecture changed
- [ ] No TODOs or placeholder code left behind (unless explicitly agreed)
- [ ] Changes align with constraints in CONTEXT.md
- [ ] **SECURITY**: No credentials or sensitive data in tracked files
- [ ] **SECURITY**: All credentials loaded from environment variables
- [ ] **SECURITY**: Examples use placeholders or localhost only
- [ ] **SECURITY**: `.env` file not modified or committed

## Change Boundaries

**DO NOT change the following unless the task explicitly requests it:**
- Infrastructure configuration (Docker, K8s, cloud resources)
- Dependencies (package.json, requirements.txt, go.mod, etc.) - use package managers if needed
- Global configuration files (tsconfig, eslint, pytest.ini, etc.)
- CI/CD pipelines or GitHub Actions
- Database schemas or migrations (without explicit approval)
- Authentication or security-related code
- `.env` file (contains credentials - never commit)
- `.gitignore` (unless adding new sensitive files to ignore)

**DO NOT include in any files:**
- Real passwords, API keys, or credentials
- Production database connection strings
- Redis Cloud URIs with credentials
- Private endpoints or internal URLs

**When in doubt:** Ask before modifying.

## Branching & Commits

**Branching:**
- Default: one feature branch per task (e.g., `feature/add-rag-endpoint`)
- Branch from `main` unless user specifies otherwise
- If multiple parallel tasks/agents: separate branches required

**Commits:**
- Make atomic commits (one logical change per commit)
- Use conventional commit format:
  ```
  <type>(<scope>): <description>
  
  [optional body]
  ```
  Types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`
  
**Example:**
```
feat(rag): add vector similarity search endpoint

- Implement /api/search endpoint
- Add Redis vector store integration
- Include basic error handling
```

## Output Format

Use this template for all non-trivial responses:

```
### Plan
- What I'm going to do
- Why this approach
- Files I'll touch

### Changes
- Brief description of each change made
- Key decisions or tradeoffs

### Commands Run
- `command 1` - what it does
- `command 2` - what it does

### Files Touched
- path/to/file1.py - what changed
- path/to/file2.py - what changed

### Notes/Risks
- Any gotchas or things to watch
- Known limitations of the implementation

### Next Step
- What should happen next (or "Ready for review")
```

## Quick Start Prompts

**Small bugfix:**
```
Fix the bug where [specific behavior] happens when [condition].
Expected: [correct behavior]
Files likely involved: [file1, file2]
```

**Feature addition:**
```
Add [feature name] that does [specific thing].
Acceptance criteria:
- [ ] criterion 1
- [ ] criterion 2
Constraints: [any specific requirements]
```

**Bounded refactor:**
```
Refactor [specific component/function] to [improvement].
Scope: ONLY touch [specific files/modules]
Do NOT change: [things to leave alone]
Success: [how to verify it works]
```

## Tips for Effective Collaboration

- **Be specific:** "Add error handling to the Redis connection" beats "improve the code"
- **Provide context:** Link to relevant docs, error messages, or examples
- **Set boundaries:** Explicitly state what should NOT change
- **Verify incrementally:** Ask Auggie to run tests after each logical step
- **Review diffs:** Check the changes before committing

## Emergency Stops

If Auggie is:
- Making changes outside the stated scope
- Creating unnecessary files
- Refactoring unrelated code
- Guessing at requirements

**Say:** "STOP - revert changes and let's clarify the scope"

---

# Last Completed Work

**Branch:** deterministic
**Phases A-F Complete:** 2026-03-05
- Phase F: Context Pack Builder with RAG integration
- 62 passing tests, 11 skipped (integration tests)
- All orchestration phases complete
📄 See `notes/DETERMINISTIC_BRANCH_SUMMARY.md` for full history

# Next Work: V1 Completion Tasks

**Status:** In Progress (2/6 complete)
**Goal:** Transform from "phases complete" to "v1 production-ready"

**Completed tasks:**
- ✅ [V1-001] Data-driven routing registry (2026-03-04)
- ✅ [V1-002] Versioned context pack schema (2026-03-05)

**Remaining tasks (see TASKS.md):**
- [ ] [V1-003] Reusable step library
- [ ] [V1-004] Golden path CLI
- [ ] [V1-005] CI anti-rot guardrails
- [ ] [V1-006] API clarity decision

**Next up:** [V1-003] Reusable step library

---

