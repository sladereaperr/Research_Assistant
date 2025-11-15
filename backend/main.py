import traceback
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse
import asyncio
import json
from typing import AsyncGenerator
import os
from dotenv import load_dotenv
import base64
from fastapi.responses import HTMLResponse
from backend.graph.workflow import research_workflow
from backend.graph.state import ResearchState

# Load environment variables
load_dotenv()

app = FastAPI(title="Autonomous AI Research Assistant")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store active research sessions
active_sessions = {}

@app.get("/")
async def root():
    return {
        "message": "Autonomous AI Research Assistant API",
        "version": "1.0.0",
        "endpoints": {
            "/api/research/start": "POST - Start research process",
            "/api/research/status/{session_id}": "GET - Get research status",
            "/api/research/paper/{session_id}": "GET - Get research paper"
        }
    }

@app.post("/api/research/start")
async def start_research():
    """Start the research process with streaming updates"""
    
    async def generate_updates() -> AsyncGenerator[str, None]:
        try:
            # Create initial state
            state = ResearchState()
            session_id = "session_" + str(hash(str(asyncio.current_task())))
            
            # Send initial message
            yield f"data: {json.dumps({'type': 'message', 'content': '🚀 Starting autonomous research...'})}\n\n"
            yield f"data: {json.dumps({'type': 'progress', 'value': 0})}\n\n"
            
            # Run workflow with message streaming
            progress_steps = [
                ("Discovering emerging domain", 15),
                ("Generating research questions", 30),
                ("Collecting data", 50),
                ("Designing experiment", 65),
                ("Analyzing results", 80),
                ("Generating paper", 95)
            ]
            
            current_step = 0
            
            # Run the workflow
            async for node_output in run_workflow_with_streaming(state):
                # Send messages from state
                while len(state.messages) > 0:
                    msg = state.messages.pop(0)
                    yield f"data: {json.dumps({'type': 'message', 'content': msg})}\n\n"
                    await asyncio.sleep(0.1)
                
                # Update progress
                if current_step < len(progress_steps):
                    step_name, progress = progress_steps[current_step]
                    yield f"data: {json.dumps({'type': 'progress', 'value': progress})}\n\n"
                    current_step += 1
                
                await asyncio.sleep(0.2)
            
            # Final progress
            yield f"data: {json.dumps({'type': 'progress', 'value': 100})}\n\n"
            
            # Store session
            active_sessions[session_id] = state
            
            # Send completion
            result = {
                "domain": state.selected_domain.get('domain', 'Unknown') if state.selected_domain else 'Unknown',
                "question": state.selected_question.get('question', 'Unknown') if state.selected_question else 'Unknown',
                "confidence": sum(state.confidence_scores.values()) / len(state.confidence_scores) if state.confidence_scores else 70,
                "paperUrl": f"/api/research/paper/{session_id}",
                "sessionId": session_id
            }
            
            yield f"data: {json.dumps({'type': 'complete', 'result': result})}\n\n"
            
        except Exception as e:
            tb = traceback.format_exc()
            yield f"data: {json.dumps({'type': 'error', 'message': str(e), 'trace': tb})}\n\n"
    
    return EventSourceResponse(generate_updates())

async def run_workflow_with_streaming(state: ResearchState):
    """Run workflow and yield after each step"""
    from backend.graph.workflow import research_workflow
    
    # Discover domain
    await research_workflow._discover_domain(state)
    yield {"step": "domain_discovery"}
    
    # Generate questions
    await research_workflow._generate_questions(state)
    yield {"step": "question_generation"}
    
    # Iterate through data collection, experiment, and critique
    # Start with iteration_count = 0, and increment after each cycle
    while state.iteration_count < state.max_iterations:
        state.add_message(f"📍 System: Iteration {state.iteration_count + 1}/{state.max_iterations}")
        
        # Collect data
        await research_workflow._collect_data(state)
        yield {"step": "data_collection"}
        
        # Design experiment
        await research_workflow._design_experiment(state)
        yield {"step": "experiment"}
        
        # Critique
        await research_workflow._critique(state)
        yield {"step": "critique"}
        
        # Check if should continue
        await research_workflow._iterate_or_finalize(state)
        
        # Break if we shouldn't iterate or reached max
        if not state.should_iterate:
            state.add_message(f"✅ System: Quality threshold met. Finalizing...")
            break
        
        if state.iteration_count >= state.max_iterations:
            state.add_message(f"✅ System: Maximum iterations reached. Finalizing...")
            break
    
    # Generate final paper
    await research_workflow._generate_paper(state)
    yield {"step": "paper_generation"}

@app.get("/api/research/paper/{session_id}")
@app.get("/api/research/paper/{session_id}")
async def get_paper(session_id: str):
    """Get the research paper (safe embedding + markdown rendering + visualizations)"""
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    state = active_sessions[session_id]

    if not state.research_paper:
        raise HTTPException(status_code=404, detail="Paper not yet generated")

    # Base64-encode the paper and visualizations JSON so we can safely decode in the browser.
    paper_b64 = base64.b64encode(state.research_paper.encode("utf-8")).decode("ascii")
    visualizations_json = json.dumps(state.visualizations or {})
    viz_b64 = base64.b64encode(visualizations_json.encode("utf-8")).decode("ascii")

    html_content = f"""
    <!doctype html>
    <html lang="en">
    <head>
      <meta charset="utf-8" />
      <meta name="viewport" content="width=device-width,initial-scale=1" />
      <title>Research Paper - {session_id}</title>

      <!-- Marked for Markdown rendering -->
      <script src="https://cdn.jsdelivr.net/npm/marked@12.0.0/marked.min.js"></script>
      <!-- Plotly (for visualizations) -->
      <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>

      <style>
        body {{
          font-family: system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial;
          background: #f5f7fa;
          color: #243240;
          margin: 0;
          padding: 24px;
        }}
        .container {{
          max-width: 980px;
          margin: 24px auto;
          background: white;
          border-radius: 8px;
          box-shadow: 0 6px 24px rgba(20,30,40,0.08);
          padding: 36px;
        }}
        header h1 {{ margin: 0 0 8px 0; font-size: 24px; }}
        .meta {{ color: #667; margin-bottom: 18px; }}
        .viz {{ margin: 28px 0; padding: 18px; background:#fbfdff; border-radius:6px; border:1px solid #eef4fb; }}
        pre, code {{ background: #f7f8fa; padding: 6px 8px; border-radius: 4px; }}
        h1,h2,h3 {{ color: #10304a; }}
      </style>
    </head>
    <body>
      <div class="container">
        <header>
          <h1>Research Paper</h1>
          <div class="meta">
            Session: <strong>{session_id}</strong>
            &nbsp;•&nbsp; Domain: <strong>{state.selected_domain.get('domain','Unknown') if state.selected_domain else 'Unknown'}</strong>
            &nbsp;•&nbsp; Question: <strong>{state.selected_question.get('question','Unknown') if state.selected_question else 'Unknown'}</strong>
          </div>
        </header>

        <main>
          <div id="paper-content">Loading paper…</div>

          <h2 style="margin-top:32px">Visualizations</h2>
          <div id="viz-container"></div>
        </main>
      </div>

      <script>
      // safe base64 -> utf8 decoder
      function b64DecodeUnicode(str) {{
        // convert base64 to percent-encoded string, then decode
        try {{
          return decodeURIComponent(Array.prototype.map.call(atob(str), function(c) {{
            return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2);
          }}).join(''));
        }} catch (e) {{
          // fallback for very large strings or older browsers
          return atob(str);
        }}
      }}

      // Get the paper markdown and visualizations from base64 strings.
      const paperB64 = "{paper_b64}";
      const vizB64 = "{viz_b64}";

      const markdown = b64DecodeUnicode(paperB64);
      let visualizations = {{}};
      try {{
        visualizations = JSON.parse(b64DecodeUnicode(vizB64));
      }} catch (e) {{
        console.warn("Failed to parse visualizations JSON", e);
      }}

      // Configure marked.js to allow HTML (for visualizations)
      marked.setOptions({{
        breaks: true,
        gfm: true,
        sanitize: false,  // Allow HTML for visualizations
        silent: true
      }});

      // Render markdown using marked.js
      try {{
        const rendered = marked.parse(markdown);
        document.getElementById('paper-content').innerHTML = rendered;
        
        // Re-execute any scripts that were in the HTML (for Plotly charts)
        const scripts = document.getElementById('paper-content').querySelectorAll('script');
        scripts.forEach(oldScript => {{
          const newScript = document.createElement('script');
          Array.from(oldScript.attributes).forEach(attr => {{
            newScript.setAttribute(attr.name, attr.value);
          }});
          newScript.appendChild(document.createTextNode(oldScript.innerHTML));
          oldScript.parentNode.replaceChild(newScript, oldScript);
        }});
      }} catch (e) {{
        console.error("Failed to render paper:", e);
        document.getElementById('paper-content').innerText = "Failed to render paper: " + e.toString();
      }}

      // Insert visualizations (visualizations values are HTML strings produced server-side)
      const vizContainer = document.getElementById('viz-container');
      
      if (Object.keys(visualizations).length === 0) {{
        vizContainer.innerHTML = '<p style="color: #999; font-style: italic;">No visualizations available for this research.</p>';
      }} else {{
        for (const [key, value] of Object.entries(visualizations)) {{
          if (!value || value.trim() === '') continue;
          
          const block = document.createElement('div');
          block.className = 'viz';
          const title = document.createElement('h3');
          title.textContent = key.replace(/_/g, ' ').replace(/\\b\\w/g, c => c.toUpperCase());
          block.appendChild(title);

          // Create a container for the visualization
          const content = document.createElement('div');
          content.style.width = '100%';
          content.style.minHeight = '400px';
          
          // Insert the HTML (which includes Plotly divs and scripts)
          content.innerHTML = value;
          block.appendChild(content);

          vizContainer.appendChild(block);

          // Re-execute scripts for Plotly charts (browsers don't execute scripts via innerHTML)
          const scripts = content.querySelectorAll('script');
          scripts.forEach(oldScript => {{
            const newScript = document.createElement('script');
            Array.from(oldScript.attributes).forEach(attr => {{
              newScript.setAttribute(attr.name, attr.value);
            }});
            newScript.textContent = oldScript.textContent;
            oldScript.parentNode.replaceChild(newScript, oldScript);
          }});
        }}
      }}
      </script>
    </body>
    </html>
    """

    return HTMLResponse(content=html_content)

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)