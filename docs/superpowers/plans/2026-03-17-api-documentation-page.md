# API Documentation Page — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a comprehensive API documentation page at `/api/docs` with a link in the homepage navbar, enabling external developers to discover and consume the FIPE price API.

**Architecture:** A new Flask route serves a standalone Jinja2 template (`api_docs.html`) with a sticky sidebar and scrollable endpoint sections. The page shares the existing design system (CSS variables, dark/light mode, Inter font) and reuses the navbar pattern. CSRF exemption for non-browser requests enables external API consumers to hit POST endpoints directly.

**Tech Stack:** Flask, Jinja2, HTML/CSS/JS (no new dependencies)

**Spec:** `docs/superpowers/specs/2026-03-17-api-documentation-page-design.md`

---

### Task 1: Add conditional CSRF exemption for non-browser API requests

**Files:**
- Modify: `app.py:168` (after `csrf = CSRFProtect(app)`)

The spec requires CSRF exemption only when no session cookie is present (non-browser requests). This preserves CSRF protection for the webapp's own frontend while allowing external consumers (curl, Postman, server-to-server) to hit POST endpoints.

- [ ] **Step 1: Register a custom CSRF error handler with conditional logic**

In `app.py`, after line 168 (`csrf = CSRFProtect(app)`), add a custom error handler that conditionally allows requests without session cookies:

```python
@csrf.error_handler
def csrf_error_handler(reason):
    """
    Custom CSRF error handler that exempts non-browser API requests.

    CSRF attacks require a browser with an active session cookie. Requests without
    session cookies (curl, Postman, server-to-server) cannot be CSRF targets,
    so we allow them through. Browser requests (with session cookie) still require
    a valid CSRF token.
    """
    session_cookie_name = app.config.get('SESSION_COOKIE_NAME', 'session')
    is_api_request = request.path.startswith('/api/')

    if is_api_request and session_cookie_name not in request.cookies:
        # Non-browser API request: no session cookie means no CSRF risk
        return None  # Allow the request to proceed

    # Browser request with session cookie: enforce CSRF as normal
    from flask_wtf.csrf import CSRFError
    raise CSRFError(reason)
```

**Note:** Flask-WTF's `CSRFProtect.error_handler` decorator registers a callback that is invoked when CSRF validation fails. Returning `None` allows the request to proceed. If this approach doesn't work with the installed Flask-WTF version, use the alternative approach of wrapping the CSRF check in a `before_request`:

```python
from flask_wtf.csrf import CSRFError

@app.before_request
def conditional_csrf_protect():
    """Skip CSRF for API POST requests from non-browser clients."""
    if (request.method == 'POST'
            and request.path.startswith('/api/')
            and app.config.get('SESSION_COOKIE_NAME', 'session') not in request.cookies):
        # Mark this request to skip CSRF — set the token to match
        request.environ['HTTP_X_CSRFTOKEN'] = g.get('csrf_token', '')
```

The implementer should test which approach works and use that one. The key requirement: **browser requests with session cookies must still be CSRF-protected**.

- [ ] **Step 2: Verify the app still starts**

Run: `cd /home/mathe/programming/historico_fipe_webapp && python -c "from app import app; print('OK')"`
Expected: `OK`

- [ ] **Step 3: Test conditional CSRF behavior**

```bash
# Should succeed (no session cookie = exempt from CSRF):
curl -X POST http://localhost:5000/api/compare-vehicles \
  -H "Content-Type: application/json" \
  -d '{"vehicle_ids": [1]}'
# Expected: JSON response (200 or 404), NOT a 400 CSRF error
```

- [ ] **Step 4: Commit**

```bash
git add app.py
git commit -m "feat: add conditional CSRF exemption for non-browser API requests"
```

---

### Task 2: Add the /api/docs route in app.py

**Files:**
- Modify: `app.py` (add new route near the index route, around line 477)

- [ ] **Step 1: Add the /api/docs route**

Insert after the `index()` route function (after line 476), before the `/health` route:

```python
@app.route('/api/docs')
@limiter.limit("20 per minute")
def api_docs():
    """
    API documentation page.

    Serves a comprehensive API reference for external developers.
    """
    if not hasattr(g, 'csp_nonce'):
        g.csp_nonce = secrets.token_urlsafe(16)

    return render_template(
        'api_docs.html',
        ga_measurement_id=app.config.get('GA_MEASUREMENT_ID', '')
    )
```

- [ ] **Step 2: Verify the route registers**

Run: `cd /home/mathe/programming/historico_fipe_webapp && python -c "from app import app; print([rule.rule for rule in app.url_map.iter_rules() if 'docs' in rule.rule])"`
Expected: `['/api/docs']`

- [ ] **Step 3: Commit**

```bash
git add app.py
git commit -m "feat: add /api/docs route for API documentation page"
```

---

### Task 3: Add API docs link to homepage navbar

**Files:**
- Modify: `templates/index.html:91-104` (navbar section)

- [ ] **Step 1: Update the navbar to include API Docs link**

In `templates/index.html`, replace the navbar section (lines 91-104). The key change is wrapping the theme toggle and new API link in a flex container on the right side with a vertical divider:

Replace lines 99-102:
```html
            <button id="themeToggle" class="theme-toggle" aria-label="Alternar tema">
                <i class="bi bi-sun-fill"></i>
                <span class="theme-toggle-text">Claro</span>
            </button>
```

With:
```html
            <div class="navbar-right">
                <a href="{{ url_for('api_docs') }}" class="navbar-api-link">API Docs</a>
                <div class="navbar-divider"></div>
                <button id="themeToggle" class="theme-toggle" aria-label="Alternar tema">
                    <i class="bi bi-sun-fill"></i>
                    <span class="theme-toggle-text">Claro</span>
                </button>
            </div>
```

- [ ] **Step 2: Commit**

```bash
git add templates/index.html
git commit -m "feat: add API Docs link to homepage navbar"
```

---

### Task 4: Add API docs CSS styles

**Files:**
- Modify: `static/css/style.css` (append new sections at end of file)

- [ ] **Step 1: Add navbar-right, API link, and divider styles**

Append to `static/css/style.css`:

```css
/* ========================================
   24. Navbar Right Section (API link + theme toggle)
   ======================================== */
.navbar-right {
    display: flex;
    align-items: center;
    gap: 1rem;
}

.navbar-api-link {
    color: #6c5ce7;
    text-decoration: none;
    font-weight: 500;
    font-size: 0.8125rem;
    transition: all var(--transition-base);
    padding: 0.375rem 0;
}

.navbar-api-link:hover {
    color: #5b4cdb;
}

.navbar-divider {
    width: 1px;
    height: 20px;
    background: rgba(128, 128, 128, 0.2);
}
```

- [ ] **Step 2: Add API docs page layout styles**

Append to `static/css/style.css`:

```css
/* ========================================
   25. API Documentation Page
   ======================================== */
.api-docs-layout {
    display: flex;
    min-height: calc(100vh - 120px);
}

.api-docs-sidebar {
    width: 250px;
    min-width: 250px;
    position: sticky;
    top: 120px;
    height: calc(100vh - 120px);
    overflow-y: auto;
    padding: 1.5rem 1rem;
    border-right: 1px solid var(--color-border-light);
    background: var(--color-bg-primary);
}

.api-docs-sidebar-title {
    font-weight: 700;
    font-size: 0.875rem;
    color: var(--color-accent);
    margin-bottom: 1.5rem;
    padding: 0 0.5rem;
}

.api-docs-sidebar-category {
    font-size: 0.6875rem;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    color: var(--color-text-muted);
    margin-bottom: 0.5rem;
    margin-top: 1.25rem;
    padding: 0 0.5rem;
    font-weight: 600;
}

.api-docs-sidebar-category:first-of-type {
    margin-top: 0;
}

.api-docs-sidebar-link {
    display: block;
    padding: 0.375rem 0.5rem;
    border-radius: 6px;
    color: var(--color-text-primary);
    text-decoration: none;
    font-size: 0.8125rem;
    transition: all var(--transition-fast);
    margin-bottom: 0.125rem;
}

.api-docs-sidebar-link:hover {
    background: var(--color-bg-secondary);
    color: var(--color-accent);
}

.api-docs-sidebar-link.active {
    background: rgba(108, 92, 231, 0.12);
    color: var(--color-accent);
    font-weight: 500;
}

.api-docs-sidebar-link .method-badge-sm {
    font-size: 0.625rem;
    font-weight: 700;
    margin-right: 0.25rem;
}

.method-get { color: #27ae60; }
.method-post { color: #2980b9; }

.api-docs-main {
    flex: 1;
    padding: 2rem 2.5rem;
    max-width: 900px;
}

/* API docs section styles */
.api-docs-section {
    margin-bottom: 3rem;
    scroll-margin-top: 130px;
}

.api-docs-section h2 {
    font-size: 1.5rem;
    margin-bottom: 1rem;
    padding-bottom: 0.75rem;
    border-bottom: 2px solid var(--color-border-light);
}

.api-docs-section h3 {
    font-size: 1.125rem;
    margin-bottom: 0.75rem;
}

.api-docs-section p {
    color: var(--color-text-secondary);
    line-height: 1.7;
    margin-bottom: 1rem;
    font-size: 0.9375rem;
}

/* Endpoint header */
.endpoint-header {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    margin-bottom: 0.75rem;
}

.method-badge {
    padding: 0.25rem 0.75rem;
    border-radius: 4px;
    font-size: 0.75rem;
    font-weight: 700;
    color: white;
    flex-shrink: 0;
}

.method-badge.get { background: #27ae60; }
.method-badge.post { background: #2980b9; }

.endpoint-path {
    font-size: 1.0625rem;
    font-weight: 600;
    font-family: 'Fira Code', 'Cascadia Code', 'Consolas', monospace;
    color: var(--color-text-primary);
}

.endpoint-description {
    color: var(--color-text-secondary);
    margin-bottom: 1rem;
    font-size: 0.9375rem;
}

/* Rate limit badge */
.rate-limit-badge {
    display: inline-block;
    background: rgba(241, 196, 15, 0.15);
    color: #f39c12;
    padding: 0.1875rem 0.625rem;
    border-radius: 4px;
    font-size: 0.6875rem;
    font-weight: 600;
    margin-bottom: 1.25rem;
}

/* Parameters table */
.params-table {
    width: 100%;
    border-collapse: collapse;
    margin-bottom: 1.25rem;
    font-size: 0.875rem;
}

.params-table th {
    text-align: left;
    padding: 0.625rem 0.75rem;
    background: var(--color-bg-secondary);
    border-bottom: 2px solid var(--color-border-light);
    font-size: 0.6875rem;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    color: var(--color-text-muted);
    font-weight: 600;
}

.params-table td {
    padding: 0.625rem 0.75rem;
    border-bottom: 1px solid var(--color-border-light);
    vertical-align: top;
}

.params-table code {
    background: var(--color-bg-secondary);
    padding: 0.125rem 0.375rem;
    border-radius: 3px;
    font-size: 0.8125rem;
    color: var(--color-accent);
}

.param-required {
    color: #e74c3c;
    font-size: 0.75rem;
    font-weight: 600;
}

.param-optional {
    color: var(--color-text-muted);
    font-size: 0.75rem;
}

.no-params {
    background: var(--color-bg-secondary);
    border: 1px solid var(--color-border-light);
    border-radius: 6px;
    padding: 0.75rem 1rem;
    color: var(--color-text-muted);
    font-style: italic;
    font-size: 0.8125rem;
    margin-bottom: 1.25rem;
}

/* Code blocks */
.api-code-block {
    background: #1e1e2e;
    color: #cdd6f4;
    border-radius: 6px;
    padding: 1rem 1.25rem;
    font-family: 'Fira Code', 'Cascadia Code', 'Consolas', monospace;
    font-size: 0.8125rem;
    line-height: 1.6;
    overflow-x: auto;
    margin-bottom: 1.25rem;
    position: relative;
}

.api-code-block .code-label {
    position: absolute;
    top: 0.5rem;
    right: 0.75rem;
    font-size: 0.625rem;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    color: #6c7086;
}

/* Syntax highlighting */
.code-keyword { color: #89b4fa; }
.code-string { color: #a6e3a1; }
.code-number { color: #fab387; }
.code-comment { color: #6c7086; }
.code-key { color: #89b4fa; }
.code-bracket { color: #585b70; }

/* Response header */
.response-header {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin-bottom: 0.5rem;
    font-size: 0.875rem;
    font-weight: 600;
}

.response-status {
    font-size: 0.75rem;
    font-weight: 600;
}

.response-status.success { color: #27ae60; }
.response-status.error { color: #e74c3c; }

/* Error responses table */
.error-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.875rem;
    margin-bottom: 1.25rem;
}

.error-table td {
    padding: 0.5rem 0.75rem;
    border-bottom: 1px solid var(--color-border-light);
}

.error-table td:first-child {
    width: 60px;
    font-weight: 600;
    color: #e74c3c;
}

/* Rate limits summary table */
.rate-limits-table {
    width: 100%;
    border-collapse: collapse;
    margin-bottom: 1.25rem;
    font-size: 0.875rem;
}

.rate-limits-table th {
    text-align: left;
    padding: 0.625rem 0.75rem;
    background: var(--color-bg-secondary);
    border-bottom: 2px solid var(--color-border-light);
    font-size: 0.6875rem;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    color: var(--color-text-muted);
    font-weight: 600;
}

.rate-limits-table td {
    padding: 0.625rem 0.75rem;
    border-bottom: 1px solid var(--color-border-light);
}

.rate-limits-table code {
    background: var(--color-bg-secondary);
    padding: 0.125rem 0.375rem;
    border-radius: 3px;
    font-size: 0.8125rem;
}

/* Mobile responsive */
@media (max-width: 768px) {
    .api-docs-sidebar {
        display: none;
    }

    .api-docs-mobile-nav {
        display: block;
        padding: 1rem;
        background: var(--color-bg-secondary);
        border-bottom: 1px solid var(--color-border-light);
    }

    .api-docs-main {
        padding: 1.5rem 1rem;
    }

    .endpoint-header {
        flex-wrap: wrap;
    }

    .endpoint-path {
        font-size: 0.875rem;
    }

    .params-table {
        font-size: 0.8125rem;
    }
}

@media (min-width: 769px) {
    .api-docs-mobile-nav {
        display: none;
    }
}

/* Dark mode adjustments for API docs */
[data-theme="dark"] .api-docs-sidebar {
    background: var(--color-bg-secondary);
    border-right-color: var(--color-border);
}

[data-theme="dark"] .navbar-api-link {
    color: #a29bfe;
}

[data-theme="dark"] .navbar-api-link:hover {
    color: #b8b3ff;
}

[data-theme="dark"] .navbar-divider {
    background: rgba(128, 128, 128, 0.3);
}
```

- [ ] **Step 3: Commit**

```bash
git add static/css/style.css
git commit -m "feat: add CSS styles for API docs page and navbar link"
```

---

### Task 5: Create the API documentation template

**Files:**
- Create: `templates/api_docs.html`

- [ ] **Step 1: Create the api_docs.html template**

Create `templates/api_docs.html` with the complete content below. This is a large file (~800 lines). The implementer should write this file exactly as shown, substituting only `{{ }}` Jinja2 template variables.

The template follows these patterns from the existing codebase:
- Same `<head>` structure as `index.html` (meta tags, Inter font, Bootstrap CSS/Icons, custom CSS, CSP nonce) but **without** Plotly.js
- Same navbar with logo (linking back to `/`), API Docs link (active/bold), divider, theme toggle
- The docs page uses `lang="en"` since it targets external developers (API docs are in English)

**Complete template structure with all endpoint content:**

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="FIPE Price Tracker API Reference - Access historical vehicle price data from Brazil's FIPE table via RESTful endpoints.">
    <meta name="robots" content="index, follow">
    <title>API Reference | FIPE Price Tracker</title>
    <link rel="icon" type="image/x-icon" href="{{ url_for('static', filename='favicon.ico') }}">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.0/font/bootstrap-icons.css">
    <link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}">

    {% if ga_measurement_id %}
    <script async src="https://www.googletagmanager.com/gtag/js?id={{ ga_measurement_id }}" nonce="{{ g.csp_nonce }}"></script>
    <script nonce="{{ g.csp_nonce }}">
        window.dataLayer = window.dataLayer || [];
        function gtag(){dataLayer.push(arguments);}
        gtag('js', new Date());
        gtag('config', '{{ ga_measurement_id }}');
    </script>
    {% endif %}
</head>
<body>
    <nav class="navbar navbar-light">
        <div class="container-fluid">
            <a href="{{ url_for('index') }}" class="navbar-brand mb-0 h1">
                <img id="navbarLogo" src="{{ url_for('static', filename='img/logo-light.png') }}" alt="FIPE Histórico" class="navbar-logo"
                     width="1080" height="293"
                     data-light="{{ url_for('static', filename='img/logo-light.png') }}"
                     data-dark="{{ url_for('static', filename='img/logo-dark.png') }}">
            </a>
            <div class="navbar-right">
                <a href="{{ url_for('api_docs') }}" class="navbar-api-link" style="font-weight:700;">API Docs</a>
                <div class="navbar-divider"></div>
                <button id="themeToggle" class="theme-toggle" aria-label="Toggle theme">
                    <i class="bi bi-sun-fill"></i>
                    <span class="theme-toggle-text">Claro</span>
                </button>
            </div>
        </div>
    </nav>

    <div class="api-docs-layout">
        <!-- Sidebar -->
        <aside class="api-docs-sidebar">
            <div class="api-docs-sidebar-title">API Reference</div>

            <div class="api-docs-sidebar-category">Getting Started</div>
            <a href="#introduction" class="api-docs-sidebar-link active">Introduction</a>
            <a href="#authentication" class="api-docs-sidebar-link">Authentication</a>
            <a href="#rate-limits" class="api-docs-sidebar-link">Rate Limits</a>
            <a href="#error-handling" class="api-docs-sidebar-link">Error Handling</a>

            <div class="api-docs-sidebar-category">Vehicle Data</div>
            <a href="#get-brands" class="api-docs-sidebar-link"><span class="method-badge-sm method-get">GET</span> /api/brands</a>
            <a href="#get-vehicle-options" class="api-docs-sidebar-link"><span class="method-badge-sm method-get">GET</span> /api/vehicle-options</a>
            <a href="#get-months" class="api-docs-sidebar-link"><span class="method-badge-sm method-get">GET</span> /api/months</a>
            <a href="#get-default-car" class="api-docs-sidebar-link"><span class="method-badge-sm method-get">GET</span> /api/default-car</a>

            <div class="api-docs-sidebar-category">Price &amp; History</div>
            <a href="#post-compare-vehicles" class="api-docs-sidebar-link"><span class="method-badge-sm method-post">POST</span> /api/compare-vehicles</a>
            <a href="#post-price" class="api-docs-sidebar-link"><span class="method-badge-sm method-post">POST</span> /api/price</a>

            <div class="api-docs-sidebar-category">Economic &amp; Market</div>
            <a href="#post-economic-indicators" class="api-docs-sidebar-link"><span class="method-badge-sm method-post">POST</span> /api/economic-indicators</a>
            <a href="#get-depreciation-analysis" class="api-docs-sidebar-link"><span class="method-badge-sm method-get">GET</span> /api/depreciation-analysis</a>

            <div class="api-docs-sidebar-category">System</div>
            <a href="#get-health" class="api-docs-sidebar-link"><span class="method-badge-sm method-get">GET</span> /health</a>
        </aside>

        <!-- Mobile nav -->
        <div class="api-docs-mobile-nav">
            <select id="mobileNavSelect" class="form-select">
                <option value="">Jump to section...</option>
                <optgroup label="Getting Started">
                    <option value="#introduction">Introduction</option>
                    <option value="#authentication">Authentication</option>
                    <option value="#rate-limits">Rate Limits</option>
                    <option value="#error-handling">Error Handling</option>
                </optgroup>
                <optgroup label="Vehicle Data">
                    <option value="#get-brands">GET /api/brands</option>
                    <option value="#get-vehicle-options">GET /api/vehicle-options</option>
                    <option value="#get-months">GET /api/months</option>
                    <option value="#get-default-car">GET /api/default-car</option>
                </optgroup>
                <optgroup label="Price &amp; History">
                    <option value="#post-compare-vehicles">POST /api/compare-vehicles</option>
                    <option value="#post-price">POST /api/price</option>
                </optgroup>
                <optgroup label="Economic &amp; Market">
                    <option value="#post-economic-indicators">POST /api/economic-indicators</option>
                    <option value="#get-depreciation-analysis">GET /api/depreciation-analysis</option>
                </optgroup>
                <optgroup label="System">
                    <option value="#get-health">GET /health</option>
                </optgroup>
            </select>
        </div>

        <!-- Main content -->
        <main class="api-docs-main">

            <!-- ===== INTRODUCTION ===== -->
            <section id="introduction" class="api-docs-section">
                <h2>Introduction</h2>
                <p>The FIPE Price Tracker API provides programmatic access to historical vehicle price data from Brazil's FIPE (Fundação Instituto de Pesquisas Econômicas) table. Use these endpoints to query price history, compare vehicles, and analyze market trends.</p>
                <p>All responses are returned as <strong>JSON</strong>. Dates are stored in <code>YYYY-MM-DD</code> format. Prices are in Brazilian Real (BRL) — for example, <code>R$ 56.789,00</code>.</p>
                <p>Base URL:</p>
                <div class="api-code-block"><span class="code-string">https://your-domain.com</span></div>
            </section>

            <!-- ===== AUTHENTICATION ===== -->
            <section id="authentication" class="api-docs-section">
                <h2>Authentication</h2>
                <p>The API is <strong>public</strong> and requires no authentication. No API keys are needed. You can call any endpoint directly from curl, Postman, or your application code.</p>
                <div class="api-code-block">
                    <span class="code-label">bash</span>
<span class="code-comment"># No authentication needed</span>
<span class="code-keyword">curl</span> <span class="code-string">https://your-domain.com/api/brands</span></div>
            </section>

            <!-- ===== RATE LIMITS ===== -->
            <section id="rate-limits" class="api-docs-section">
                <h2>Rate Limits</h2>
                <p>All endpoints are rate-limited by IP address. When you exceed the limit, the API returns HTTP <code>429 Too Many Requests</code>.</p>
                <table class="rate-limits-table">
                    <thead>
                        <tr><th>Endpoint</th><th>Method</th><th>Limit</th></tr>
                    </thead>
                    <tbody>
                        <tr><td><code>/api/brands</code></td><td>GET</td><td>120/min</td></tr>
                        <tr><td><code>/api/vehicle-options/&lt;id&gt;</code></td><td>GET</td><td>120/min</td></tr>
                        <tr><td><code>/api/months</code></td><td>GET</td><td>120/min</td></tr>
                        <tr><td><code>/api/default-car</code></td><td>GET</td><td>120/min</td></tr>
                        <tr><td><code>/api/price</code></td><td>POST</td><td>60/min</td></tr>
                        <tr><td><code>/api/compare-vehicles</code></td><td>POST</td><td>30/min</td></tr>
                        <tr><td><code>/api/economic-indicators</code></td><td>POST</td><td>60/min</td></tr>
                        <tr><td><code>/api/depreciation-analysis</code></td><td>GET</td><td>20/min</td></tr>
                        <tr><td><code>/health</code></td><td>GET</td><td>60/min</td></tr>
                    </tbody>
                </table>
            </section>

            <!-- ===== ERROR HANDLING ===== -->
            <section id="error-handling" class="api-docs-section">
                <h2>Error Handling</h2>
                <p>Errors return a JSON object with an <code>error</code> field describing what went wrong.</p>
                <div class="api-code-block">
                    <span class="code-label">json</span>
<span class="code-bracket">{</span>
  <span class="code-key">"error"</span>: <span class="code-string">"Description of what went wrong"</span>
<span class="code-bracket">}</span></div>
                <table class="error-table">
                    <tr><td>400</td><td>Bad Request — missing or invalid parameters</td></tr>
                    <tr><td>404</td><td>Not Found — no data matches your query</td></tr>
                    <tr><td>429</td><td>Too Many Requests — rate limit exceeded</td></tr>
                    <tr><td>500</td><td>Internal Server Error — something went wrong on our end</td></tr>
                </table>
            </section>

            <!-- ===== GET /api/brands ===== -->
            <section id="get-brands" class="api-docs-section">
                <div class="endpoint-header">
                    <span class="method-badge get">GET</span>
                    <span class="endpoint-path">/api/brands</span>
                </div>
                <p class="endpoint-description">List all vehicle brands available in the most recent FIPE reference table.</p>
                <span class="rate-limit-badge">120 requests/minute</span>

                <h3>Parameters</h3>
                <div class="no-params">No parameters required.</div>

                <h3>Request</h3>
                <div class="api-code-block">
                    <span class="code-label">bash</span>
<span class="code-keyword">curl</span> <span class="code-string">https://your-domain.com/api/brands</span></div>

                <div class="response-header">Response <span class="response-status success">200 OK</span></div>
                <div class="api-code-block">
                    <span class="code-label">json</span>
<span class="code-bracket">[</span>
  <span class="code-bracket">{</span>
    <span class="code-key">"id"</span>: <span class="code-number">21</span>,
    <span class="code-key">"name"</span>: <span class="code-string">"Chevrolet"</span>
  <span class="code-bracket">}</span>,
  <span class="code-bracket">{</span>
    <span class="code-key">"id"</span>: <span class="code-number">22</span>,
    <span class="code-key">"name"</span>: <span class="code-string">"Fiat"</span>
  <span class="code-bracket">}</span>,
  <span class="code-bracket">{</span>
    <span class="code-key">"id"</span>: <span class="code-number">59</span>,
    <span class="code-key">"name"</span>: <span class="code-string">"Volkswagen"</span>
  <span class="code-bracket">}</span>
<span class="code-bracket">]</span></div>

                <h3>Errors</h3>
                <table class="error-table">
                    <tr><td>429</td><td>Rate limit exceeded</td></tr>
                    <tr><td>500</td><td>Database query failed</td></tr>
                </table>
            </section>

            <!-- ===== GET /api/vehicle-options ===== -->
            <section id="get-vehicle-options" class="api-docs-section">
                <div class="endpoint-header">
                    <span class="method-badge get">GET</span>
                    <span class="endpoint-path">/api/vehicle-options/&lt;brand_id&gt;</span>
                </div>
                <p class="endpoint-description">Get all models and year variants for a brand, with a lookup table for bidirectional filtering (select model first or year first).</p>
                <span class="rate-limit-badge">120 requests/minute</span>

                <h3>Parameters</h3>
                <table class="params-table">
                    <thead><tr><th>Name</th><th>Type</th><th>In</th><th>Description</th></tr></thead>
                    <tbody>
                        <tr><td><code>brand_id</code></td><td>integer</td><td>URL path <span class="param-required">required</span></td><td>Brand ID (from <code>/api/brands</code>)</td></tr>
                    </tbody>
                </table>

                <h3>Request</h3>
                <div class="api-code-block">
                    <span class="code-label">bash</span>
<span class="code-keyword">curl</span> <span class="code-string">https://your-domain.com/api/vehicle-options/59</span></div>

                <div class="response-header">Response <span class="response-status success">200 OK</span></div>
                <div class="api-code-block">
                    <span class="code-label">json</span>
<span class="code-bracket">{</span>
  <span class="code-key">"models"</span>: <span class="code-bracket">[</span>
    <span class="code-bracket">{</span><span class="code-key">"id"</span>: <span class="code-number">837</span>, <span class="code-key">"name"</span>: <span class="code-string">"Gol 1.0 12V MCV"</span><span class="code-bracket">}</span>,
    <span class="code-bracket">{</span><span class="code-key">"id"</span>: <span class="code-number">838</span>, <span class="code-key">"name"</span>: <span class="code-string">"Golf 1.4 TSI"</span><span class="code-bracket">}</span>
  <span class="code-bracket">]</span>,
  <span class="code-key">"years"</span>: <span class="code-bracket">[</span>
    <span class="code-bracket">{</span><span class="code-key">"id"</span>: <span class="code-number">2100</span>, <span class="code-key">"name"</span>: <span class="code-string">"2024 Gasolina"</span><span class="code-bracket">}</span>,
    <span class="code-bracket">{</span><span class="code-key">"id"</span>: <span class="code-number">2101</span>, <span class="code-key">"name"</span>: <span class="code-string">"2023 Flex"</span><span class="code-bracket">}</span>
  <span class="code-bracket">]</span>,
  <span class="code-key">"model_year_lookup"</span>: <span class="code-bracket">{</span>
    <span class="code-key">"837"</span>: <span class="code-bracket">[</span><span class="code-number">2100</span>, <span class="code-number">2101</span><span class="code-bracket">]</span>,
    <span class="code-key">"838"</span>: <span class="code-bracket">[</span><span class="code-number">2100</span><span class="code-bracket">]</span>
  <span class="code-bracket">}</span>
<span class="code-bracket">}</span></div>

                <h3>Errors</h3>
                <table class="error-table">
                    <tr><td>404</td><td>No models found for this brand</td></tr>
                    <tr><td>429</td><td>Rate limit exceeded</td></tr>
                    <tr><td>500</td><td>Database query failed</td></tr>
                </table>
            </section>

            <!-- ===== GET /api/months ===== -->
            <section id="get-months" class="api-docs-section">
                <div class="endpoint-header">
                    <span class="method-badge get">GET</span>
                    <span class="endpoint-path">/api/months</span>
                </div>
                <p class="endpoint-description">List all available FIPE reference months, sorted from newest to oldest.</p>
                <span class="rate-limit-badge">120 requests/minute</span>

                <h3>Parameters</h3>
                <div class="no-params">No parameters required.</div>

                <h3>Request</h3>
                <div class="api-code-block">
                    <span class="code-label">bash</span>
<span class="code-keyword">curl</span> <span class="code-string">https://your-domain.com/api/months</span></div>

                <div class="response-header">Response <span class="response-status success">200 OK</span></div>
                <div class="api-code-block">
                    <span class="code-label">json</span>
<span class="code-bracket">[</span>
  <span class="code-bracket">{</span>
    <span class="code-key">"date"</span>: <span class="code-string">"2024-06-01"</span>,
    <span class="code-key">"label"</span>: <span class="code-string">"junho/2024"</span>
  <span class="code-bracket">}</span>,
  <span class="code-bracket">{</span>
    <span class="code-key">"date"</span>: <span class="code-string">"2024-05-01"</span>,
    <span class="code-key">"label"</span>: <span class="code-string">"maio/2024"</span>
  <span class="code-bracket">}</span>
<span class="code-bracket">]</span></div>

                <h3>Errors</h3>
                <table class="error-table">
                    <tr><td>429</td><td>Rate limit exceeded</td></tr>
                    <tr><td>500</td><td>Database query failed</td></tr>
                </table>
            </section>

            <!-- ===== GET /api/default-car ===== -->
            <section id="get-default-car" class="api-docs-section">
                <div class="endpoint-header">
                    <span class="method-badge get">GET</span>
                    <span class="endpoint-path">/api/default-car</span>
                </div>
                <p class="endpoint-description">Get the default vehicle selection configured for the application. Useful for initializing a UI with a pre-selected vehicle.</p>
                <span class="rate-limit-badge">120 requests/minute</span>

                <h3>Parameters</h3>
                <div class="no-params">No parameters required.</div>

                <h3>Request</h3>
                <div class="api-code-block">
                    <span class="code-label">bash</span>
<span class="code-keyword">curl</span> <span class="code-string">https://your-domain.com/api/default-car</span></div>

                <div class="response-header">Response <span class="response-status success">200 OK</span></div>
                <div class="api-code-block">
                    <span class="code-label">json</span>
<span class="code-bracket">{</span>
  <span class="code-key">"brand"</span>: <span class="code-string">"Volkswagen"</span>,
  <span class="code-key">"brand_id"</span>: <span class="code-number">59</span>,
  <span class="code-key">"model"</span>: <span class="code-string">"Gol 1.0 12V MCV"</span>,
  <span class="code-key">"model_id"</span>: <span class="code-number">837</span>,
  <span class="code-key">"year"</span>: <span class="code-string">"2024 Gasolina"</span>,
  <span class="code-key">"year_id"</span>: <span class="code-number">2100</span>
<span class="code-bracket">}</span></div>

                <h3>Errors</h3>
                <table class="error-table">
                    <tr><td>404</td><td>Default vehicle not found in database</td></tr>
                    <tr><td>429</td><td>Rate limit exceeded</td></tr>
                    <tr><td>500</td><td>Database query failed</td></tr>
                </table>
            </section>

            <!-- ===== POST /api/compare-vehicles ===== -->
            <section id="post-compare-vehicles" class="api-docs-section">
                <div class="endpoint-header">
                    <span class="method-badge post">POST</span>
                    <span class="endpoint-path">/api/compare-vehicles</span>
                </div>
                <p class="endpoint-description">Get price history for up to 5 vehicles. Returns time-series data suitable for charting.</p>
                <span class="rate-limit-badge">30 requests/minute</span>

                <h3>Parameters</h3>
                <table class="params-table">
                    <thead><tr><th>Name</th><th>Type</th><th>In</th><th>Description</th></tr></thead>
                    <tbody>
                        <tr><td><code>vehicle_ids</code></td><td>array of integers</td><td>JSON body <span class="param-required">required</span></td><td>List of ModelYear IDs to compare (max 5)</td></tr>
                        <tr><td><code>start_date</code></td><td>string</td><td>JSON body <span class="param-optional">optional</span></td><td>Start date filter (YYYY-MM-DD)</td></tr>
                        <tr><td><code>end_date</code></td><td>string</td><td>JSON body <span class="param-optional">optional</span></td><td>End date filter (YYYY-MM-DD)</td></tr>
                    </tbody>
                </table>

                <h3>Request</h3>
                <div class="api-code-block">
                    <span class="code-label">bash</span>
<span class="code-keyword">curl</span> -X POST <span class="code-string">https://your-domain.com/api/compare-vehicles</span> \
  -H <span class="code-string">"Content-Type: application/json"</span> \
  -d <span class="code-string">'{"vehicle_ids": [2100, 2101], "start_date": "2023-01-01", "end_date": "2024-06-01"}'</span></div>

                <div class="response-header">Response <span class="response-status success">200 OK</span></div>
                <div class="api-code-block">
                    <span class="code-label">json</span>
<span class="code-bracket">{</span>
  <span class="code-key">"vehicles"</span>: <span class="code-bracket">[</span>
    <span class="code-bracket">{</span>
      <span class="code-key">"name"</span>: <span class="code-string">"Volkswagen Gol 1.0 12V MCV 2024 Gasolina"</span>,
      <span class="code-key">"year_id"</span>: <span class="code-number">2100</span>,
      <span class="code-key">"data"</span>: <span class="code-bracket">[</span>
        <span class="code-bracket">{</span>
          <span class="code-key">"date"</span>: <span class="code-string">"2023-01-01"</span>,
          <span class="code-key">"price"</span>: <span class="code-number">55230.00</span>,
          <span class="code-key">"label"</span>: <span class="code-string">"janeiro/2023"</span>
        <span class="code-bracket">}</span>,
        <span class="code-bracket">{</span>
          <span class="code-key">"date"</span>: <span class="code-string">"2023-02-01"</span>,
          <span class="code-key">"price"</span>: <span class="code-number">55890.00</span>,
          <span class="code-key">"label"</span>: <span class="code-string">"fevereiro/2023"</span>
        <span class="code-bracket">}</span>
      <span class="code-bracket">]</span>
    <span class="code-bracket">}</span>
  <span class="code-bracket">]</span>
<span class="code-bracket">}</span></div>

                <h3>Errors</h3>
                <table class="error-table">
                    <tr><td>400</td><td>Missing <code>vehicle_ids</code> or exceeds maximum of 5</td></tr>
                    <tr><td>404</td><td>No price data found for the given vehicles</td></tr>
                    <tr><td>429</td><td>Rate limit exceeded</td></tr>
                    <tr><td>500</td><td>Database query failed</td></tr>
                </table>
            </section>

            <!-- ===== POST /api/price ===== -->
            <section id="post-price" class="api-docs-section">
                <div class="endpoint-header">
                    <span class="method-badge post">POST</span>
                    <span class="endpoint-path">/api/price</span>
                </div>
                <p class="endpoint-description">Look up a single price point for a specific vehicle at a specific reference month. Uses fuzzy matching for brand and model names.</p>
                <span class="rate-limit-badge">60 requests/minute</span>

                <h3>Parameters</h3>
                <table class="params-table">
                    <thead><tr><th>Name</th><th>Type</th><th>In</th><th>Description</th></tr></thead>
                    <tbody>
                        <tr><td><code>brand</code></td><td>string</td><td>JSON body <span class="param-required">required</span></td><td>Brand name (fuzzy match, e.g. "Volkswagen")</td></tr>
                        <tr><td><code>model</code></td><td>string</td><td>JSON body <span class="param-required">required</span></td><td>Model name (fuzzy match, e.g. "Gol")</td></tr>
                        <tr><td><code>year</code></td><td>string</td><td>JSON body <span class="param-required">required</span></td><td>Year description (exact match, e.g. "2024 Gasolina")</td></tr>
                        <tr><td><code>month</code></td><td>string</td><td>JSON body <span class="param-required">required</span></td><td>Reference month date (YYYY-MM-DD, e.g. "2024-01-01")</td></tr>
                    </tbody>
                </table>

                <h3>Request</h3>
                <div class="api-code-block">
                    <span class="code-label">bash</span>
<span class="code-keyword">curl</span> -X POST <span class="code-string">https://your-domain.com/api/price</span> \
  -H <span class="code-string">"Content-Type: application/json"</span> \
  -d <span class="code-string">'{"brand": "Volkswagen", "model": "Gol", "year": "2024 Gasolina", "month": "2024-01-01"}'</span></div>

                <div class="response-header">Response <span class="response-status success">200 OK</span></div>
                <div class="api-code-block">
                    <span class="code-label">json</span>
<span class="code-bracket">{</span>
  <span class="code-key">"brand"</span>: <span class="code-string">"Volkswagen"</span>,
  <span class="code-key">"model"</span>: <span class="code-string">"Gol 1.0 12V MCV"</span>,
  <span class="code-key">"year"</span>: <span class="code-string">"2024 Gasolina"</span>,
  <span class="code-key">"month"</span>: <span class="code-string">"janeiro/2024"</span>,
  <span class="code-key">"month_date"</span>: <span class="code-string">"2024-01-01"</span>,
  <span class="code-key">"price"</span>: <span class="code-number">56789.00</span>,
  <span class="code-key">"price_formatted"</span>: <span class="code-string">"R$ 56.789,00"</span>,
  <span class="code-key">"fipe_code"</span>: <span class="code-string">"026011-6"</span>
<span class="code-bracket">}</span></div>

                <h3>Errors</h3>
                <table class="error-table">
                    <tr><td>400</td><td>Missing required parameters (brand, model, year, month)</td></tr>
                    <tr><td>404</td><td>No price found for the given combination</td></tr>
                    <tr><td>429</td><td>Rate limit exceeded</td></tr>
                    <tr><td>500</td><td>Database query failed</td></tr>
                </table>
            </section>

            <!-- ===== POST /api/economic-indicators ===== -->
            <section id="post-economic-indicators" class="api-docs-section">
                <div class="endpoint-header">
                    <span class="method-badge post">POST</span>
                    <span class="endpoint-path">/api/economic-indicators</span>
                </div>
                <p class="endpoint-description">Get IPCA (inflation) and CDI (interest rate) data for a date range. Data is sourced from Brazil's Central Bank (BCB) API.</p>
                <span class="rate-limit-badge">60 requests/minute</span>

                <h3>Parameters</h3>
                <table class="params-table">
                    <thead><tr><th>Name</th><th>Type</th><th>In</th><th>Description</th></tr></thead>
                    <tbody>
                        <tr><td><code>start_date</code></td><td>string</td><td>JSON body <span class="param-required">required</span></td><td>Start date (YYYY-MM-DD)</td></tr>
                        <tr><td><code>end_date</code></td><td>string</td><td>JSON body <span class="param-required">required</span></td><td>End date (YYYY-MM-DD)</td></tr>
                    </tbody>
                </table>

                <h3>Request</h3>
                <div class="api-code-block">
                    <span class="code-label">bash</span>
<span class="code-keyword">curl</span> -X POST <span class="code-string">https://your-domain.com/api/economic-indicators</span> \
  -H <span class="code-string">"Content-Type: application/json"</span> \
  -d <span class="code-string">'{"start_date": "2023-01-01", "end_date": "2024-01-01"}'</span></div>

                <div class="response-header">Response <span class="response-status success">200 OK</span></div>
                <div class="api-code-block">
                    <span class="code-label">json</span>
<span class="code-bracket">{</span>
  <span class="code-key">"ipca"</span>: <span class="code-bracket">[</span>
    <span class="code-bracket">{</span><span class="code-key">"date"</span>: <span class="code-string">"2023-01-01"</span>, <span class="code-key">"value"</span>: <span class="code-number">0.53</span><span class="code-bracket">}</span>,
    <span class="code-bracket">{</span><span class="code-key">"date"</span>: <span class="code-string">"2023-02-01"</span>, <span class="code-key">"value"</span>: <span class="code-number">0.84</span><span class="code-bracket">}</span>
  <span class="code-bracket">]</span>,
  <span class="code-key">"cdi"</span>: <span class="code-bracket">[</span>
    <span class="code-bracket">{</span><span class="code-key">"date"</span>: <span class="code-string">"2023-01-01"</span>, <span class="code-key">"value"</span>: <span class="code-number">1.12</span><span class="code-bracket">}</span>,
    <span class="code-bracket">{</span><span class="code-key">"date"</span>: <span class="code-string">"2023-02-01"</span>, <span class="code-key">"value"</span>: <span class="code-number">0.92</span><span class="code-bracket">}</span>
  <span class="code-bracket">]</span>
<span class="code-bracket">}</span></div>

                <h3>Errors</h3>
                <table class="error-table">
                    <tr><td>400</td><td>Missing <code>start_date</code> or <code>end_date</code></td></tr>
                    <tr><td>429</td><td>Rate limit exceeded</td></tr>
                    <tr><td>500</td><td>Failed to fetch data from BCB API</td></tr>
                </table>
            </section>

            <!-- ===== GET /api/depreciation-analysis ===== -->
            <section id="get-depreciation-analysis" class="api-docs-section">
                <div class="endpoint-header">
                    <span class="method-badge get">GET</span>
                    <span class="endpoint-path">/api/depreciation-analysis</span>
                </div>
                <p class="endpoint-description">Get market-wide depreciation statistics, optionally filtered by brand or year. Returns average depreciation rates across all vehicles in the database.</p>
                <span class="rate-limit-badge">20 requests/minute</span>

                <h3>Parameters</h3>
                <table class="params-table">
                    <thead><tr><th>Name</th><th>Type</th><th>In</th><th>Description</th></tr></thead>
                    <tbody>
                        <tr><td><code>brand_id</code></td><td>integer</td><td>Query string <span class="param-optional">optional</span></td><td>Filter by brand ID</td></tr>
                        <tr><td><code>year_id</code></td><td>integer</td><td>Query string <span class="param-optional">optional</span></td><td>Filter by year ID</td></tr>
                    </tbody>
                </table>

                <h3>Request</h3>
                <div class="api-code-block">
                    <span class="code-label">bash</span>
<span class="code-keyword">curl</span> <span class="code-string">"https://your-domain.com/api/depreciation-analysis?brand_id=59"</span></div>

                <div class="response-header">Response <span class="response-status success">200 OK</span></div>
                <div class="api-code-block">
                    <span class="code-label">json</span>
<span class="code-bracket">{</span>
  <span class="code-key">"analysis_type"</span>: <span class="code-string">"by_brand"</span>,
  <span class="code-key">"data"</span>: <span class="code-bracket">[</span>
    <span class="code-bracket">{</span>
      <span class="code-key">"name"</span>: <span class="code-string">"Volkswagen"</span>,
      <span class="code-key">"avg_depreciation"</span>: <span class="code-number">-12.5</span>,
      <span class="code-key">"vehicle_count"</span>: <span class="code-number">45</span>,
      <span class="code-key">"best_retention"</span>: <span class="code-string">"Golf GTI"</span>,
      <span class="code-key">"worst_retention"</span>: <span class="code-string">"Fox"</span>
    <span class="code-bracket">}</span>
  <span class="code-bracket">]</span>
<span class="code-bracket">}</span></div>

                <h3>Errors</h3>
                <table class="error-table">
                    <tr><td>404</td><td>No depreciation data available</td></tr>
                    <tr><td>429</td><td>Rate limit exceeded</td></tr>
                    <tr><td>500</td><td>Database query failed</td></tr>
                </table>
            </section>

            <!-- ===== GET /health ===== -->
            <section id="get-health" class="api-docs-section">
                <div class="endpoint-header">
                    <span class="method-badge get">GET</span>
                    <span class="endpoint-path">/health</span>
                </div>
                <p class="endpoint-description">Health check endpoint for monitoring and load balancers. Returns service status and database connectivity.</p>
                <span class="rate-limit-badge">60 requests/minute</span>

                <h3>Parameters</h3>
                <div class="no-params">No parameters required.</div>

                <h3>Request</h3>
                <div class="api-code-block">
                    <span class="code-label">bash</span>
<span class="code-keyword">curl</span> <span class="code-string">https://your-domain.com/health</span></div>

                <div class="response-header">Response <span class="response-status success">200 OK</span></div>
                <div class="api-code-block">
                    <span class="code-label">json</span>
<span class="code-bracket">{</span>
  <span class="code-key">"status"</span>: <span class="code-string">"healthy"</span>,
  <span class="code-key">"timestamp"</span>: <span class="code-string">"2024-06-15T10:30:00"</span>,
  <span class="code-key">"service"</span>: <span class="code-string">"fipe-price-tracker"</span>,
  <span class="code-key">"checks"</span>: <span class="code-bracket">{</span>
    <span class="code-key">"database"</span>: <span class="code-string">"ok"</span>
  <span class="code-bracket">}</span>
<span class="code-bracket">}</span></div>

                <h3>Errors</h3>
                <table class="error-table">
                    <tr><td>503</td><td>Service Unavailable — database connection failed</td></tr>
                </table>
            </section>

        </main>
    </div>

    <footer>
        <div class="container text-center">
            <p class="mb-0">
                Data from <a href="https://veiculos.fipe.org.br/" target="_blank" rel="noopener noreferrer">FIPE Table</a>
            </p>
            <p class="mb-0 mt-2">
                <i class="bi bi-code-slash"></i>
                Built with <a href="https://www.anthropic.com" target="_blank" rel="noopener noreferrer">Claude</a>
                <i class="bi bi-dot"></i>
                Flask + Python
            </p>
        </div>
    </footer>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>

    <script nonce="{{ g.csp_nonce }}">
    (function() {
        // Theme toggle (same logic as index.html, without Plotly chart update)
        const themeToggle = document.getElementById('themeToggle');
        const themeIcon = themeToggle.querySelector('i');
        const themeText = themeToggle.querySelector('.theme-toggle-text');
        const navbarLogo = document.getElementById('navbarLogo');
        const html = document.documentElement;

        function getInitialTheme() {
            const savedTheme = localStorage.getItem('theme');
            if (savedTheme) return savedTheme;
            if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) return 'dark';
            return 'light';
        }

        function applyTheme(theme) {
            html.setAttribute('data-theme', theme);
            if (theme === 'dark') {
                themeIcon.classList.remove('bi-sun-fill');
                themeIcon.classList.add('bi-moon-stars-fill');
                themeText.textContent = 'Escuro';
            } else {
                themeIcon.classList.remove('bi-moon-stars-fill');
                themeIcon.classList.add('bi-sun-fill');
                themeText.textContent = 'Claro';
            }
            if (navbarLogo) {
                navbarLogo.src = theme === 'dark' ? navbarLogo.dataset.dark : navbarLogo.dataset.light;
            }
        }

        function toggleTheme() {
            const currentTheme = html.getAttribute('data-theme') || 'light';
            const newTheme = currentTheme === 'light' ? 'dark' : 'light';
            localStorage.setItem('theme', newTheme);
            applyTheme(newTheme);
        }

        applyTheme(getInitialTheme());
        themeToggle.addEventListener('click', toggleTheme);

        if (window.matchMedia) {
            window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
                if (!localStorage.getItem('theme')) applyTheme(e.matches ? 'dark' : 'light');
            });
        }

        // Sidebar active link tracking on scroll
        const sections = document.querySelectorAll('.api-docs-section');
        const sidebarLinks = document.querySelectorAll('.api-docs-sidebar-link');

        window.addEventListener('scroll', function() {
            let current = '';
            sections.forEach(function(section) {
                if (window.scrollY >= section.offsetTop - 150) {
                    current = section.getAttribute('id');
                }
            });
            sidebarLinks.forEach(function(link) {
                link.classList.remove('active');
                if (link.getAttribute('href') === '#' + current) {
                    link.classList.add('active');
                }
            });
        });

        // Mobile nav select
        var mobileNav = document.getElementById('mobileNavSelect');
        if (mobileNav) {
            mobileNav.addEventListener('change', function() {
                if (this.value) {
                    document.querySelector(this.value).scrollIntoView({ behavior: 'smooth' });
                }
            });
        }
    })();
    </script>
</body>
</html>
```

**Note:** The theme toggle script and sidebar scroll tracking are already included in the complete template HTML above (inside the `<script nonce="{{ g.csp_nonce }}">` block at the bottom). No separate script file is needed.

- [ ] **Step 2: Commit**

```bash
git add templates/api_docs.html
git commit -m "feat: create API documentation page template with all endpoints"
```

---

### Task 6: Manual verification and final commit

**Files:**
- All modified files

- [ ] **Step 1: Start the app and verify all pages work**

Run: `cd /home/mathe/programming/historico_fipe_webapp && python app.py`

Verify in browser:
1. Homepage (`/`) — API Docs link visible in navbar, right-aligned next to theme toggle
2. API docs page (`/api/docs`) — renders correctly with sidebar, all endpoints
3. Theme toggle works on both pages, persists between page navigation
4. Sidebar links scroll to correct sections
5. Mobile view — sidebar collapses, mobile nav dropdown appears

- [ ] **Step 2: Test CSRF exemption works for external requests**

```bash
# Test that POST endpoints work without CSRF token (simulating external consumer)
curl -X POST http://localhost:5000/api/compare-vehicles \
  -H "Content-Type: application/json" \
  -d '{"vehicle_ids": [1]}'
```

Expected: Should return JSON response (200 or 404 depending on data), NOT a 400 CSRF error.

- [ ] **Step 3: Test that CSRF still works for browser requests**

The webapp's own JavaScript still sends CSRF tokens via the `X-CSRFToken` header. This should continue working as before.

- [ ] **Step 4: Final commit if any adjustments were needed**

```bash
git add -A
git commit -m "fix: adjustments from manual verification of API docs page"
```
