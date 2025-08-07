# 📘 InformaTruth: AI-Driven News Authenticity Analyzer
🧠 Fine-tuned RoBERTa-based Multi-Modal Fake News Detector with Explanation Generation using FLAN-T5, URL/PDF/Text support, and Agentic LangGraph orchestration. Orchestrated through a LangGraph-powered agentic pipeline with Planner, Retriever, Tool Router, Fallback Agent, and LLM Answerer agents, plus memory and dynamic tool augmentation.

[![InformaTruth](https://github.com/user-attachments/assets/60bfca60-19bc-404e-9f97-a57ed6f0b5f1)](https://github.com/user-attachments/assets/60bfca60-19bc-404e-9f97-a57ed6f0b5f1)

---

## 🚀 Live Demo

🖥️ **Try it now**: [InformaTruth — Fake News Detection AI App](https://informatruth.onrender.com)

---

## 🔍 Overview
In the digital age, misinformation spreads rapidly across news outlets, social media, and online platforms. With the increasing difficulty of distinguishing between credible journalism and deceptive content, This agentic AI system detects fake news from text, PDF, or website URLs using a fine-tuned RoBERTa model. It leverages a multi-agent architecture with LangGraph, including Planner, Retriever, Tool Router, and Explanation Agent. When a claim is classified, the system uses FLAN-T5 to generate human-readable reasoning. If local evidence fails, it falls back on Wikipedia or DuckDuckGo search. This production-grade solution supports real-world fact-checking, multi-source ingestion, tool-augmented reasoning, and modular orchestration.

---

## ⚙️ Tech Stack
| **Category**                | **Technology/Resource**                                                                                |
| --------------------------- | ------------------------------------------------------------------------------------------------------ |
| **Core Framework**          | PyTorch, Transformers, HuggingFace                                                                     |
| **Classification Model**    | Fine-tuned RoBERTa-base on LIAR Dataset                                                                |
| **Explanation Model**       | FLAN-T5-base (Zero-shot Prompting)                                                                     |
| **Training Data**           | LIAR Dataset (Political Fact-Checking)                                                                 |
| **Evaluation Metrics**      | Accuracy, Precision, Recall, F1-score                                                                  |
| **Training Framework**      | HuggingFace Trainer                                                                                    |
| **LangGraph Orchestration** | LangGraph (Multi-Agent Directed Acyclic Execution Graph)                                               |
| **Agents Used**             | PlannerAgent, InputHandlerAgent, ToolRouterAgent, ExecutorAgent, ExplanationAgent, FallbackSearchAgent |
| **Input Modalities**        | Raw Text, Website URLs (via Newspaper3k), PDF Documents (via PyMuPDF)                                  |
| **Tool Augmentation**       | DuckDuckGo Search API (Fallback), Wikipedia (Planned), ToolRouter Logic                                |
| **Web Scraping**            | Newspaper3k (HTML → Clean Article)                                                                     |
| **PDF Parsing**             | PyMuPDF                                                                                                |
| **Explainability**          | Natural language justification generated using FLAN-T5                                                 |
| **State Management**        | Shared State Object (LangGraph-compatible)                                                             |
| **Deployment Interface**    | Flask (HTML,CSS,JS)                                                                                |
| **Hosting Platform**        | Render (Docker)                                                                  |
| **Version Control**         | Git, GitHub                                                                                            |
| **Logging & Debugging**     | Logs, Print Debugs, Custom Logger                                                 |
| **Input Support**         | Text, URLs, PDF documents                                                             |

---

## ✅ Key Features

* **🔄 Multi-Format Input Support**
  Accepts raw **text**, **web URLs**, and **PDF documents** with automated preprocessing for each type.

* **🧠 Full NLP Pipeline**
  Integrates summarization (optional), **fake news classification** (RoBERTa), and **natural language explanation** (FLAN-T5).

* **🧱 Modular Agent-Based Architecture**
  Built using **LangGraph** with modular agents: `Planner`, `Tool Router`, `Executor`, `Explanation Agent`, and `Fallback Agent`.

* **📜 Explanation Generation**
  Uses **FLAN-T5** to generate human-readable, zero-shot rationales for model predictions.

* **🧪 Tool-Augmented & Fallback Logic**
  Dynamically queries **DuckDuckGo** when local context is insufficient, enabling robust fallback handling.

* **🧼 Clean, Modular Codebase with Logging**
  Structured using clean architecture principles, agent separation, and informative logging.

* **🌐 Flask with Web UI**
  User-friendly, interactive, and responsive frontend for input, output, and visual explanations.

* **🐳 Dockerized for Deployment**
  Fully containerized setup with `Dockerfile` and `requirements.txt` for seamless deployment.

* **⚙️ CI/CD with GitHub Actions**
  Automated pipelines for testing, linting, and Docker build validation to ensure code quality and production-readiness.

---

## 📦 Project File Structure

```bash
InformaTruth/
│
├── .github/              # GitHub Actions
│   └── workflows/
│       └── main.yml 
│
├── agents/                            # Modular agents (planner, executor, etc.)
│   ├── executor.py
│   ├── fallback_search.py
│   ├── input_handler.py
│   ├── planner.py
│   ├── router.py
│   └── __init__.py
│
├── fine_tuned_liar_detector/         # Fine-tuned RoBERTa model directory
│   ├── config.json
│   ├── vocab.json
│   ├── tokenizer_config.json
│   ├── special_tokens_map.json
│   ├── model.safetensors
│   └── merges.txt
│
├── graph/                            # LangGraph state and builder logic
│   ├── builder.py
│   ├── state.py
│   └── __init__.py
│
├── models/                           # Classification + LLM model loader
│   ├── classifier.py
│   ├── loader.py
│   └── __init__.py
│
├── news/                             # Sample news or test input
│   └── news.pdf
│
├── notebook/                         # Jupyter notebooks for experimentation
│   ├── 1 Fine-Tuning.ipynb
│   └── 2 Fine-Tuning with Multi Agent.ipynb
│
├── static/                           # Static files (CSS, JS)
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── script.js
│
├── templates/                        # HTML templates for Flask UI
│   ├── dj_base.html
│   └── dj_index.html
│
├── tests/                            # Unit tests
│   └── test_app.py
│
├── train/                            # Training logic
│   ├── config.py
│   ├── data_loader.py
│   ├── predictor.py
│   ├── run.py
│   ├── trainer.py
│   └── __init__.py
│
├── utils/                            # Utilities like logging, evaluation
│   ├── logger.py
│   ├── results.py
│   └── __init__.py
│
├── __init__.py                        
├── app.png                           # Demo
├── demo.webm                         # Demo video
├── app.py                            # Flask app entry point
├── main.py                           # Main script / orchestrator
├── config.py                         # Configuratin file
├── setup.py                          # Project setup for pip install
├── render.yaml                       # Project setup render
├── Dockerfile                        # Docker container spec
├── requirements.txt                  # Python dependencies
├── LICENSE                           # License file
├── .gitignore                        # Git ignore rules
├── .gitattributes                    # Git lfs rules
└── README.md                         # Readme
```

---

## 🧱 System Architecture
```mermaid
graph TD
    A[User Input] --> B{Input Type}
    B -->|Text| C[Direct Text Processing]
    B -->|URL| D[Newspaper3k Parser]
    B -->|PDF| E[PyMuPDF Parser]

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
    
    L --> M[Web UI using Flask,HTML,CSS,JS]

    style M fill:#e3f2fd,stroke:#90caf9
    style G fill:#fff9c4,stroke:#fbc02d
    style I fill:#fbe9e7,stroke:#ff8a65
    style H fill:#f1f8e9,stroke:#aed581
```

---

## 📊 Model Performance
| Epoch | Train Loss | Val Loss | Accuracy | F1     | Precision | Recall  |
|-------|------------|----------|----------|--------|-----------|---------|
| 1     | 0.3889     | 0.6674   | 0.7204   | 0.8285 | 0.7461    | 0.9313  |
| 2     | 0.4523     | 0.6771   | 0.7196   | 0.8259 | 0.7511    | 0.9173  |

> Emphasis on **Recall** ensures the model catches most fake news cases.

---

## 🐳 Docker Instructions
### Step 1: Build Docker image
```bash
docker build -t informa-truth-app .
```

### Step 2: Run Docker container
```bash
docker run -p 8501:8501 informa-truth-app
```

---

## ⚙️ CI/CD Pipeline (GitHub Actions)
The CI/CD pipeline automates code checks, Docker image building, and Streamlit app validation.

### Sample Workflow
```yaml
name: CI Pipeline
on: [push]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repo
        uses: actions/checkout@v3

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install flake8 pytest

      - name: Run tests
        run: pytest tests/

      - name: Docker build
        run: docker build -t informa-truth-app .
```

---

## 🌐 Real-World Use Case
* Journalists and media watchdogs
* Educators and students
* Concerned citizens and digital media consumers
* Social media platforms for content moderation

---

## 👤 Author
**Md Emon Hasan**  
📧 iconicemon01@gmail.com  
🔗 [GitHub](https://github.com/Md-Emon-Hasan)
🔗 [LinkedIn](https://www.linkedin.com/in/md-emon-hasan-695483237/)
🔗 [Facebook](https://www.facebook.com/mdemon.hasan2001/)
🔗 [WhatsApp](https://wa.me/8801834363533)

---