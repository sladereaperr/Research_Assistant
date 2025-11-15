# Autonomous AI Research Assistant

A multi-agent system that autonomously discovers emerging scientific domains, generates research questions, collects data, designs experiments, and produces comprehensive research papers.

## Prerequisites

- Python 3.9+
- Node.js 18+
- npm or yarn

## Setup Instructions

### 1. Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create a virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt
```

### 2. Environment Variables

Create a `.env` file in the `backend` directory:

```bash
# Required: Google Gemini API Key
GEMINI_API_KEY=your_gemini_api_key_here

# Optional: Gemini Model (defaults to gemini-2.5-flash)
GEMINI_MODEL=gemini-2.5-flash

# Optional: Tavily API Key (for enhanced web search)
TAVILY_API_KEY=your_tavily_api_key_here

# Optional: Server Port (defaults to 8000)
PORT=8000
```

**Get API Keys:**
- Gemini API Key: https://makersuite.google.com/app/apikey
- Tavily API Key: https://tavily.com (optional, falls back to DuckDuckGo)

### 3. Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install Node dependencies
npm install
```

## Running the Application

### Option 1: Run Both Services Separately (Recommended for Development)

**Terminal 1 - Backend:**
```bash
cd backend
source venv/bin/activate  # If using virtual environment
python main.py
# Or: uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

The application will be available at:
- Frontend: http://localhost:5173 (or the port Vite assigns)
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### Option 2: Run with Docker (if Dockerfile exists)

```bash
docker build -t research-assistant ./backend
docker run -p 8000:8000 --env-file ./backend/.env research-assistant
```

## Testing the Application

### 1. Manual Testing via Web UI

1. Start both backend and frontend servers
2. Open http://localhost:5173 in your browser
3. Click "Start Research" button
4. Watch the progress as agents work:
   - Domain Scout discovers emerging domains
   - Question Generator formulates research questions
   - Data Alchemist collects data
   - Experiment Designer runs statistical analysis
   - Critic evaluates and iterates
   - Orchestrator generates final paper
5. View the generated research paper

### 2. Test Backend API Directly

**Test Health Endpoint:**
```bash
curl http://localhost:8000/health
```

**Test Research Start (SSE Stream):**
```bash
curl -N http://localhost:8000/api/research/start -X POST
```

**View API Documentation:**
Open http://localhost:8000/docs in your browser for interactive API testing

### 3. Test Individual Components

**Test Domain Discovery:**
```python
# In Python shell
from backend.agents.domain_scout import domain_scout
from backend.graph.state import ResearchState

state = ResearchState()
result = await domain_scout.discover_domains(state)
print(result)
```

**Test Paper Generation:**
```python
from backend.agents.orchestrator import orchestrator
from backend.graph.state import ResearchState

state = ResearchState()
# ... populate state with test data ...
result = await orchestrator.generate_final_paper(state)
print(result['paper'])
```

## Troubleshooting

### Common Issues

1. **"GEMINI_API_KEY not found"**
   - Ensure `.env` file exists in `backend/` directory
   - Check that the key is correctly set: `GEMINI_API_KEY=your_key_here`

2. **Port Already in Use**
   - Change PORT in `.env` or kill the process using port 8000
   - For frontend, Vite will automatically use next available port

3. **Module Not Found Errors**
   - Ensure virtual environment is activated
   - Reinstall dependencies: `pip install -r requirements.txt`

4. **CORS Errors**
   - Backend CORS is configured to allow all origins
   - Ensure frontend proxy is configured correctly in `vite.config.js`

5. **LLM Generation Fails**
   - Check API key is valid and has quota
   - System will use fallback content if LLM fails
   - Check console logs for specific error messages

### Debug Mode

Enable verbose logging by setting:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Project Structure

```
.
├── backend/
│   ├── agents/          # AI agent implementations
│   │   ├── domain_scout.py
│   │   ├── question_generator.py
│   │   ├── data_alchemist.py
│   │   ├── experiment_designer.py
│   │   ├── critic.py
│   │   └── orchestrator.py
│   ├── graph/          # LangGraph workflow
│   │   ├── workflow.py
│   │   └── state.py
│   ├── tools/          # External tools
│   │   ├── search.py
│   │   ├── scraper.py
│   │   └── data_processor.py
│   ├── utils/         # Utilities
│   │   ├── llm.py
│   │   ├── memory.py
│   │   └── visualization.py
│   ├── main.py        # FastAPI server
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.jsx    # Main React component
│   │   └── main.jsx
│   └── package.json
└── docs/              # Documentation
```

## Features

- 🔍 **Domain Discovery**: Automatically identifies emerging scientific domains
- 💡 **Question Generation**: Creates novel, testable research questions
- 🧪 **Data Collection**: Gathers data from multiple sources (ArXiv, web, GitHub)
- 🔬 **Experiment Design**: Designs and executes statistical analyses
- 🎯 **Critical Evaluation**: Iteratively improves research quality
- 📝 **Paper Generation**: Produces comprehensive research papers with:
  - Abstract
  - Introduction
  - Methods
  - Results with visualizations
  - Discussion
  - Limitations & Future Work

## API Endpoints

- `GET /` - API information
- `POST /api/research/start` - Start research (SSE stream)
- `GET /api/research/paper/{session_id}` - View generated paper
- `GET /health` - Health check
- `GET /docs` - Interactive API documentation

## License

MIT

