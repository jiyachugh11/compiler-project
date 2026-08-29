# HashSense — Compiler & Hash Analysis Platform

HashSense is a full-stack analysis platform that combines **compiler analysis** with **hash-function benchmarking**.

The system extracts identifiers/symbols from source code, analyzes the compiler workload, and uses the extracted data to evaluate different hashing strategies.

---

# 🚀 Requirements

Before running the project, install:

### Backend

* Python 3.10+
* pip
* FastAPI
* Uvicorn

### Frontend

* Node.js
* npm

---

# 1. Clone the Repository

```bash
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd compiler-project-backend-hash-analysis
```

---

# 2. Backend Setup

Open a terminal in the **repository root**, where `pyproject.toml` is located.

### Create a virtual environment

```bash
python -m venv venv
```

Activate it on Windows:

```powershell
venv\Scripts\activate
```

### Install the backend

```bash
pip install -e .
```

Install FastAPI and Uvicorn:

```bash
pip install fastapi uvicorn
```

---

# 3. Verify the Backend

Run:

```bash
python -c "import compiler; import hashing; print('Backend packages imported successfully')"
```

You should see:

```text
Backend packages imported successfully
```

---

# 4. Start the Backend

From the repository root, run:

```bash
uvicorn api_server:app --reload --port 8000
```

The backend should now be available at:

```text
http://localhost:8000
```

Keep this terminal running.

---

# 5. Backend API Documentation

FastAPI automatically provides API documentation.

Open:

```text
http://localhost:8000/docs
```

You can use this page to inspect and test the available API endpoints.

---

# 6. Frontend Setup

Open a **new terminal**.

Go into the frontend folder:

```bash
cd frontend
```

Install the dependencies:

```bash
npm install
```

---

# 7. Install Tailwind CSS

This project uses **Tailwind CSS v4 with Vite**.

Run:

```bash
npm install tailwindcss @tailwindcss/vite
```

Make sure your `vite.config.js` contains:

```js
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [
    react(),
    tailwindcss(),
  ],
})
```

Your `src/index.css` should contain:

```css
@import "tailwindcss";
```

No `postcss.config.mjs` or `tailwind.config.js` is required for this setup.

---

# 8. Start the Frontend

From the `frontend` folder:

```bash
npm run dev
```

Vite will provide a local URL, usually:

```text
http://localhost:5173
```

Open that URL in your browser.

---

# ▶️ Running the Complete Project

You need **two terminals** running simultaneously.

### Terminal 1 — Backend

From the repository root:

```bash
venv\Scripts\activate
uvicorn api_server:app --reload --port 8000
```

Backend:

```text
http://localhost:8000
```

### Terminal 2 — Frontend

From the `frontend` folder:

```bash
npm run dev
```

Frontend:

```text
http://localhost:5173
```

---

# 🔗 Frontend → Backend Connection

The frontend communicates with the backend using:

```js
const API_URL = "http://localhost:8000";
```

This is located in `frontend/src/App.jsx`.

Therefore, the backend must be running on port `8000` while using the frontend.

---

# 🧠 How the Application Works

## Compiler Analysis

The Compiler Analysis section accepts source code and processes it through the compiler pipeline.

The pipeline performs tasks such as:

* Lexical analysis
* Token extraction
* Identifier/symbol extraction
* Symbol-table analysis
* String interning
* Workload profiling

The resulting workload is passed to the hashing analysis system.

## Hash Benchmarks

The Hash Benchmarks section analyzes the extracted workload using different hash functions.

It provides:

* Hash-function benchmarking
* Hash-table analysis
* Collision analysis
* Bucket distribution analysis
* Performance comparison
* Hash-function recommendations

The results are displayed through the Hash Dashboard.

---

# 🧪 Running Tests

From the repository root:

```bash
pytest
```

If pytest is not installed:

```bash
pip install pytest
```

Then:

```bash
pytest
```

To run a specific test:

```bash
pytest tests/test_lexer.py
```

For hashing tests:

```bash
pytest tests/test_hash_functions.py
```

---

# 🛠️ Useful Commands

### Backend

Create virtual environment:

```bash
python -m venv venv
```

Activate:

```powershell
venv\Scripts\activate
```

Install:

```bash
pip install -e .
```

Run API:

```bash
uvicorn api_server:app --reload --port 8000
```

Run tests:

```bash
pytest
```

### Frontend

Enter frontend:

```bash
cd frontend
```

Install dependencies:

```bash
npm install
```

Start development server:

```bash
npm run dev
```

Build for production:

```bash
npm run build
```

Preview production build:

```bash
npm run preview
```

Run ESLint:

```bash
npm run lint
```

---

# ⚠️ Troubleshooting

### `ModuleNotFoundError: No module named 'compiler'`

From the repository root:

```bash
pip install -e .
```

Then verify:

```bash
python -c "import compiler; print('compiler OK')"
```

### `ModuleNotFoundError: No module named 'hashing'`

Run:

```bash
pip install -e .
```

Then:

```bash
python -c "import hashing; print('hashing OK')"
```

### `Cannot find package '@tailwindcss/vite'`

Go into the frontend:

```bash
cd frontend
```

Then:

```bash
npm install tailwindcss @tailwindcss/vite
```

Restart Vite:

```bash
npm run dev
```

### Frontend cannot connect to backend

Make sure the backend is running:

```bash
uvicorn api_server:app --reload --port 8000
```

Then check:

```text
http://localhost:8000/docs
```

Also make sure `App.jsx` contains:

```js
const API_URL = "http://localhost:8000";
```

---

# 🎨 Frontend Styling

The main UI is built using Tailwind CSS.

The main frontend styling/components are handled by:

* `App.jsx` — main layout and navigation
* `CompilerDashboard.jsx` — Compiler Analysis interface
* `HashDashboard.jsx` — Hash Benchmark interface
* `index.css` — global Tailwind CSS setup

---

# 📌 Development Notes

The application follows this general flow:

```text
Source Code
    ↓
Compiler Analysis
    ↓
Lexer / Symbol Extraction
    ↓
Workload Profiling
    ↓
Hash Analysis
    ↓
Benchmarking & Recommendation
    ↓
Frontend Dashboard
```

The React frontend communicates with the Python backend through the FastAPI API.

---

# 📄 License

Add your project's license information here.
