# Environment Setup Guide

This guide explains how to configure the FIPE Price Tracker webapp using environment variables.

## Quick Start

1. **Copy the example file**:
   ```bash
   cp .env.example .env
   ```

2. **Edit `.env` with your settings** (see below)

3. **Run the application**:
   ```bash
   python app.py
   ```

## Environment Variables

### Required Variables

#### `DATABASE_URL`
**Purpose**: Connection string for your database

**Development (SQLite)**:
```
DATABASE_URL=sqlite:///C:/path/to/your/fipe_data.db
```

**Production (PostgreSQL)**:
```
DATABASE_URL=postgresql://username:password@localhost:5432/fipe_db
```

**Notes**:
- For SQLite, use absolute paths
- For PostgreSQL, install `psycopg2-binary` first (uncomment in requirements.txt)

#### `SECRET_KEY`
**Purpose**: Flask session encryption key

**Development**:
```
SECRET_KEY=dev-secret-key-change-in-production
```

**Production**:
Generate a secure key:
```bash
python generate_secret_key.py
```
Then copy the output to your `.env` file.

### Optional Variables

#### `FLASK_ENV`
**Purpose**: Set the application environment

**Options**:
- `development` (default) - Debug mode enabled, verbose logging
- `production` - Optimized for performance

```
FLASK_ENV=development
```

#### `DEFAULT_BRAND`
**Purpose**: Brand to show when the page first loads

**Default**: `Volkswagen`

```
DEFAULT_BRAND=Volkswagen
```

#### `DEFAULT_MODEL`
**Purpose**: Model name to search for when the page first loads

**Default**: `Gol`

**Notes**:
- Uses fuzzy matching (searches for models containing this text)
- Case-insensitive

```
DEFAULT_MODEL=Gol
```

#### `SQLALCHEMY_ECHO`
**Purpose**: Log all SQL queries to console

**Options**:
- `False` (default) - No SQL logging
- `True` - Print all SQL queries (useful for debugging)

```
SQLALCHEMY_ECHO=False
```

## Example Configurations

### Local Development
```bash
FLASK_ENV=development
SECRET_KEY=dev-secret-key-change-in-production
DATABASE_URL=sqlite:///C:/Users/mathe/Desktop/Programming/fipe_scrapper/fipe_data.db
DEFAULT_BRAND=Volkswagen
DEFAULT_MODEL=Gol
SQLALCHEMY_ECHO=False
```

### Production Server
```bash
FLASK_ENV=production
SECRET_KEY=a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6
DATABASE_URL=postgresql://fipe_user:secure_password@db.example.com:5432/fipe_production
DEFAULT_BRAND=Volkswagen
DEFAULT_MODEL=Gol
SQLALCHEMY_ECHO=False
```

## Security Best Practices

### DO:
✅ Generate a secure `SECRET_KEY` for production using `generate_secret_key.py`
✅ Keep `.env` file out of version control (already in .gitignore)
✅ Use strong database passwords in production
✅ Use environment-specific `.env` files for different deployments

### DON'T:
❌ Commit `.env` to git
❌ Use the default `SECRET_KEY` in production
❌ Share `.env` files via email or messaging
❌ Store database credentials in code

## Troubleshooting

### Problem: "No module named 'dotenv'"
**Solution**: Install python-dotenv
```bash
pip install python-dotenv
```

### Problem: "Unable to open database file"
**Solution**: Check that `DATABASE_URL` path is correct and file exists
```bash
# Verify the file exists
ls "C:/path/to/fipe_data.db"

# Or on Windows PowerShell
Test-Path "C:\path\to\fipe_data.db"
```

### Problem: Changes to .env not taking effect
**Solution**: Restart the Flask application (Ctrl+C and run `python app.py` again)

### Problem: Database connection errors with PostgreSQL
**Solution**:
1. Verify PostgreSQL is running
2. Check credentials in `DATABASE_URL`
3. Ensure `psycopg2-binary` is installed:
   ```bash
   pip install psycopg2-binary
   ```

## Deployment Considerations

When deploying to platforms like Heroku, Railway, or PythonAnywhere:

1. **Don't use `.env` files** - Set environment variables through the platform's dashboard
2. **Set `FLASK_ENV=production`**
3. **Generate a secure `SECRET_KEY`**
4. **Use managed database services** for `DATABASE_URL`

### Platform-Specific Instructions

**Heroku**:
```bash
heroku config:set FLASK_ENV=production
heroku config:set SECRET_KEY=your-secure-key
heroku config:set DATABASE_URL=your-database-url
```

**Railway**:
Set variables in the Railway dashboard under "Variables" tab

**PythonAnywhere**:
Add variables to your WSGI configuration file

## Additional Resources

- [Flask Configuration Documentation](https://flask.palletsprojects.com/en/3.0.x/config/)
- [SQLAlchemy Database URLs](https://docs.sqlalchemy.org/en/20/core/engines.html#database-urls)
- [python-dotenv Documentation](https://github.com/theskumar/python-dotenv)
