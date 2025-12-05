# Formula Student AI Pipeline - Project Memory & Knowledge Base

**Last Updated:** 2025-12-05
**Status:** Core System Complete (70% Done)
**Model Stack:** Gemini 3.0 Pro + Gemini 2.5 Flash + text-embedding-004

---

## Project Overview

This is a Formula Student Quiz Application powered by Google's latest Gemini models. It helps judges and students answer questions about FS Rules and FSA Handbook with:
- **Native multimodal RAG** (handles text + images)
- **Long context** (2M+ tokens for entire rulebooks)
- **Code execution** for scoring calculations
- **Advanced reasoning** for trick questions

### User Interface Design
**PRIMARY INPUT METHOD:** Screenshot + Optional Text Prompt
- User uploads screenshot of quiz question (may contain diagrams, tables, formulas)
- User can add optional text prompt for clarification
- Interface looks like classic LLM chat (ChatGPT/Claude style)
- Gemini's native vision capabilities handle multimodal inputs seamlessly

**Interface Style:** Clean chat interface (similar to ChatGPT)
- Message bubbles
- Image preview in chat
- Streaming responses
- Code/formula rendering with syntax highlighting

**User Flow:**
1. User opens app → Chat interface appears
2. User clicks "Upload Screenshot" or drag-and-drop image
3. (Optional) User adds text: "What's the score?" or "Explain this rule"
4. User hits Send
5. Backend processes image with Gemini Vision
6. Response streams back with:
   - Answer text
   - Relevant rule citations (clickable)
   - Calculations shown step-by-step
   - Confidence level
7. User can ask follow-up questions in same conversation

---

## Current Project State

### What We Have ✅
- ✅ FSA Competition Handbook 2025 v1.3.0 (in data/raw/)
- ✅ FS Rules 2025 v1.1 (in data/raw/)
- ✅ Complete folder structure
- ✅ Core formula library ([src/core/formulas.py](src/core/formulas.py)) - 6 formulas, tested
- ✅ Gemini function declarations ([src/core/tools.py](src/core/tools.py))
- ✅ Configuration system ([config/](config/))
- ✅ PDF processing pipeline ([src/processing/](src/processing/))
- ✅ Test suite ([tests/test_formulas.py](tests/test_formulas.py)) - 20 passing tests
- ✅ Requirements.txt with all dependencies
- ✅ README.md and documentation
- ✅ PROJECT_MEMORY.md (this file)

### What We're Building Next
- [x] RAG system with embeddings ✅ COMPLETE
- [x] Gemini-powered agent system (router + reasoning) ✅ COMPLETE
- [ ] FastAPI backend with chat endpoint
- [ ] React chat interface (screenshot upload + text chat)

---

## Technical Architecture

### Model Allocation
| Component | Model | Why |
|-----------|-------|-----|
| Router & Simple Queries | Gemini 2.5 Flash | Ultra-fast, cheap, perfect for classification |
| Complex Reasoning | Gemini 3.0 Pro | Best reasoning for logic puzzles and rule conflicts |
| Embeddings | text-embedding-004 | High semantic density for RAG |
| Code Execution | Gemini API native | Safe sandbox for calculations |

### Rule Priority System
**CRITICAL HIERARCHY:**
```
FSA Handbook (AT-rules) > FS Rules (D-rules)
```
When conflicts occur, FSA Handbook ALWAYS wins.

### Formula Execution Strategy: HYBRID APPROACH
**DECISION (2025-12-05): Hardcoded Functions + LLM Intelligence**

**Why Hybrid?**
- ✅ **Deterministic calculations** (no hallucination risk)
- ✅ **Blazing fast** (Python execution, not LLM inference)
- ✅ **Fully testable** (unit tests guarantee correctness)
- ✅ **Intelligent selection** (LLM chooses right formula)
- ✅ **Natural language explanation** (LLM explains the math)

**How It Works:**
```
User Question → Gemini 3.0 Pro analyzes → Selects formula from library
                                      → Extracts parameters
                                      → Calls hardcoded Python function
                                      → Returns result + explanation
```

**Safety Layer:**
For new/uncertain formulas:
1. Gemini Code Execution generates formula from rules
2. Execute in sandbox
3. Compare with hardcoded version
4. Alert if mismatch detected
5. Human verification before adding to library

**Formula Library Structure:**
- Core formulas: **Hardcoded** (skidpad, acceleration, etc.)
- Rare/complex formulas: **Generated + cached** after verification
- All formulas: **Versioned** with rule reference

**Concrete Example:**
```python
# Question: "Team scored 4.5s in skidpad, max time is 5.0s. What's their score?"

# Step 1: Gemini 3.0 Pro analyzes
{
  "formula_needed": "skidpad_score",
  "parameters": {"t_team": 4.5, "t_max": 5.0},
  "rule_reference": "D 4.3.3"
}

# Step 2: Execute HARDCODED function (deterministic!)
result = calculate_skidpad_score(4.5, 5.0)  # → 71.25

# Step 3: Gemini explains
"According to FS Rules D 4.3.3, the team scores **71.25 points**.
Calculation: 0.95 × 75 × ((5.0/4.5)² - 1)/0.5625 + 0.05 × 75 = 71.25"
```

**What We DON'T Do:**
❌ Ask Gemini to calculate: "what is (5.0/4.5)² ?" ← RISKY
✅ Gemini just picks the formula, Python does the math ← SAFE

---

## Folder Structure

```
CTM-Bot/
├── config/                        # Configuration files
│   ├── gemini_config.py          # API keys, model settings
│   ├── prompts.py                # System prompts
│   └── settings.yaml             # App settings
│
├── data/                         # All data files
│   ├── raw/                      # Original PDFs
│   ├── processed/                # Chunked documents
│   └── embeddings/               # Vector embeddings
│
├── src/                          # Source code
│   ├── core/                     # Core functionality
│   │   ├── formulas.py          # FS calculation formulas
│   │   ├── tools.py             # Gemini function declarations
│   │   └── validators.py        # Input validation
│   │
│   ├── processing/               # Document processing
│   │   ├── pdf_processor.py     # Extract from PDFs
│   │   ├── chunker.py           # Smart chunking
│   │   └── embedder.py          # Generate embeddings
│   │
│   ├── rag/                      # Retrieval system
│   │   ├── retriever.py         # Hybrid retrieval
│   │   ├── vector_store.py      # Vertex AI interface
│   │   └── reranker.py          # Context reranking
│   │
│   ├── agents/                   # AI agents
│   │   ├── router.py            # Flash 2.5 router
│   │   ├── reasoning_agent.py   # Gemini 3.0 Pro
│   │   └── code_executor.py     # Code execution
│   │
│   ├── quiz/                     # Quiz application
│   │   ├── question_generator.py
│   │   ├── answer_validator.py
│   │   └── difficulty_manager.py
│   │
│   └── api/                      # REST API
│       ├── main.py              # FastAPI app
│       ├── routes.py            # Endpoints
│       └── models.py            # Data models
│
├── tests/                        # Test suite
├── scripts/                      # Utility scripts
│
└── frontend/                     # Chat-style web interface
    ├── src/
    │   ├── components/
    │   │   ├── ChatInterface.tsx    # Main chat UI
    │   │   ├── MessageBubble.tsx    # Individual messages
    │   │   ├── ImageUpload.tsx      # Screenshot upload
    │   │   ├── MarkdownRenderer.tsx # Render formulas/code
    │   │   └── StreamingText.tsx    # Streaming responses
    │   ├── hooks/
    │   │   └── useChat.ts           # Chat state management
    │   ├── services/
    │   │   └── api.ts               # Backend API calls
    │   └── App.tsx                  # Main app
    ├── public/
    ├── package.json
    └── tailwind.config.js           # Styling (Tailwind CSS)
```

---

## Formula Student Formulas Library

### Key Formulas to Implement

#### 1. Skidpad Score (D 4.3.3)
```python
def calculate_skidpad_score(t_team: float, t_max: float, p_max: float = 75.0):
    """
    Calculates Skidpad score based on FS Rules.

    Args:
        t_team: Team's time in seconds
        t_max: Maximum time threshold
        p_max: Maximum points (default 75.0)

    Returns:
        Score rounded to 2 decimals
    """
    if t_team > t_max:
        return 0.05 * p_max

    term1 = (t_max / t_team) ** 2 - 1
    score = 0.95 * p_max * (term1 / 0.5625) + 0.05 * p_max
    return round(score, 2)
```

#### 2. Acceleration Score (D 4.2.3)
```python
def calculate_acceleration_score(t_team: float, t_max: float, p_max: float = 75.0):
    """Calculates Acceleration score."""
    if t_team > t_max:
        return 0.05 * p_max

    term1 = (t_max / t_team) - 1
    score = 0.95 * p_max * (term1 / 0.3333) + 0.05 * p_max
    return round(score, 2)
```

#### 3. Autocross Score (D 5.1)
```python
def calculate_autocross_score(t_team: float, t_min: float, p_max: float = 100.0):
    """Calculates Autocross score."""
    if t_min == 0:
        return 0

    score = p_max * (t_min / t_team)
    return round(score, 2)
```

#### 4. Endurance Score (D 6.3)
```python
def calculate_endurance_score(t_team: float, t_min: float, p_max: float = 250.0):
    """Calculates Endurance score."""
    if t_min == 0:
        return 0

    score = p_max * (t_min / t_team)
    return round(score, 2)
```

#### 5. Efficiency Score (D 7.1)
```python
def calculate_efficiency_score(e_team: float, e_min: float, t_team_eff: float,
                               t_min_eff: float, p_max: float = 100.0):
    """
    Calculates Efficiency score.

    Args:
        e_team: Team's energy consumption
        e_min: Minimum energy consumption
        t_team_eff: Team's efficiency time
        t_min_eff: Minimum efficiency time
        p_max: Maximum points (default 100.0)
    """
    if e_team == 0 or t_team_eff == 0:
        return 0

    efficiency_factor = (e_min / e_team) * (t_min_eff / t_team_eff)
    score = p_max * min(efficiency_factor, 1.0)
    return round(score, 2)
```

### Additional Formulas Needed
- [ ] Cost calculation
- [ ] Design scoring
- [ ] Business plan scoring
- [ ] Engineering design scoring
- [ ] Penalties calculation

---

## System Prompts

### Master System Prompt (Gemini 3.0 Pro)
```
You are an AI assistant for Formula Student judges, powered by Gemini 3.0 Pro.
Your task is to answer questions based on:
- FS Rules 2025 v1.1
- FSA Competition Handbook 2025 v1.3.0

CRITICAL RULES:
1. ALWAYS use provided tools for calculations - NEVER calculate manually
2. ALWAYS cite exact rule IDs (e.g., "According to AT 8.2.3..." or "Per D 4.3.3...")
3. When FSA Handbook conflicts with FS Rules, FSA Handbook ALWAYS takes precedence
4. For trick questions, analyze carefully before answering
5. If uncertain, explicitly state your confidence level

RESPONSE FORMAT:
- Provide direct answer first
- Cite rule reference
- Show calculation if applicable
- Explain reasoning for complex questions
```

### Router Prompt (Gemini 2.5 Flash)
```
You are a fast routing agent. Classify incoming questions into:

1. KNOWLEDGE - Factual questions about rules (Who, What, Where, When, How many)
2. CALCULATION - Math problems requiring formulas (scores, points, times)
3. REASONING - Complex logic, conflicts, or interpretation questions
4. MULTIMODAL - Questions involving images, diagrams, or tables

Output ONLY the category name.
```

---

## RAG Strategy

### Chunking Strategy
- **Chunk Size:** Full rule sections (not paragraphs)
- **Why:** Gemini 3.0 Pro handles large contexts excellently
- **Overlap:** 100 tokens between chunks
- **Metadata:** Include rule ID, document source, section title

### Retrieval Strategy
1. **Semantic Search:** Top 5 chunks via Vertex AI Vector Search
2. **Keyword Boost:** Exact rule ID matches get priority
3. **Document Weighting:** FSA Handbook chunks get 1.5x relevance boost
4. **Reranking:** Gemini 2.5 Flash reranks by actual relevance

### Vector Store Schema
```json
{
  "chunk_id": "unique_id",
  "text": "full_chunk_text",
  "embedding": [768-dim vector],
  "metadata": {
    "source": "FSA_Handbook | FS_Rules",
    "rule_id": "AT 8.2.3",
    "section": "Technical Inspection",
    "page": 42,
    "priority": 1.5
  }
}
```

---

## API Endpoints

### Core Endpoints

#### 1. Chat Endpoint (Primary)
```
POST /api/v1/chat
Content-Type: multipart/form-data

Input:
  - image: File (screenshot of quiz question) - REQUIRED or OPTIONAL
  - message: string (optional text prompt/clarification)
  - conversation_id: string (optional, for multi-turn chats)

Output:
{
  "answer": "Team A scores 71.25 points according to...",
  "rule_references": ["D 4.3.3", "AT 8.2.1"],
  "calculation_used": "skidpad_score",
  "confidence": 0.95,
  "sources": [
    {"document": "FS_Rules", "section": "D 4.3.3", "page": 42}
  ],
  "conversation_id": "uuid-here"
}
```

#### 2. Direct Calculation Endpoint
```
POST /api/v1/calculate
Input: formula_name, parameters
Output: result, explanation, rule_reference
```

#### 3. Quiz Generation (Optional - if we want auto-generated quizzes)
```
GET /api/v1/quiz/generate
- Input: difficulty, topic (optional)
- Output: question, options, correct_answer_hash

POST /api/v1/quiz/validate
- Input: question_id, user_answer
- Output: correct, explanation, score
```

#### 4. Health & Info
```
GET /api/v1/health
Output: {"status": "ok", "models": ["gemini-3.0-pro", "gemini-2.5-flash"]}
```

---

## Key Dependencies

### Python Packages
```
google-generativeai>=0.4.0
google-cloud-aiplatform>=1.40.0
llama-index>=0.9.0
fastapi>=0.104.0
uvicorn>=0.24.0
pydantic>=2.5.0
python-dotenv>=1.0.0
PyPDF2>=3.0.0
tiktoken>=0.5.0
numpy>=1.24.0
```

### Environment Variables
```env
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
VERTEX_AI_LOCATION=us-central1
GEMINI_API_KEY=your-api-key
VECTOR_SEARCH_INDEX_ID=your-index-id
```

---

## Implementation Roadmap

### Phase 1: Foundation ✅ (Current)
- [x] Project planning
- [x] Memory file creation
- [ ] Folder structure setup
- [ ] Core formula library
- [ ] Basic configuration

### Phase 2: Document Processing
- [ ] PDF text extraction
- [ ] Smart chunking implementation
- [ ] Embedding generation
- [ ] Vector store setup

### Phase 3: Agent System
- [ ] Router with Flash 2.5
- [ ] Reasoning agent with Gemini 3.0 Pro
- [ ] Code execution wrapper
- [ ] Tool integration

### Phase 4: RAG System
- [ ] Retriever implementation
- [ ] Vertex AI Vector Search integration
- [ ] Reranking logic
- [ ] Context optimization

### Phase 5: Quiz Application
- [ ] Question generator
- [ ] Answer validator
- [ ] Difficulty manager
- [ ] Scoring system

### Phase 6: API & Interface
- [ ] FastAPI setup
- [ ] Endpoint implementation
- [ ] Frontend (if needed)
- [ ] Documentation

### Phase 7: Testing & Optimization
- [ ] Unit tests
- [ ] Integration tests
- [ ] Performance optimization
- [ ] Edge case handling

---

## Important Notes & Decisions

### Decision Log
1. **2025-12-05:** Chose Gemini 3.0 Pro + Flash 2.5 stack over other LLMs for native multimodal + code execution
2. **2025-12-05:** Decided on larger chunk sizes to leverage Gemini 3.0's context window
3. **2025-12-05:** FSA Handbook takes absolute priority over FS Rules in conflicts

### Known Challenges
- [ ] Handling multimodal inputs (diagrams in rules)
- [ ] Edge case: Conflicting rules between documents
- [ ] Performance optimization for real-time quiz
- [ ] Hallucination prevention in calculations

### Questions to Resolve
- [ ] Should we support multiple languages (German/English)?
- [ ] Need web interface or just API?
- [ ] How to handle rule updates (versioning)?
- [ ] User authentication needed?

---

## Testing Strategy

### Test Categories
1. **Formula Tests:** All calculations against known correct values
2. **Retrieval Tests:** Verify correct chunks retrieved for sample questions
3. **Reasoning Tests:** Trick questions and edge cases
4. **Integration Tests:** End-to-end question answering
5. **Performance Tests:** Response time under load

### Sample Test Cases
```python
# Test: Skidpad calculation
assert calculate_skidpad_score(4.5, 5.0) == 71.25

# Test: Rule priority (FSA > FS)
# If FSA says X and FS Rules say Y, system must return X

# Test: Multimodal
# Upload image of scoring table, ask about values
```

---

## Resources & References

### Documentation
- [Gemini API Docs](https://ai.google.dev/docs)
- [Vertex AI Documentation](https://cloud.google.com/vertex-ai/docs)
- [LlamaIndex Vertex AI Integration](https://docs.llamaindex.ai/en/stable/examples/llm/gemini.html)

### Formula Student Official Rules
- FSA Competition Handbook 2025 v1.3.0 (in root directory)
- FS Rules 2025 v1.1 (in root directory)

---

## Next Steps

**Immediate Actions:**
1. Create folder structure
2. Set up GCP project and Vertex AI
3. Implement core formula library
4. Start document processing pipeline

**User to Provide:**
- [ ] GCP project ID
- [ ] Confirm if frontend needed
- [ ] Language preference (EN/DE or both)
- [ ] Any specific quiz requirements

---

*This file is continuously updated as the project evolves. Always check this file first before making architectural decisions.*
