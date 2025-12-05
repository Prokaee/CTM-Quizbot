# Formula Student AI Pipeline

**Gemini 3.0 Pro Powered Quiz & Question Answering System**

A state-of-the-art AI system for Formula Student judges and participants. Upload screenshots of quiz questions and get accurate answers based on **FS Rules 2025** and **FSA Competition Handbook 2025**.

---

## ✨ Features

- 📸 **Screenshot-Based Input** - Upload images of quiz questions, diagrams, or scoring tables
- 🧠 **Gemini 3.0 Pro** - Advanced reasoning for complex questions and trick questions
- ⚡ **Gemini 2.5 Flash** - Lightning-fast question routing and classification
- 🎯 **Deterministic Calculations** - Hardcoded formulas guarantee accuracy (no LLM math errors)
- 📚 **Hybrid RAG** - Retrieves relevant rules with semantic search
- 🔍 **Multimodal Understanding** - Processes text, images, diagrams, and tables
- 📖 **Rule Citations** - Every answer includes exact rule references
- 💬 **Chat Interface** - ChatGPT-style interface with streaming responses

---

## 🏗️ Architecture

### Model Strategy

| Component | Model | Purpose |
|-----------|-------|---------|
| **Reasoning Engine** | Gemini 3.0 Pro | Complex logic, rule interpretation, conflict resolution |
| **Router** | Gemini 2.5 Flash | Fast question classification |
| **Embeddings** | text-embedding-004 | Document vectorization for RAG |
| **Vision** | Gemini 3.0 Pro (multimodal) | Screenshot and diagram analysis |

### Hybrid Formula Execution

```
User Question → Gemini analyzes → Selects formula
                                 ↓
                          Extracts parameters
                                 ↓
                          Hardcoded Python function
                                 ↓
                          Deterministic result
                                 ↓
                          Gemini explains result
```

**Why Hybrid?**
- ✅ **100% accurate calculations** (no LLM hallucination)
- ✅ **Blazing fast** (microseconds vs. seconds)
- ✅ **Fully tested** (comprehensive test suite)
- ✅ **Intelligent** (LLM selects right formula and explains)

---

## 📁 Project Structure

```
CTM-Bot/
├── config/                      # Configuration
│   ├── settings.py             # App settings (loads from .env)
│   ├── gemini_config.py        # Gemini API initialization
│   └── prompts.py              # System prompts
│
├── data/
│   ├── raw/                    # Original PDF files
│   ├── processed/              # Chunked documents (JSON)
│   └── embeddings/             # Vector embeddings
│
├── src/
│   ├── core/
│   │   ├── formulas.py        # Hardcoded FS calculation formulas
│   │   └── tools.py           # Gemini function declarations
│   │
│   ├── processing/
│   │   ├── pdf_processor.py   # PDF text extraction
│   │   ├── chunker.py         # Semantic chunking
│   │   └── embedder.py        # Embedding generation
│   │
│   ├── rag/
│   │   ├── retriever.py       # Hybrid retrieval
│   │   ├── vector_store.py    # Vector search
│   │   └── reranker.py        # Context reranking
│   │
│   ├── agents/
│   │   ├── router.py          # Question router
│   │   ├── reasoning_agent.py # Main reasoning agent
│   │   └── code_executor.py   # Code execution wrapper
│   │
│   └── api/
│       ├── main.py            # FastAPI application
│       ├── routes.py          # API endpoints
│       └── models.py          # Pydantic models
│
├── tests/                      # Test suite
│   └── test_formulas.py       # ✅ 20 passing tests
│
├── scripts/
│   └── process_pdfs.py        # Process PDF documents
│
└── frontend/                   # React chat interface
```

---

## 🚀 Quick Start

### 1. Prerequisites

- Python 3.10+
- Google Gemini API key
- (Optional) Google Cloud Project for Vertex AI

### 2. Installation

```bash
# Clone repository
git clone <repo-url>
cd CTM-Bot

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env and add your API keys
GEMINI_API_KEY=your-api-key-here
GOOGLE_CLOUD_PROJECT=your-project-id  # Optional
```

### 4. Build RAG System

```bash
# Build complete RAG pipeline (recommended)
python scripts/build_rag.py
```

This will:
- Extract text from FSA Handbook and FS Rules PDFs
- Create semantic chunks
- Generate embeddings with Gemini
- Build hybrid vector store
- Test retrieval

**OR** process PDFs only:
```bash
python scripts/process_pdfs.py  # Just PDF → chunks
```

### 5. Run Tests

```bash
# Run formula tests
pytest tests/test_formulas.py -v

# Expected: 20 passed ✅
```

### 6. Run the System

```bash
# Interactive CLI mode (recommended for testing)
python main.py

# Or test the complete system
python scripts/test_system.py
```

### 7. Start API Server (Coming Soon)

```bash
# Start FastAPI backend
uvicorn src.api.main:app --reload

# API will be available at http://localhost:8000
```

### 8. Start Frontend (Coming Soon)

```bash
cd frontend
npm install
npm run dev

# Frontend will be at http://localhost:3000
```

---

## 📖 Usage Examples

### Example 1: Simple Knowledge Question

**Input:**
```
Q: How many fire extinguishers must a vehicle carry?
```

**Output:**
```
According to T 6.4.1, each vehicle must carry two (2) fire extinguishers
with minimum capacity as specified in the rules.

Rule Reference: T 6.4.1 (Fire Extinguishers)
Confidence: 100%
```

### Example 2: Calculation Question

**Input:**
```
Q: Team A scored 4.5 seconds in skidpad. The maximum time is 5.0 seconds.
   What is their score?
```

**Output:**
```
Team A scores 33.46 points in Skidpad.

Calculation (D 4.3.3):
- t_team = 4.5s
- t_max = 5.0s
- Formula: 0.95 × 75 × [(5.0/4.5)² - 1]/0.5625 + 0.05 × 75
- Result: 33.46 points

Rule Reference: D 4.3.3 (Skidpad Scoring)
```

### Example 3: Screenshot Upload

**Input:**
```
[Upload screenshot of scoring table]
Question: "What's the team's total score?"
```

**Output:**
```
Based on the scoring table in the image:

Skidpad: 33.46 points
Acceleration: 68.50 points
Autocross: 92.31 points

Total Dynamic Events Score: 194.27 points

Rule References: D 4.3.3, D 4.2.3, D 5.1
```

---

## 🧪 Testing

### Run All Tests

```bash
pytest tests/ -v --cov=src
```

### Test Individual Components

```bash
# Test formulas only
pytest tests/test_formulas.py -v

# Test with coverage
pytest tests/test_formulas.py --cov=src.core.formulas
```

### Current Test Coverage

- ✅ Formula calculations: 20 tests
- ✅ Skidpad scoring (normal, perfect, minimum, errors)
- ✅ Acceleration scoring
- ✅ Autocross scoring
- ✅ Endurance scoring
- ✅ Efficiency scoring
- ✅ Formula registry

---

## 📊 Supported Formulas

| Event | Formula | Rule Reference | Max Points |
|-------|---------|----------------|------------|
| Skidpad | `calculate_skidpad_score` | D 4.3.3 | 75.0 |
| Acceleration | `calculate_acceleration_score` | D 4.2.3 | 75.0 |
| Autocross | `calculate_autocross_score` | D 5.1 | 100.0 |
| Endurance | `calculate_endurance_score` | D 6.3 | 250.0 |
| Efficiency | `calculate_efficiency_score` | D 7.1 | 100.0 |
| Cost | `calculate_cost_score` | D 3.1 | 100.0 |

---

## 🔧 Configuration

### Environment Variables

See [.env.example](.env.example) for all available options.

Key settings:
```env
# Gemini Models
GEMINI_PRO_MODEL=gemini-3.0-pro
GEMINI_FLASH_MODEL=gemini-2.5-flash

# RAG Settings
CHUNK_SIZE=2000
CHUNK_OVERLAP=200
TOP_K_RETRIEVAL=5

# API
API_PORT=8000
CORS_ORIGINS=http://localhost:3000
```

### Chunking Strategy

- **Chunk Size:** 2000 characters (large chunks for Gemini 3.0's context)
- **Overlap:** 200 characters (ensures continuity)
- **Method:** Semantic boundaries (sections, rules, headings)

---

## 🎯 Rule Priority

**CRITICAL:** When rules conflict:

```
FSA Handbook (AT-rules) > FS Rules (D/T/A/B rules)
```

The system is explicitly programmed to prioritize FSA Handbook over FS Rules.

---

## 📡 API Endpoints

### Primary Chat Endpoint

```http
POST /api/v1/chat
Content-Type: multipart/form-data

Parameters:
  - image: File (screenshot)
  - message: string (optional text)
  - conversation_id: string (optional)

Response:
{
  "answer": "Team A scores 33.46 points...",
  "rule_references": ["D 4.3.3"],
  "calculation_used": "skidpad_score",
  "confidence": 0.95,
  "sources": [...],
  "conversation_id": "uuid"
}
```

### Other Endpoints

- `GET /api/v1/health` - Health check
- `POST /api/v1/calculate` - Direct formula calculation
- `GET /api/v1/formulas` - List available formulas

---

## 🛠️ Development

### Adding New Formulas

1. Add function to `src/core/formulas.py`
2. Add declaration to `src/core/tools.py`
3. Register in `FORMULA_LIBRARY`
4. Add tests to `tests/test_formulas.py`

Example:
```python
# src/core/formulas.py
def calculate_new_event_score(param1: float, param2: float) -> FormulaResult:
    """Calculate new event score per Rule X.Y.Z"""
    score = ... # your calculation
    return FormulaResult(...)

# src/core/tools.py
new_event_declaration = FunctionDeclaration(
    name="calculate_new_event_score",
    description="...",
    parameters={...}
)
```

---

## 📝 Memory & Context

This project uses [PROJECT_MEMORY.md](PROJECT_MEMORY.md) to track:
- Architecture decisions
- Implementation details
- Formula library
- API designs
- RAG strategy

**Always check PROJECT_MEMORY.md before making changes!**

---

## 🚧 Roadmap

### Completed ✅
- [x] Core formula library (6 formulas, 20 passing tests)
- [x] PDF processing pipeline (extraction + chunking)
- [x] Configuration system (Pydantic settings)
- [x] Function declarations for Gemini
- [x] RAG system (FAISS + hybrid search)
- [x] Reasoning agents (Router + Main agent)
- [x] Agent orchestrator (complete pipeline)
- [x] CLI interface (interactive mode)
- [x] Test scripts

### In Progress 🚧
- [ ] FastAPI backend with /chat endpoint
- [ ] React chat interface
- [ ] Image upload handling
- [ ] Streaming responses

### Planned 📋
- [ ] Deployment configuration (Docker)
- [ ] CI/CD pipeline
- [ ] Additional formulas (Design, Business Plan)
- [ ] Multi-language support (DE/EN)

---

## 📄 License

[Add your license here]

---

## 🤝 Contributing

[Add contributing guidelines]

---

## 📞 Support

For issues or questions:
- Check [PROJECT_MEMORY.md](PROJECT_MEMORY.md)
- Review test cases in `tests/`
- Open an issue

---

## 🙏 Acknowledgments

- Formula Student Germany
- Formula Student Austria
- Google Gemini Team

---

**Built with ❤️ for the Formula Student community**
