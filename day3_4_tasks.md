# RepoMind — Week 4 Day 3-4 Frontend Tasks Checklist

This checklist tracks your step-by-step progress during the implementation of the RepoMind web application chat UI.

---

## 📋 Task List

- [x] **Task 1: Configure FastAPI to Serve Static Files**
  - Mount `backend/static` for static files.
  - Redirect GET `/` to serve `backend/static/index.html`.
- [x] **Task 2: Implement HTML & CSS Foundation**
  - Set up `backend/static/index.html` structure.
  - Define custom HSL variables, dark mode styling, and animations in `backend/static/styles.css`.
- [x] **Task 3: Implement Javascript logic in app.js**
  - Wire repository search and `/sync` button functionality.
  - Render RAG answers, chat bubbles, and citations as clickable links to GitHub.
- [x] **Task 4: Verify UI locally in browser**
  - Start the backend server.
  - Connect to `http://localhost:8000/` and run integration test queries.
