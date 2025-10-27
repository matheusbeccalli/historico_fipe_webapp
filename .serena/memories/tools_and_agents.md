# Development Tools and Agents

This document describes the specialized tools available for working with this codebase.

## Serena MCP - Semantic Code Navigation

Serena provides symbol-based code navigation instead of line-based file reading. This is the **preferred way** to explore and modify code.

### Available Tools

**Symbol Overview and Reading:**
- `get_symbols_overview(relative_path)` - Get high-level view of classes/functions in a file
- `find_symbol(name_path, relative_path, include_body=False, depth=0)` - Find and read specific symbols
- `find_referencing_symbols(name_path, relative_path)` - Find all references to a symbol

**Code Search:**
- `search_for_pattern(substring_pattern, relative_path="", paths_include_glob="")` - Search for code patterns
- `find_file(file_mask, relative_path=".")` - Find files by name pattern
- `list_dir(relative_path, recursive=False)` - List directory contents

**Symbol-Based Editing:**
- `replace_symbol_body(name_path, relative_path, body)` - Replace entire function/class
- `insert_after_symbol(name_path, relative_path, body)` - Insert code after a symbol
- `insert_before_symbol(name_path, relative_path, body)` - Insert code before a symbol
- `rename_symbol(name_path, relative_path, new_name)` - Rename symbol across codebase

### Usage Guidelines

**Always follow this priority:**
1. Use `get_symbols_overview` before reading full files
2. Use `find_symbol` to read specific functions/classes
3. Read entire files only as last resort

**For editing code:**
- Prefer symbol-based editing over line-based editing
- Use `replace_symbol_body` for entire functions/classes
- Use `insert_after_symbol` or `insert_before_symbol` for adding new code

## Specialized AI Agents

Located in `.claude/agents/`, these agents should be used proactively.

### 1. code-reviewer
**Purpose:** Review code quality, security, and best practices

**Use after:**
- Adding new API endpoints
- Modifying database queries
- Implementing new features
- Refactoring existing code

**Provides:**
- Security vulnerability detection
- Performance analysis
- Code quality review
- Project-specific pattern validation
- Prioritized feedback (Critical → High → Medium → Low)

### 2. data-analyst-sql
**Purpose:** Data analysis, SQL queries, insights, optimization

**Use for:**
- Analyzing FIPE price trends
- Optimizing slow queries
- Exploring data patterns
- Generating reports or insights
- Understanding data relationships

**Provides:**
- Efficient SQLAlchemy ORM queries
- Price trend analysis
- Query performance tuning
- Statistical analysis

### 3. debug-specialist
**Purpose:** Debug errors, exceptions, and unexpected behavior

**Use when encountering:**
- 500 errors or API failures
- Unexpected behavior (wrong data, incorrect charts)
- Application crashes or exceptions
- Database connection issues
- Test failures

**Provides:**
- Systematic root cause analysis
- Stack trace interpretation
- Strategic debug logging
- Minimal fix implementation
- Prevention recommendations

### 4. feature-implementation-planner
**Purpose:** Plan implementation of features from README.md roadmap

**Use for:**
- Planning new features from "Melhorias Futuras"
- Breaking down complex features into steps
- Understanding feature dependencies
- Creating implementation checklists

**Provides:**
- Deep feature analysis
- Phased implementation strategy (Database → Backend → Frontend → Testing)
- Architecture-aware planning
- Risk assessment and dependency mapping
- Code-level guidance with exact file locations

## Recommended Workflows

### Implementing a New Feature
1. **Plan**: Use `feature-implementation-planner` agent
2. **Navigate**: Use Serena's `get_symbols_overview` and `find_symbol`
3. **Implement**: Use Serena's symbol editing tools
4. **Review**: Use `code-reviewer` agent
5. **Debug**: Use `debug-specialist` if issues arise

### Analyzing Data or Optimizing Queries
1. Use `data-analyst-sql` agent for insights and optimization
2. Use Serena's `find_symbol` to understand existing query patterns
3. Use `code-reviewer` agent to validate security and performance

### Debugging Issues
1. Use `debug-specialist` agent to investigate root cause
2. Use Serena's `find_symbol` to understand related code
3. Use Serena's symbol editing to implement fix
4. Use `code-reviewer` agent to validate the fix

### Exploring Unfamiliar Code
1. Use Serena's `get_symbols_overview` to understand file structure
2. Use Serena's `find_symbol` to read specific functions
3. Use `find_referencing_symbols` to understand usage
4. Use `search_for_pattern` to find similar code patterns
