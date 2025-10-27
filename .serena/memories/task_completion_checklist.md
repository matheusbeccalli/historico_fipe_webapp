# Task Completion Checklist

## When a coding task is completed, follow these steps:

### 1. Code Quality Checks
- [ ] Review code for adherence to project conventions (see code_style_conventions.md)
- [ ] Ensure proper error handling (try-finally for database sessions)
- [ ] Verify all database sessions are properly closed
- [ ] Check for SQL injection protection (use SQLAlchemy ORM only)
- [ ] Validate input parameters where needed
- [ ] Add appropriate docstrings for new functions/classes

### 2. Testing
**Note**: This project does not have automated tests currently.
- [ ] Manual testing via browser at http://127.0.0.1:5000
- [ ] Test API endpoints with curl or Postman if added/modified
- [ ] Verify dropdowns update correctly
- [ ] Check charts render properly
- [ ] Test with different vehicle selections
- [ ] Verify error handling (try invalid inputs)
- [ ] Test on Windows environment

### 3. Documentation
- [ ] Update CLAUDE.md if architecture/patterns changed
- [ ] Update README.md if user-facing features added
- [ ] Add comments for complex logic
- [ ] Update API endpoint documentation if endpoints added/modified
- [ ] Update database schema docs if models changed

### 4. Configuration
- [ ] Update .env.example if new environment variables added
- [ ] Update requirements.txt if new dependencies added
- [ ] Ensure .gitignore covers sensitive files

### 5. Security Review
- [ ] Verify API key authentication on new endpoints
- [ ] Check rate limiting is applied to new endpoints
- [ ] Ensure no secrets are hardcoded
- [ ] Validate all user inputs
- [ ] Sanitize LIKE patterns in SQL queries
- [ ] Review CSRF protection if forms added

### 6. Performance Considerations
- [ ] Check for N+1 query problems
- [ ] Verify efficient database queries (joins vs multiple queries)
- [ ] Consider adding database indexes if new queries added
- [ ] Test with realistic data volumes

### 7. Frontend (if applicable)
- [ ] Test in browser console for JavaScript errors
- [ ] Verify responsive design on different screen sizes
- [ ] Check dark/light theme compatibility
- [ ] Ensure API key is passed in headers
- [ ] Test error messages display to users

### 8. Version Control
- [ ] Stage relevant files with `git add`
- [ ] Review changes with `git diff`
- [ ] Commit with descriptive message
- [ ] Push to remote if appropriate

## No Automated Tools Required
This project does not currently use:
- Linting tools (pylint, flake8)
- Code formatters (black, autopep8)
- Type checkers (mypy)
- Test runners (pytest, unittest)
- CI/CD pipelines

Manual code review and testing is sufficient.

## Critical Reminders

### Database Operations
- ⚠️ **NEVER** perform INSERT, UPDATE, or DELETE operations
- This is a **read-only webapp** - database populated by separate scraper
- All operations should be SELECT queries only

### Session Management
- **ALWAYS** use try-finally blocks for database sessions
- **ALWAYS** close sessions in finally block
- Use `get_db()` helper for session creation

### API Security
- **ALWAYS** add `@require_api_key` decorator to new API endpoints
- **ALWAYS** add rate limiting with `@limiter.limit()`
- Verify API_KEY is in API_KEYS_ALLOWED

### Date and Price Formatting
- **ALWAYS** use `format_month_portuguese()` for displaying dates
- **ALWAYS** use `format_price_brl()` for displaying prices
- Store dates as YYYY-MM-DD in database
- Store prices as floats in database

## Running the Application

After making changes, test by:
```bash
# Activate virtual environment
source venv/Scripts/activate  # Windows Git Bash
venv\Scripts\activate          # Windows CMD

# Run the application
python app.py

# Access at http://127.0.0.1:5000
# Check browser console for errors
# Check terminal for Flask logs
```

## Common Issues to Check

### If changes don't appear:
- Hard refresh browser (Ctrl+F5)
- Clear browser cache
- Check browser console for errors
- Verify static files are being served

### If database errors occur:
- Verify DATABASE_URL in .env is correct
- Check fipe_data.db exists and is accessible
- Review SQLAlchemy query syntax
- Enable SQLALCHEMY_ECHO=True to see queries

### If API errors occur:
- Check API_KEY is set in .env
- Verify API_KEYS_ALLOWED includes API_KEY
- Test endpoint with curl to isolate frontend/backend
- Review Flask logs in terminal

## Git Workflow

```bash
# Check status
git status

# Add files
git add app.py
git add static/js/app.js
# or
git add .

# Commit
git commit -m "Descriptive message about what changed"

# Push (if working with remote)
git push origin main
```

## When Task is Complete

- ✅ All checklist items addressed
- ✅ Application runs without errors
- ✅ Manual testing confirms functionality works
- ✅ Code committed to git with descriptive message
- ✅ Documentation updated if needed
