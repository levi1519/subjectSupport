# Architect Guard Maintenance Guide

## Overview

The Architect Guard is a governance framework implementing RFC 2119 compliance standards for the academicTutoring platform. It ensures code quality, architectural consistency, and documentation standards.

## Structure

```
apps/academicTutoring/
├── requirements/
│   ├── requirements_accounts.json       # RFC 2119 specs for accounts app
│   └── requirements_core.json           # RFC 2119 specs for core app
│
├── context/
│   ├── context_accounts.json           # Architecture docs for accounts
│   └── context_core.json               # Architecture docs for core
│
└── logs/
    ├── ARCHITECT_GUARD_IMPLEMENTATION.md  # Setup log
    └── AUDIT_REPORT_ARCHITECT_GUARD.md   # Comprehensive audit
```

## Using the RFC 2119 Templates

### Reading Requirements
Each requirements file contains:

```json
{
  "metadata": { "app": "...", "version": "1.0.0" },
  "MUST": [...],      // Non-negotiable requirements
  "SHOULD": [...],    // Strongly recommended
  "MAY": [...],       // Optional enhancements
  "MUST_NOT": [...]   // Prohibited patterns
}
```

### RFC 2119 Key Terms

| Term | Meaning | Enforcement |
|------|---------|-----------|
| **MUST** | Requirement is absolute | Pre-deployment check |
| **SHOULD** | Requirement is recommended | Code review guideline |
| **MAY** | Requirement is optional | Future enhancement |
| **MUST_NOT** | Requirement is prohibited | Security/quality check |

### Example: Validating a Feature Against Requirements

**Feature**: Add new tutor rating system

**Check Requirements**:
1. Does it violate any MUST_NOT rules?
   - ✅ "Session data MUST NOT be accessible without authentication" - Store ratings only for authenticated users
   
2. Does it satisfy all MUST requirements?
   - ✅ "All database operations MUST handle timezone-aware datetimes" - Use Django's timezone utilities
   - ✅ "Database connection MUST timeout gracefully" - Add timeout handling
   
3. Can it follow SHOULD guidelines?
   - ✅ "Session history SHOULD be queryable by date range" - Yes, can add date filters to ratings
   
4. Any MAY enhancements?
   - ✅ "Analytics MAY track tutor performance metrics" - Yes, ratings are part of analytics

## Maintenance Tasks

### Monthly Audit
```bash
# Verify migrations still load without errors
python manage.py showmigrations

# Run Django system checks
python manage.py check

# Check for new circular imports
grep -r "from accounts import" apps/academicTutoring/core/
```

### When Adding New Features

1. **Update requirements files** if MUST/SHOULD/MAY/MUST_NOT rules change
2. **Documents architectures** in context/ folder
3. **Add migration** if schema changes
4. **Update audit log** with changes
5. **Run tests** to ensure RFC 2119 compliance

### When Splitting Apps

1. Create new subdirectory under `apps/academicTutoring/`
2. Generate `requirements_<app_name>.json` with RFC 2119 compliance
3. Create `context_<app_name>.json` documenting architecture
4. Update `INSTALLED_APPS` in settings.py
5. Add migration for any schema changes
6. Update audit report

## Pre-Deployment Checklist

- [ ] All migrations load: `python manage.py showmigrations` (no errors)
- [ ] Django check passes: `python manage.py check` (0 issues)
- [ ] No MUST_NOT violations in code review
- [ ] All MUST requirements addressed
- [ ] Context documentation updated
- [ ] Audit log includes changes
- [ ] All tests pass
- [ ] Git commits are clean and signed (optional)

## Continuous Integration (CI/CD)

### Recommended GitHub Actions

```yaml
# .github/workflows/architect-guard.yml
name: Architect Guard Validation

on: [push, pull_request]

jobs:
  validation:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Django Check
        run: python manage.py check
      - name: Migration Check
        run: python manage.py showmigrations
      - name: RFC 2119 Lint
        run: python scripts/validate_requirements.py
```

### Scripts to Implement

Create `scripts/validate_requirements.py`:
```python
#!/usr/bin/env python
import json
import sys

def validate_rfc2119_structure(req_file):
    """Validate requirements file has all RFC 2119 sections"""
    with open(req_file) as f:
        data = json.load(f)
    
    required_keys = ['metadata', 'MUST', 'SHOULD', 'MAY', 'MUST_NOT']
    missing = [k for k in required_keys if k not in data]
    
    if missing:
        print(f"❌ {req_file} missing: {missing}")
        return False
    
    print(f"✅ {req_file} RFC 2119 structure valid")
    return True

if __name__ == '__main__':
    req_files = [
        'apps/academicTutoring/requirements/requirements_accounts.json',
        'apps/academicTutoring/requirements/requirements_core.json'
    ]
    
    results = [validate_rfc2119_structure(f) for f in req_files]
    sys.exit(0 if all(results) else 1)
```

## Troubleshooting

### Issue: "GDAL not found" warning

**Solution**: Expected in development. Production uses PostGIS automatically.
```bash
# To enable GIS in development (Windows):
# Install OSGeo4W from: https://trac.osgeo.org/osgeo4w/
# Then set in .env: GDAL_LIBRARY_PATH=C:\OSGeo4W\bin

# Or simply ignore the warning; GIS features are disabled by default
```

### Issue: Migration conflicts after app reorganization

**Solution**: Ensure apps.py has correct full path:
```python
# apps/academicTutoring/accounts/apps.py
class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.academicTutoring.accounts'  # ← MUST be full path
```

### Issue: Circular imports

**Solution**: Use TYPE_CHECKING and forward references:
```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from apps.academicTutoring.core.models import ClassSession
```

## Contact & Updates

- **Last Updated**: 2026-03-22
- **Framework**: Django 5.2.8
- **Python**: 3.13+
- **Architecture Pattern**: Apps Container (Django best practice)

## References

- [RFC 2119: Key Words for use in Standards](https://tools.ietf.org/html/rfc2119)
- [Django Architecture Best Practices](https://docs.djangoproject.com/en/5.2/)
- [PostGIS GeoDjango Guide](https://docs.djangoproject.com/en/5.2/ref/contrib/gis/)
