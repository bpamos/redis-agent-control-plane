# Security Guidelines

**IMPORTANT:** This file defines security rules that MUST be followed by all contributors, including AI assistants.

- AI assistants: See `AUGGIE.md` for security requirements in the workflow
- Developers: See `CONTEXT.md` for architectural security constraints
- All: Follow the guidelines below to protect sensitive information

---

## Credentials and Secrets Management

### ✅ Protected Files

The following files contain sensitive information and are **protected from git commits**:

1. **`.env`** - Contains Redis Cloud credentials
   - ✅ Listed in `.gitignore` (line 138)
   - ✅ Verified not tracked by git
   - ✅ Never commit this file

### 📋 Configuration Template

Use **`.env.example`** as a template:
```bash
# Copy the example file
cp .env.example .env

# Edit .env with your actual credentials
# .env is automatically ignored by git
```

### 🔒 What's Protected

**Redis Cloud Credentials:**
- Connection URL with password
- Hostname and port
- Database credentials

**Location:** `.env` file (gitignored)

### 📝 What's Safe to Commit

The following are safe and do NOT contain credentials:
- ✅ `.env.example` - Template with placeholder values
- ✅ Documentation files - Reference localhost or placeholders
- ✅ Test files - Use `redis://localhost:6379` for local testing
- ✅ Code files - Load credentials from environment variables

### 🚨 Security Checklist

Before committing code, verify:

- [ ] `.env` file is NOT staged for commit
- [ ] No passwords or secrets in code files
- [ ] No Redis Cloud endpoints with credentials in documentation
- [ ] All examples use placeholders or localhost
- [ ] `.gitignore` includes `.env`

### 🔍 Verification Commands

```bash
# Check if .env is ignored
git check-ignore -v .env
# Should output: .gitignore:138:.env	.env

# Check if .env is tracked
git ls-files | grep "\.env$"
# Should output: (nothing)

# Search for potential credential leaks
grep -r "redis://" --include="*.md" --include="*.py" . | grep -v "localhost"
# Review output for any real credentials
```

### 📚 Environment Variables

All scripts and code use environment variables for credentials:

```python
import os
from dotenv import load_dotenv

# Load from .env file
load_dotenv()

# Get Redis URL (defaults to localhost if not set)
redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
```

### 🛡️ Best Practices

1. **Never hardcode credentials** in code or documentation
2. **Always use environment variables** for sensitive data
3. **Use `.env.example`** to document required variables
4. **Keep `.env` in `.gitignore`** at all times
5. **Review diffs before committing** to catch accidental leaks
6. **Rotate credentials** if accidentally exposed

### 📞 Incident Response

If credentials are accidentally committed:

1. **Immediately rotate** the exposed credentials
2. **Remove from git history** using `git filter-branch` or BFG Repo-Cleaner
3. **Force push** the cleaned history (if safe to do so)
4. **Notify team members** to pull the cleaned history

### 🔗 References

**Internal Documentation:**
- `AUGGIE.md` - AI assistant security requirements and workflow
- `CONTEXT.md` - Architectural security constraints
- `notes/SECURITY_AUDIT_2026_03_04.md` - Latest security audit results

**External Resources:**
- [GitHub: Removing sensitive data](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository)
- [Git: gitignore documentation](https://git-scm.com/docs/gitignore)
- [Python: python-dotenv](https://github.com/theskumar/python-dotenv)

---

## Current Status: ✅ SECURE

- ✅ `.env` file is gitignored
- ✅ No credentials in committed files
- ✅ All endpoints redacted from documentation
- ✅ `.env.example` uses safe placeholders
- ✅ All code uses environment variables

**Last Verified:** 2026-03-04

