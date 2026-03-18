# API Documentation Page — Design Spec

## Overview

Add a dedicated API documentation page to the FIPE Tracker webapp, accessible at `/api/docs`, with a link in the homepage navbar. The page targets external developers who want to integrate with the FIPE price API programmatically.

## Goals

- Provide comprehensive, developer-friendly API reference documentation
- Match the existing app's visual identity (dark/light mode, glassmorphism, Inter font)
- Enable external developers to consume POST endpoints without CSRF friction
- Zero new dependencies — pure HTML/CSS/JS

## Non-Goals

- Interactive "try it out" functionality (Swagger-style)
- API key authentication system
- Auto-generated docs from code annotations

## Architecture

### New Route

- **`GET /api/docs`** — serves `templates/api_docs.html`
- Rate limited at 20 requests/minute (same as index page)
- CSP nonce pattern identical to index route
- No authentication required

### New Template

- **`templates/api_docs.html`** — standalone page, not embedded in index.html
- Shares navbar structure with homepage (logo, API link, theme toggle)
- Reads theme from `localStorage` using same key as main app

### CSRF Exemption for External API Consumers

Currently, POST endpoints (`/api/compare-vehicles`, `/api/price`, `/api/economic-indicators`) are protected by Flask-WTF's global CSRF. This blocks external consumers (curl, Postman, server-to-server).

**Solution:** Exempt requests that don't originate from a browser session. Skip CSRF validation when the request has no session cookie. This preserves CSRF protection for the webapp's own frontend while allowing programmatic access.

**Implementation in `app.py`:**
- Override `CSRFProtect`'s behavior or use `@csrf.exempt` on API routes with a custom check
- Add a before-request handler that checks for session cookie presence
- If no session cookie, skip CSRF validation for `/api/*` POST routes

**Security consideration:** CSRF attacks require a browser with an active session. Requests without session cookies cannot be CSRF targets, so exempting them is safe.

## Page Layout

### Desktop (>768px)

```
┌─────────────────────────────────────────────────────────┐
│  FIPE Tracker              API Docs │ 🌙 Modo Escuro   │
├──────────────┬──────────────────────────────────────────┤
│              │                                          │
│  SIDEBAR     │  MAIN CONTENT                           │
│  (sticky)    │  (scrollable)                           │
│  ~250px      │  max-width ~900px                       │
│              │                                          │
│  Getting     │  ┌────────────────────────────────────┐  │
│  Started     │  │ GET  /api/brands                   │  │
│  ─────────   │  │ Description...                     │  │
│  Introduction│  │ Rate limit: 120/min                │  │
│  Auth        │  │                                    │  │
│  Rate Limits │  │ Parameters                         │  │
│  Errors      │  │ ┌──────────────────────────────┐   │  │
│              │  │ │ No parameters required.      │   │  │
│  Vehicle     │  │ └──────────────────────────────┘   │  │
│  Data        │  │                                    │  │
│  ─────────   │  │ Request Example                    │  │
│  GET brands  │  │ ┌──────────────────────────────┐   │  │
│  GET options │  │ │ curl https://domain/api/...   │   │  │
│  GET months  │  │ └──────────────────────────────┘   │  │
│  GET default │  │                                    │  │
│              │  │ Response  200 OK                    │  │
│  Price &     │  │ ┌──────────────────────────────┐   │  │
│  History     │  │ │ [{"id": 21, "name": ...}]    │   │  │
│  ─────────   │  │ └──────────────────────────────┘   │  │
│  POST compare│  │                                    │  │
│  POST price  │  │ Error Responses                    │  │
│              │  │ 429 - Rate limit exceeded          │  │
│  Economic    │  │ 500 - Server error                 │  │
│  ─────────   │  └────────────────────────────────────┘  │
│  POST econ.  │                                          │
│  GET deprec. │  (next endpoint...)                      │
│              │                                          │
│  System      │                                          │
│  ─────────   │                                          │
│  GET health  │                                          │
└──────────────┴──────────────────────────────────────────┘
```

### Mobile (<768px)

- Sidebar collapses to a hamburger menu or top dropdown
- Full-width stacked content
- Code blocks horizontally scrollable

## Content Structure

### Top Sections

#### 1. Introduction
- What the API provides (historical FIPE vehicle price data)
- Base URL format
- All responses are JSON
- Dates stored as `YYYY-MM-DD`, displayed in Portuguese (`janeiro/2024`)
- Prices in Brazilian Real format (`R$ 11.520,00`)

#### 2. Authentication
- API is public, no authentication required
- No API keys needed
- POST endpoints can be called directly from any HTTP client

#### 3. Rate Limits
Summary table:

| Endpoint | Method | Rate Limit |
|----------|--------|-----------|
| `/api/brands` | GET | 120/min |
| `/api/vehicle-options/<brand_id>` | GET | 120/min |
| `/api/months` | GET | 120/min |
| `/api/default-car` | GET | 120/min |
| `/api/price` | POST | 60/min |
| `/api/compare-vehicles` | POST | 30/min |
| `/api/economic-indicators` | POST | 60/min |
| `/api/depreciation-analysis` | GET | 20/min |
| `/health` | GET | 60/min |

Returns HTTP `429 Too Many Requests` when exceeded.

#### 4. Error Handling
Standard error response format:
```json
{
  "error": "Description of what went wrong"
}
```

HTTP status codes used: 400 (bad request), 404 (not found), 429 (rate limited), 500 (server error).

### Endpoint Sections

Each endpoint section contains:

1. **Header** — method badge (green GET / blue POST) + endpoint path
2. **Description** — what the endpoint does
3. **Rate limit badge** — e.g., "120 requests/minute"
4. **Parameters table** — name, type, required/optional, description
5. **Request example** — curl command with headers and body (for POST)
6. **Response example** — full JSON with realistic FIPE data
7. **Error responses** — table of possible error codes with descriptions

#### Endpoint Categories

**Vehicle Data:**
- `GET /api/brands` — List all brands in the latest FIPE table
- `GET /api/vehicle-options/<brand_id>` — Models, years, and bidirectional filtering lookup for a brand
- `GET /api/months` — All available reference months
- `GET /api/default-car` — Default vehicle selection (names + IDs)

**Price & History:**
- `POST /api/compare-vehicles` — Price history for up to 5 vehicles (params: `vehicle_ids[]`, `start_date`, `end_date`)
- `POST /api/price` — Single price lookup (params: `brand`, `model`, `year`, `month`)

**Economic & Market:**
- `POST /api/economic-indicators` — IPCA and CDI data for date ranges (params: `start_date`, `end_date`)
- `GET /api/depreciation-analysis` — Market-wide depreciation statistics (query params: `brand_id`, `year_id`)

**System:**
- `GET /health` — Health check with database connectivity status

## Visual Design

### Theme Support
- Reads from `localStorage` using same key as main app (`theme` or equivalent)
- All elements adapt to dark/light mode
- Code blocks use dark background in both modes (Catppuccin-style syntax highlighting)

### Styling
- Same font family as main app (Inter)
- Same glassmorphism navbar
- Same color palette and border-radius patterns
- Method badges: GET = `#27ae60` (green), POST = `#2980b9` (blue)
- Rate limit badges: `rgba(241,196,15,0.15)` background with `#f39c12` text
- Error code text: `#e74c3c` (red)
- Code blocks: `#1e1e2e` background, monospace font (Fira Code or system monospace)

### Responsive Breakpoints
- Desktop (>768px): sidebar + main content side by side
- Mobile (<=768px): sidebar collapses, stacked layout

## Navbar Integration

Add "API Docs" link to the homepage navbar, right-aligned next to the theme toggle, separated by a vertical divider:

```
FIPE Tracker                    API Docs │ 🌙 Modo Escuro
```

- Link styled with `color: #6c5ce7`, `font-weight: 500`, `font-size: 13px`
- Vertical divider: `1px solid rgba(128,128,128,0.2)`, `height: 20px`
- The API docs page navbar includes a link back to the main app

## Files to Create/Modify

### New Files
- `templates/api_docs.html` — API documentation page template

### Modified Files
- `app.py` — Add `/api/docs` route + CSRF exemption logic for non-browser API requests
- `templates/index.html` — Add "API Docs" link to navbar
- `static/css/style.css` — Add API docs page styles (sidebar, code blocks, method badges, responsive)

## Testing Criteria

- All 9 endpoints documented with complete request/response examples
- Dark/light mode toggle works on docs page
- Theme persists when navigating between homepage and docs page
- Sidebar links scroll to correct endpoint sections
- Mobile layout renders correctly (sidebar collapses)
- External consumers can hit POST endpoints without CSRF errors (when no session cookie)
- Rate limit information matches actual app configuration
- All JSON response examples use realistic FIPE data
