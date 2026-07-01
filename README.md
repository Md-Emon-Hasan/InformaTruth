# InformaTruth: Explainable AI Fake News Authenticity Analyzer
[![CI/CD](https://github.com/Md-Emon-Hasan/InformaTruth/actions/workflows/main.yml/badge.svg)](https://github.com/Md-Emon-Hasan/InformaTruth/actions) [![Python](https://img.shields.io/badge/python-3.11-blue)](https://python.org) [![PyTorch](https://img.shields.io/badge/PyTorch-%23EE4C2C.svg?style=flat&logo=PyTorch&logoColor=white)](https://pytorch.org/) [![Hugging Face](https://img.shields.io/badge/%F0%9F%A4%97%20Hugging%20Face-Transformers-blue)](https://huggingface.co/) [![LangChain](https://img.shields.io/badge/LangChain-1C3C3C?style=flat&logo=langchain&logoColor=white)](https://python.langchain.com/) [![scikit-learn](https://img.shields.io/badge/scikit--learn-%23F7931E.svg?style=flat&logo=scikit-learn&logoColor=white)](https://scikit-learn.org/) [![Pandas](https://img.shields.io/badge/pandas-%23150458.svg?style=flat&logo=pandas&logoColor=white)](https://pandas.pydata.org/) [![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=flat&logo=fastapi)](https://fastapi.tiangolo.com) [![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=flat&logo=docker&logoColor=white)](https://www.docker.com/) ![React](https://img.shields.io/badge/react-%2320232a.svg?style=flat&logo=react&logoColor=%2361DAFB) ![Tailwind CSS](https://img.shields.io/badge/tailwindcss-%2338B2AC.svg?style=flat&logo=tailwind-css&logoColor=white) ![Vite](https://img.shields.io/badge/vite-%23646CFF.svg?style=flat&logo=vite&logoColor=white)

InformaTruth is an end-to-end AI-powered multi-agent fact-checking system that automatically verifies news articles, PDFs, and web content. It leverages QLoRA (4-bit) fine-tuning of RoBERTa, LangGraph orchestration, RAG pipelines, and fallback retrieval agents to deliver reliable, context-aware verification. The system features a modular multi-agent architecture including Planner, Retriever, Generator, Memory, and Fallback Agents, integrating diverse tools for comprehensive reasoning.

It achieves ~66% accuracy and ~62% macro-F1 (with ~78% recall on fake-news detection) on the LIAR dataset, with 95% query coverage and ~60% improved reliability through intelligent tool routing and memory integration. Designed for real-world deployment, InformaTruth includes a Flask-based responsive UI, FastAPI endpoints, Dockerized containers, and a CI/CD pipeline, enabling enterprise-grade automated fact verification at scale.

[![Project demo video](https://github.com/user-attachments/assets/423ca9a1-caf1-405e-b671-be842d9a1240)](https://github.com/user-attachments/assets/423ca9a1-caf1-405e-b671-be842d9a1240)

[![InformaTruth](https://github.com/user-attachments/assets/1e6717bc-53a3-4848-80a8-252c4eae8f5b)](https://github.com/user-attachments/assets/1e6717bc-53a3-4848-80a8-252c4eae8f5b)
[![InformaTruth](https://github.com/user-attachments/assets/187a8cc1-75dc-46c5-809a-8d88214797e4)](https://github.com/user-attachments/assets/187a8cc1-75dc-46c5-809a-8d88214797e4)

---

## Live Demo

**Try it now**: [InformaTruth — Fake News Detection AI App](https://informatruth.onrender.com)

---

## Tech Stack
| **Category**                | **Technology/Resource**                                                                                |
| --------------------------- | ------------------------------------------------------------------------------------------------------ |
| **Core Framework**          | PyTorch, Transformers, HuggingFace                                                                     |
| **Frontend Framework**      | **React.js** (Vite), Tailwind CSS, DaisyUI                                                             |
| **Backend Framework**       | **FastAPI** (Async, Pydantic)                                                                          |
| **Classification Model**    | QLoRA Fine-tuned RoBERTa-base (4-bit NF4 + LoRA adapters) on LIAR Dataset                              |
| **Explanation Model**       | FLAN-T5-base (Zero-shot Prompting)                                                                     |
| **Training Data**           | LIAR Dataset (Political Fact-Checking)                                                                 |
| **Evaluation Metrics**      | Accuracy, Macro-F1, Per-class (Fake) Precision/Recall/F1, ROC-AUC                                      |
| **Training Framework**      | HuggingFace Trainer                                                                                    |
| **Fine-tuning Method**      | QLoRA — 4-bit NF4 quantized base + LoRA adapters (PEFT) on attention query/key/value projections       |
| **LangGraph Orchestration** | LangGraph (Multi-Agent Directed Acyclic Execution Graph)                                               |
| **Agents Used**             | PlannerAgent, InputHandlerAgent, ToolRouterAgent, ExecutorAgent, ExplanationAgent, FallbackSearchAgent |
| **Input Modalities**        | Raw Text, Website URLs (via Newspaper3k), PDF Documents (via PyMuPDF)                                  |
| **Tool Augmentation**       | DuckDuckGo Search API (Fallback), Wikipedia (Planned), ToolRouter Logic                                |
| **Web Scraping**            | Newspaper3k (HTML → Clean Article)                                                                     |
| **PDF Parsing**             | PyMuPDF (Backend) / PDF.js (Frontend)                                                                  |
| **Explainability**          | Natural language justification generated using FLAN-T5                                                 |
| **State Management**        | Shared State Object (LangGraph-compatible)                                                             |
| **Hosting Platform**        | Render (Docker)                                                                                        |
| **Version Control**         | Git, GitHub                                                                                            |
| **Logging & Debugging**     | Centralized Logs in `logs/` directory                                                                  |
| **Database**                | **SQLite** + **SQLModel** (Auto-persistence of analysis results)                                       |
| **Input Support**           | Text, URLs, PDF documents                                                                              |

---

## Key Features

* **Monolithic & Agentic Architecture**
  Strictly organized codebase following agentic principles with modular separation of concerns.

* **Modern React Frontend**
  A responsive, pixel-perfect UI built with **React**, **Vite**, and **Tailwind CSS**, featuring dark mode and glassmorphism design.

* **FastAPI Backend**
  High-performance asynchronous API handling automatic documentation and efficient model serving.

* **Multi-Format Input Support**
  Accepts raw **text**, **web URLs**, and **PDF documents** (with client-side text extraction).

* **Full NLP Pipeline**
  Integrates **fake news classification** (QLoRA-tuned RoBERTa) and **natural language explanation** (FLAN-T5).

* **Modular Agent-Based Architecture**
  Built using **LangGraph** with modular agents: `Planner`, `Router`, `Executor`, and `Fallback`.

* **Explanation Generation**
  Uses **FLAN-T5** to generate human-readable rationales for model predictions.

* **Comprehensive Testing**
  Targeting 100% test coverage with automated unit and integration tests using `pytest` (Backend) and `vitest` (Frontend).

* **Structured Logging**
  All logs are automatically saved to the `logs/` directory for better debugging and monitoring.

---

## Project File Structure

```bash
InformaTruth/
│
├── .github/
│   └── workflows/
│       └── main.yml                  # CI/CD Configuration
│
├── backend/                          # FastAPI Backend
│   ├── app/                          # Application Package
│   │   ├── agents/                   # Modular Pipeline Agents
│   │   │   ├── executor.py
│   │   │   ├── fallback_search.py
│   │   │   ├── input_handler.py
│   │   │   ├── planner.py
│   │   │   └── router.py
│   │   ├── graph/                    # LangGraph Orchestration
│   │   │   ├── builder.py
│   │   │   └── state.py
│   │   ├── models/                   # AI Model Wrappers
│   │   │   ├── classifier.py
│   │   │   ├── db.py                 # Database Models
│   │   │   └── loader.py
│   │   ├── utils/                    # Shared Utilities
│   │   │   ├── logger.py
│   │   │   └── results.py
│   │   ├── db.py                     # Database Connection & Setup
│   │   └── main.py                   # FastAPI entry point
│   │   └── valid.tsv
│   ├── logs/                         # Application Logs
│   │   └── fake_news_pipeline.log
│   ├── news/                         # Sample Data
│   │   └── news.pdf
│   ├── tests/                        # Backend Tests
│   │   ├── conftest.py
│   │   ├── test_agents.py
│   │   ├── test_api.py
│   │   ├── test_db.py                # Database Integration Tests
│   │   ├── test_edge_cases.py
│   │   ├── test_lifespan.py
│   │   └── test_models.py
│   ├── train/                        # Training module
│   │   ├── config.py
│   │   ├── data_loader.py
│   │   ├── predictor.py
│   │   ├── run.py
│   │   ├── trainer.py
│   │   └── utils.py
│   ├── config.py                     # Global Configuration
│   ├── Dockerfile                    # Backend Dockerfile
│   ├── pyproject.toml                # Project Configuration
│   ├── requirements.txt              # Python dependencies
│   └── setup.py                      # Package Setup
│
├── frontend/                         # React Frontend
│   ├── public/                       # Static Assets
│   ├── src/                          # Source Code
│   │   ├── assets/                   # Images/Vectors
│   │   │   └── react.svg
│   │   ├── components/               # React Components
│   │   │   ├── AnalysisForm.jsx
│   │   │   ├── Footer.jsx
│   │   │   ├── Hero.jsx
│   │   │   ├── Navbar.jsx
│   │   │   └── ResultsParams.jsx
│   │   ├── App.jsx                   # Main App Component
│   │   ├── App.test.jsx              # Frontend Unit Tests
│   │   ├── index.css                 # Tailwind
│   │   ├── main.jsx                 
│   │   └── setupTests.js             
│   ├── Dockerfile                    # Frontend Dockerfile
│   ├── eslint.config.js            
│   ├── index.html                    # HTML Entry Point
│   ├── package-lock.json           
│   ├── package.json                 
│   └── vite.config.js                # Vite Configuration
│
├── docker-compose.yml                # Docker Orchestration
├── demo.mp4                          # Demo Video
├── demo-1.png                        # Demo Image
├── demo-2.png                        # Demo Image
├── LICENSE                           # Project License
├── README.md                         # Documentation
├── render.yml                        # Render Deployment Config
└── run.py                            # Root launch script
```

---

## Getting Started

### 1. Running the Application (Local Development)
To launch both the **FastAPI Backend** and **React Frontend** locally in parallel:
```bash
python run.py
```
- **Backend**: `http://localhost:8000`
- **Frontend**: `http://localhost:5173`

### 2. Running with Docker (Production/Containerized)
To build and run the entire stack using Docker Compose:
```bash
docker-compose up --build
```

### 3. Running Training
To trigger the model training process (ensure you are in `backend/`):
```bash
cd backend
python train/run.py
```

### 4. Running Tests
**Backend (Pytest):**
```bash
cd backend
python -m pytest tests/ --cov=app --cov-report=term-missing
```

**Frontend (Vitest):**
```bash
cd frontend
npm test
```

---

## System Architecture
```mermaid
graph TD
    A[User Input] --> B{Input Type}
    B -->|Text| C[Direct Text Processing]
    B -->|URL| D[Newspaper3k Parser]
    B -->|PDF| E[PDF.js Extraction]

    C --> F[Text Cleaner]
    D --> F
    E --> F

    F --> G[Context Validator]
    G -->|Sufficient Context| H[RoBERTa Classifier]
    G -->|Insufficient Context| I[Web Search Agent]
    
    I --> J[Context Aggregator]
    J --> H

    H --> K[FLAN-T5 Explanation Generator]
    K --> L[Output Formatter]
    
    L --> M[React Frontend]

    style M fill:#e3f2fd,stroke:#90caf9
    style G fill:#fff9c4,stroke:#fbc02d
    style I fill:#fbe9e7,stroke:#ff8a65
    style H fill:#f1f8e9,stroke:#aed581
```

---

## Model Performance

The classifier is fine-tuned with **QLoRA** — a 4-bit NF4 quantized `roberta-base` with double quantization and bfloat16 compute, plus LoRA adapters (`r=16`, `alpha=32`, dropout `0.1`) on the attention query/key/value projections. Training runs for **5 epochs** (learning rate `2e-4`, batch size `16`, weight decay `0.01`). Only ~1.47M parameters (~1.17% of the model) are trainable; the quantized base stays frozen.

Per-epoch validation metrics:

| Epoch | Train Loss | Val Loss | Accuracy | Macro F1 | Precision (Fake) | Recall (Fake) | F1 (Fake) | ROC-AUC |
|-------|------------|----------|----------|----------|------------------|---------------|-----------|---------|
| 1     | 0.6395     | 0.6052   | 0.6807   | 0.6133   | 0.7374           | 0.8160        | 0.7747    | 0.6777  |
| 2     | 0.6120     | 0.5835   | 0.6900   | 0.6049   | 0.7293           | 0.8576        | 0.7883    | 0.6837  |
| 3     | 0.5907     | 0.5937   | 0.6659   | 0.6286   | 0.7630           | 0.7303        | 0.7463    | 0.7015  |
| 4     | 0.5739     | 0.5847   | 0.6877   | 0.6284   | 0.7481           | 0.8079        | 0.7769    | 0.7017  |
| 5     | 0.5553     | 0.5857   | 0.6877   | 0.6327   | 0.7525           | 0.7986        | 0.7748    | 0.7003  |

Final metrics on the held-out **LIAR test set**:

| Metric              | Score  |
|---------------------|--------|
| Accuracy            | 0.6606 |
| Macro F1            | 0.6162 |
| Precision (Fake)    | 0.7205 |
| Recall (Fake)       | 0.7751 |
| F1 (Fake)           | 0.7468 |
| ROC-AUC             | 0.6875 |
| Eval Loss           | 0.6090 |

> Emphasis on **Recall** ensures the model catches most fake news cases.

---

## Professional Testing & Quality

### 1. Linting
**Backend (Ruff):**
```bash
cd backend
ruff check app/ tests/
```
**Frontend (ESLint):**
```bash
cd frontend
npm run lint
```

### 2. Code Formatting
**Backend (Black):**
```bash
cd backend
black app/ tests/
```

---

## CI/CD Pipeline (GitHub Actions)
The project utilizes a comprehensive **GitHub Actions** workflow for automated testing and validation.

### Workflow Features:
- **Backend**:
  - Sets up Python 3.11
  - Installs dependencies from `requirements.txt`
  - Runs **Ruff** for linting
  - Runs **Black** for formatting checks
  - Executs **Pytest** with coverage reporting
- **Frontend**:
  - Sets up Node.js 18
  - Installs dependencies (`npm ci`)
  - Runs **ESLint**
  - Executes **Vitest** unit tests
- **Docker**:
  - Builds `backend` and `frontend` Docker images upon successful tests

### Trigger
The pipeline runs automatically on every `push` and `pull_request` to the `main` branch.

---

## **Developed By**

**Md Emon Hasan**  
**Email:** emon.mlengineer@gmail.com
**WhatsApp:** [+8801834363533](https://wa.me/8801834363533)  
**Portfolio:** [Md-Emon-Hasan](https://github.com/Md-Emon-Hasan)  
**GitHub:** [Md-Emon-Hasan](https://github.com/Md-Emon-Hasan)  
**LinkedIn:** [Md Emon Hasan](https://www.linkedin.com/in/md-emon-hasan-695483237/)  
**Facebook:** [Md Emon Hasan](https://www.facebook.com/mdemon.hasan2001/)

---

## License
MIT License. Free to use with credit.
