# FoodBridge AI 🌍🤝

> **Connecting Surplus-Food Donors, Verified Recipient Organizations, and Volunteers**  

---

## 📖 Project Overview

FoodBridge AI is a robust, modular platform designed to rescue surplus food by connecting donors (restaurants, grocers) with verified recipient organizations (food banks, shelters), facilitated by a network of volunteers. By optimizing food allocation, preventing waste, and ensuring compliance with eligibility screening and capacity constraints, FoodBridge aims to foster a sustainable and secure food distribution network.

---

## 🏗️ Architecture & Technology Stack

The project operates as a **modular monolith** with clear separation of concerns, featuring both a Python backend and a React frontend.

### 🟢 Backend (FastAPI, Python)
- **API Routers** (`app/routers/`): Request validation & endpoints for Auth, Donations, Allocations, Deliveries, and Analytics.
- **Authentication & RBAC**: JWT token-based authentication and role guards (Donor, Recipient, Volunteer, Admin).
- **Business Services** (`app/services/`): Core workflows, database transactions, state machines (e.g. Allocation Status, Delivery Workflow).
- **AI Coordination Layer** (`app/agents/`):
  1. *Food Eligibility and Safety Screening Agent* (Rule-based decision support, ensuring safety constraints).
  2. *Intelligent Recipient Matching Agent* (Two-stage hard filter + explainable weighted ranking).
  3. *Logistics Coordination Agent* (Pickup windows, volunteer assignments).
  4. *Demand Prediction Agent* (Machine Learning Random Forest model with feature engineering and synthetic data testing).
- **Data Layer** (`app/models/`): SQLAlchemy 2.0 ORM over a PostgreSQL database with Alembic for versioned schema migrations.
- **Testing**: Comprehensive Pytest suite running regression, end-to-end, and unit tests using an isolated SQLite in-memory database configuration.

### 🔵 Frontend (React, Vite, Tailwind CSS)
- **Framework**: React 18 using Vite for fast HMR and compilation.
- **Styling**: Tailwind CSS configured with an `EcoBridge` theme (Deep Emerald Green, Fresh Green, Warm Amber accents).
- **UI/UX Principles**: 
  - Responsive design (Desktop: top horizontal navigation, Mobile: sticky bottom navigation).
  - Component-based architecture isolating views by user roles.
- **State & Routing**: React Router for Role-based protected routes, context providers for Authentication.

---

## 📁 Directory Structure

```text
foodbridge-ai/
├── backend/
│   ├── alembic/              # Database migration scripts
│   ├── app/
│   │   ├── models/           # SQLAlchemy ORM models (Donation, Allocation, Delivery, User, Profile)
│   │   ├── routers/          # FastAPI routes
│   │   ├── schemas/          # Pydantic data validation schemas
│   │   ├── services/         # Core business logic
│   │   ├── agents/           # AI models & rule-based decision support
│   │   ├── config.py         # App configuration
│   │   └── main.py           # Application entrypoint
│   ├── tests/                # Complete Pytest test suite
│   ├── pyproject.toml        # Poetry/Pip configurations
│   └── requirements.txt      # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── components/       # Reusable UI elements (Navbar, BottomNav)
│   │   ├── contexts/         # React Contexts (AuthContext)
│   │   ├── pages/            # View components (Dashboard, Donations, Allocations, Deliveries)
│   │   ├── lib/              # Utilities (Axios client config)
│   │   ├── App.tsx           # App Router
│   │   └── index.css         # Tailwind global styles
│   ├── package.json          # Node dependencies
│   ├── vite.config.ts        # Vite configuration
│   └── tailwind.config.js    # Tailwind UI thematic settings
└── docker-compose.yml        # PostgreSQL service definition
```

---

## 🚀 Quickstart & Setup

### 1. Prerequisites
- **Python 3.12+**
- **Node.js 18+** & npm
- **Docker** & Docker Compose (for PostgreSQL dev server)

### 2. Backend Setup
```bash
cd backend
python -m venv .venv

# Activate Virtual Environment (Windows)
.\.venv\Scripts\activate
# Activate Virtual Environment (Mac/Linux)
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
cp .env.example .env
```

### 3. Database Initialization (PostgreSQL)
*(Requires Docker Desktop installed on your system. Alternatively, you may skip this step and the app will gracefully fall back to a local SQLite database file).*
```bash
# From repository root
docker compose up -d

# Run migrations
cd backend
alembic upgrade head
```

### 4. Running Backend Tests
*We provide 40+ rigorous Pytest cases evaluating end-to-end user workflows, authorization, transaction consistency, and ML behavior.*
```bash
cd backend
python -m pytest tests/ -v
```

### 5. Running the Backend Server
```bash
cd backend
uvicorn app.main:app --reload --port 8000
```
- API Docs (Swagger): [http://localhost:8000/docs](http://localhost:8000/docs)
- Health Check: [http://localhost:8000/api/health](http://localhost:8000/api/health)

### 6. Frontend Setup & Build
```bash
cd frontend
npm install

# Run the development server
npm run dev

# Create a production build
npm run build
```

---

## 🛡️ Responsible AI & Food Safety Boundaries

- **Not a Certification Body**: The Food Eligibility Agent offers rule-based decision support. It does **not** certify food as safe for consumption, nor does it override mandatory medical or legal requirements.
- **Deterministic Approvals**: Uncertain, missing, or contradictory input data will trigger human review rather than an automatic AI approval.
- **Hard Constraints**: The AI Matching algorithms respect unyielding rules—allocations cannot exceed donor supply limits or recipient capacity limits.
- **Backend Supremacy**: AI models do not bypass server-side authentication, authorization, or capacity limits. The backend remains strictly authoritative.

---

## 📊 Evaluation Results & Known Limitations

- **Thread-Safety (SQLite):** Test environments leverage SQLite memory mappings for speed. Due to known concurrency locking issues within concurrent threads on SQLite, the concurrency-race tests are intentionally skipped in local test suites but have been proven and fortified logically against PostgreSQL (`with_for_update()`).
- **ML Demand Prediction**: The Random Forest regressor is actively wired to project demand based on organizational capacity and past allocations. Due to the lack of 90+ days of historical production data, the model currently evaluates using realistic synthetic datasets. Evaluation performance (e.g. RMSE, MAE) is reported via `model_meta.json`.

---

**Developed for FoodBridge AI Milestone 9.**
