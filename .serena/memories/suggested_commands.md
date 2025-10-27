# Suggested Commands

## System Information
- **Operating System**: Windows (MINGW64_NT)
- **Shell**: Git Bash / Command Prompt

## Development Workflow

### Environment Setup
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows (Command Prompt):
venv\Scripts\activate
# Windows (Git Bash):
source venv/Scripts/activate

# Install dependencies
pip install -r requirements.txt
```

### Running the Application
```bash
# Activate venv first (see above)
# Then run the Flask app
python app.py
```
Application runs at: `http://127.0.0.1:5000`

### Configuration
```bash
# Copy environment template
cp .env.example .env

# Generate secure SECRET_KEY
python generate_secret_key.py

# Generate API_KEY
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Database Configuration
Edit `.env` file:
```bash
# SQLite (development - default)
DATABASE_URL=sqlite:///C:/Users/mathe/Desktop/Programming/fipe_scrapper/fipe_data.db

# PostgreSQL (production)
DATABASE_URL=postgresql://user:password@localhost/fipe_db
```

### Common Git Commands (Windows)
```bash
# Status check
git status

# Add files
git add .

# Commit
git commit -m "message"

# Push to remote
git push origin main

# Pull latest changes
git pull origin main
```

### Common Windows File Commands
```bash
# List files
ls
ls -la

# Change directory
cd path/to/directory

# Create directory
mkdir dirname

# Remove file
rm filename

# Copy file
cp source destination

# Move/rename file
mv source destination
```

### Python Version Check
```bash
python --version
```

### View Logs
Flask application logs appear in the console when running `python app.py`.
For debugging, set `SQLALCHEMY_ECHO=True` in `.env` to see SQL queries.
