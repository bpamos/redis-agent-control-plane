# AI Commit Policy

## ⚠️ IMPORTANT: Git Commit Approval Required

**DO NOT commit code to git without explicit approval from Brandon.**

## Policy

### ✅ AI Can Do (Without Approval)
- Create files
- Edit files
- Run tests
- Run quality checks (format, lint, type-check)
- Stage files with `git add`
- Show `git status` and `git diff`
- Prepare commit messages

### ❌ AI Cannot Do (Requires Approval)
- **`git commit`** - REQUIRES APPROVAL
- **`git push`** - REQUIRES APPROVAL
- **`git merge`** - REQUIRES APPROVAL
- **`git rebase`** - REQUIRES APPROVAL
- **`git reset`** - REQUIRES APPROVAL
- **`git tag`** - REQUIRES APPROVAL

## Workflow

### Correct Workflow:
1. AI implements changes
2. AI runs tests and quality checks
3. AI stages files with `git add`
4. AI prepares commit message
5. **AI ASKS: "Should I commit these changes?"**
6. Brandon approves or rejects
7. If approved, AI runs `git commit`

### Example:

**AI:**
```
I've completed the implementation:
- Created 5 new files
- Updated 3 existing files
- All tests passing (26/26)
- All quality checks passing

Files staged:
  src/redis_agent_control_plane/rag/chunker.py
  src/redis_agent_control_plane/rag/embedder.py
  tests/test_rag_chunker.py
  requirements.txt

Proposed commit message:
  feat(rag): implement chunker and embedder
  
  - Add adaptive H2/H3 chunking strategy
  - Add sentence-transformers embedder with caching
  - Add unit tests for both modules

Should I commit these changes?
```

**Brandon:** "yes" or "no" or "change the commit message to..."

**AI:** *Only then runs `git commit`*

## Rationale

- Gives Brandon final review before changes are committed
- Allows Brandon to modify commit messages
- Prevents accidental commits of work-in-progress
- Maintains clean git history
- Ensures Brandon is aware of all changes

## Exceptions

None. **Always ask before committing.**

## Reminder for AI Assistants

Before running `git commit`, `git push`, or any destructive git command:

1. **STOP**
2. **ASK**: "Should I commit/push these changes?"
3. **WAIT** for explicit approval
4. **ONLY THEN** proceed

**This policy applies to ALL git commits, no matter how small or obvious.**

