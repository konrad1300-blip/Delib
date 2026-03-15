# SPEC.md - Delib Database Administration Application

## 1. Project Overview

- **Project Name**: Delib
- **Project Type**: Web Application (Flask + SQLAlchemy)
- **Core Functionality**: A database administration interface with authentication, allowing users to create and manage tree-structured entries (threads with comments)
- **Target Users**: Administrators and regular users who need to manage structured data entries

## 2. Technology Stack

- **Backend**: Flask (Python web framework)
- **Database**: SQLite (development) / SQLAlchemy ORM (supports PostgreSQL, MySQL migration)
- **Authentication**: Flask-Login with password hashing (Werkzeug)
- **Frontend**: HTML5 + CSS3 (custom styling, no frameworks)
- **Template Engine**: Jinja2 (Flask default)

## 3. UI/UX Specification

### Layout Structure

- **Header**: Fixed navigation bar with logo, user info, logout button
- **Main Content**: 
  - Login page: Centered form card
  - Dashboard: Tree view of entries with expand/collapse functionality
  - Entry form: Modal or inline form for adding entries
- **Footer**: Simple copyright notice

### Responsive Breakpoints
- Mobile: < 768px
- Tablet: 768px - 1024px
- Desktop: > 1024px

### Visual Design

**Color Palette**:
- Primary: `#1a1a2e` (Deep navy)
- Secondary: `#16213e` (Dark blue)
- Accent: `#e94560` (Coral red)
- Background: `#0f0f1a` (Near black)
- Surface: `#1f1f3a` (Dark purple-gray)
- Text Primary: `#eaeaea` (Off-white)
- Text Secondary: `#a0a0b0` (Muted gray)
- Success: `#4ade80` (Green)
- Warning: `#fbbf24` (Amber)
- Error: `#ef4444` (Red)

**Typography**:
- Font Family: 'JetBrains Mono' for code/headings, 'Inter' for body text
- Headings: 24px (h1), 20px (h2), 16px (h3)
- Body: 14px
- Small: 12px

**Spacing**:
- Base unit: 8px
- Padding: 16px (cards), 24px (containers)
- Margin between elements: 16px

**Visual Effects**:
- Card shadows: `0 4px 20px rgba(0, 0, 0, 0.4)`
- Hover transitions: 0.2s ease
- Border radius: 8px (cards), 4px (buttons/inputs)
- Subtle glow on accent elements

### Components

**Login Form**:
- Username input field
- Password input field
- Login button (accent color)
- Error message display area

**Navigation Bar**:
- Logo/App name on left
- Current user display
- Logout button
- Role indicator (Admin/User badge)

**Entry Tree**:
- Expandable/collapsible tree nodes
- Visual indentation for hierarchy levels (16px per level)
- Thread entries: Bold title, timestamp, author
- Comment entries: Normal weight, lighter color
- Add child button on hover for each entry
- Delete button for admin only

**Entry Form**:
- Title field (for new threads)
- Content textarea
- Submit button
- Cancel button

## 4. Database Schema

### User Model
```
id: Integer (Primary Key)
username: String (Unique, 50 chars)
password_hash: String (200 chars)
role: String (enum: 'admin', 'user')
created_at: DateTime
```

### Entry Model (Tree Structure)
```
id: Integer (Primary Key)
title: String (200 chars, nullable for comments)
content: Text
author_id: Integer (Foreign Key to User)
parent_id: Integer (Foreign Key to Entry, nullable for root threads)
created_at: DateTime
updated_at: DateTime
```

**Tree Structure**: Adjacency list pattern using parent_id foreign key

## 5. Functionality Specification

### Authentication
- Login with username and password
- Session management with Flask-Login
- Role-based access:
  - **Admin**: Can delete any entry, view all entries
  - **User**: Can create entries, delete own entries
- Logout functionality

### Entry Management
- **Create Thread**: Top-level entry (parent_id = null)
- **Create Comment**: Reply to existing entry (parent_id = entry.id)
- **View Tree**: Recursive tree display with expand/collapse
- **Edit Entry**: Update own entries (or any if admin)
- **Delete Entry**: Cascade delete all children (admin: all, user: own only)

### User Interactions
1. Login → Redirect to dashboard
2. View dashboard → See tree of all entries
3. Click entry → Expand/collapse children
4. Click "Add Thread" → Show new thread form
5. Click "Reply" on entry → Show comment form
6. Click "Delete" → Confirm and delete entry + children

### Edge Cases
- Empty database: Show "No entries yet" message
- Deleted parent: Cascade delete all children
- Long content: Truncate with "show more"
- Deep nesting: Limit to 10 levels with visual indicator

## 6. API Routes

| Method | Route | Description |
|--------|-------|-------------|
| GET | `/` | Home/Login page |
| POST | `/login` | Handle login |
| GET | `/logout` | Handle logout |
| GET | `/dashboard` | Main dashboard with tree |
| POST | `/entry` | Create new thread |
| POST | `/entry/<id>/reply` | Create reply comment |
| POST | `/entry/<id>/delete` | Delete entry |
| GET | `/entry/<id>/edit` | Edit entry form |
| POST | `/entry/<id>/update` | Update entry |

## 7. Default Users

- **Admin**: username: `admin`, password: `admin123`
- **User**: username: `user`, password: `user123`

## 8. Acceptance Criteria

### Visual Checkpoints
- [ ] Login page displays centered card with form
- [ ] Dashboard shows navigation bar with user info
- [ ] Entry tree displays with proper indentation
- [ ] Entries can be expanded/collapsed
- [ ] Forms are styled consistently with theme

### Functional Checkpoints
- [ ] User can log in with valid credentials
- [ ] Invalid credentials show error message
- [ ] Logged out user cannot access dashboard
- [ ] User can create new thread
- [ ] User can reply to existing entry
- [ ] Tree structure displays parent-child relationships
- [ ] Admin can delete any entry
- [ ] User can delete own entries only
- [ ] Logout redirects to login page

## 9. File Structure

```
/home/konrad/Delib/
├── app.py                 # Main Flask application
├── config.py              # Configuration settings
├── models.py              # Database models
├── requirements.txt       # Python dependencies
├── static/
│   └── style.css         # Custom styles
└── templates/
    ├── base.html         # Base template
    ├── login.html        # Login page
    ├── dashboard.html    # Main dashboard
    └── entry_form.html   # Entry creation/edit form
```
