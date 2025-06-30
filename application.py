import asyncio
import logging
import os
import sys
import uuid
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from pydantic import BaseModel, Field

from backend.config import config
from backend.workflow import (
    Graph,
    competitor_review_events,
    competitor_modifications_pending,
)
from backend.services.mongodb import MongoDBService
from backend.services.pdf_service import PDFService
from backend.services.websocket_manager import WebSocketManager
from fastapi.staticfiles import StaticFiles

# Load environment variables from .env file at startup
env_path = Path(__file__).parent / '.env'
if env_path.exists():
    load_dotenv(dotenv_path=env_path, override=True)

# Configure logging with Docker compatibility
def setup_logging():
    """Set up logging with proper Docker container support."""
    # Use a specific logger name instead of root logger
    app_logger = logging.getLogger("company_research_app")
    
    # Support environment variable for log level
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    try:
        app_logger.setLevel(getattr(logging, log_level))
    except AttributeError:
        app_logger.setLevel(logging.INFO)
        print(f"Warning: Invalid LOG_LEVEL '{log_level}', using INFO")
    
    # Don't modify if already configured
    if app_logger.handlers:
        return app_logger
    
    # Create formatter with more structured output for Docker
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler (primary for Docker)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    app_logger.addHandler(console_handler)
    
    # Don't propagate to root logger to avoid conflicts
    app_logger.propagate = False
    
    app_logger.info("Application logging configured successfully - console only")
    return app_logger

# Initialize logger
logger = setup_logging()

# Log startup information for Docker debugging
logger.info("=" * 50)
logger.info("COMPANY RESEARCH AGENT STARTING")
logger.info("=" * 50)
logger.info(f"Python version: {sys.version}")
logger.info(f"Working directory: {os.getcwd()}")
logger.info(f"Log level: {logger.level}")
logger.info(f"Environment variables loaded: {bool(env_path.exists())}")
logger.info("=" * 50)

app = FastAPI(title="Tavily Company Research API")




app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

manager = WebSocketManager()
pdf_service = PDFService({"pdf_output_dir": "pdfs"})

job_status = defaultdict(lambda: {
    "status": "pending",
    "result": None,
    "error": None,
    "debug_info": [],
    "company": None,
    "report": None,
    "last_update": datetime.now().isoformat()
})

# Initialize MongoDB with centralized configuration
mongodb = None
try:
    if config.validate_config():
        mongodb = MongoDBService(config.MONGODB_URI)
        logger.info("MongoDB integration enabled with centralized configuration")
    else:
        logger.warning("Configuration validation failed. Continuing without MongoDB persistence.")
except Exception as e:
    logger.error(f"Failed to initialize MongoDB: {e}. Continuing without persistence.", exc_info=True)

class ResearchRequest(BaseModel):
    company: str
    company_url: str | None = None
    user_role: str | None = None
    
class ExecutiveSummaryRequest(BaseModel):
    company: str
    company_url: str | None = None
    user_role: str | None = None

class PDFGenerationRequest(BaseModel):
    report_content: str
    company_name: str | None = None

class CompetitorModificationRequest(BaseModel):
    job_id: str
    competitors: list

class CardChatRequest(BaseModel):
    """Request schema for on-demand card chat research."""
    card_context: str = Field(..., description="Textual content of the card the user is asking about")
    question: str = Field(..., description="User's question about the card context")

@app.options("/research")
async def preflight():
    response = JSONResponse(content=None, status_code=200)
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    return response

@app.post("/research")
async def research(data: ExecutiveSummaryRequest):
    try:
        logger.info(f"Received research request for {data.company}")
        job_id = str(uuid.uuid4())
        asyncio.create_task(process_research(job_id, data))

        response = JSONResponse(content={
            "status": "accepted",
            "job_id": job_id,
            "message": "Research started. Connect to WebSocket for updates.",
            "websocket_url": f"/research/ws/{job_id}"
        })
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        return response

    except Exception as e:
        logger.error(f"Error initiating research: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

async def process_research(job_id: str, data: ExecutiveSummaryRequest):
    try:
        if mongodb:
            mongodb.create_job(job_id, data.dict())
        await asyncio.sleep(1)  # Allow WebSocket connection

        await manager.send_status_update(job_id, status="processing", message="Starting research - Phase 1: Discovery")

        graph = Graph(
            company=data.company,
            url=data.company_url,
            user_role=data.user_role,
            websocket_manager=manager,
            job_id=job_id
        )

        # Run only the discovery phase (Phase 1) - will stop at competitor review
        state = {}
        async for s in graph.run(thread={}):
            state.update(s)
        
        # Check if we're waiting for competitor review
        if state.get("competitor_review_pending"):
            logger.info(f"Discovery phase completed for job {job_id}. Waiting for competitor review.")
            # Don't look for report content yet - we're paused for review
            job_status[job_id].update({
                "status": "competitor_review_pending",
                "company": data.company,
                "last_update": datetime.now().isoformat(),
            })
            
        
        # Look for the compiled report in multiple possible locations
        report_content = (
            state.get('report') or 
            (state.get('comprehensive_report_generator') or {}).get('report') or
            (state.get('editor') or {}).get('report') or
            (state.get('executive_report_composer') or {}).get('report')
        )
        if report_content:
            logger.info(f"Found report in final state (length: {len(report_content)})")
            job_status[job_id].update({
                "status": "completed",
                "report": report_content,
                "company": data.company,
                "last_update": datetime.now().isoformat()
            })
            if mongodb:
                mongodb.update_job(job_id=job_id, status="completed")
                mongodb.store_report(job_id=job_id, report_data={"report": report_content})
            await manager.send_status_update(
                job_id=job_id,
                status="completed",
                message="Research completed successfully",
                result={
                    "report": report_content,
                    "company": data.company
                }
            )
        else:
            logger.error(f"Research completed without finding report. State keys: {list(state.keys())}")
            logger.error(f"Editor state: {state.get('editor', {})}")
            logger.error(f"Executive report composer state: {state.get('executive_report_composer', {})}")
            
            # Log the structure of each state node for debugging
            for key in state.keys():
                if isinstance(state[key], dict):
                    logger.error(f"State[{key}] keys: {list(state[key].keys())}")
                    # Check specifically for report in this node
                    if 'report' in state[key]:
                        logger.error(f"Found report in state[{key}] with length: {len(state[key]['report'])}")
                else:
                    logger.error(f"State[{key}] type: {type(state[key])}")
            
            # Check if there was a specific error in the state
            error_message = "No report found"
            if error := state.get('error'):
                error_message = f"Error: {error}"
            
            # Try to create a minimal report from available data
            fallback_content = f"# {data.company} Research Report\n\n"
            fallback_content += "## Overview\n"
            fallback_content += f"Research was completed for {data.company}, but the final report compilation encountered issues.\n\n"
            
            # Add available data sections
            for data_type in ['financial_data', 'news_data', 'company_data']:
                curated_key = f'curated_{data_type}'
                if curated_data := state.get(curated_key):
                    fallback_content += f"## {data_type.replace('_', ' ').title()}\n"
                    fallback_content += f"Found {len(curated_data)} documents for {data_type.replace('_', ' ')}.\n\n"
            
            if site_scrape := state.get('site_scrape'):
                fallback_content += "## Company Website\n"
                fallback_content += f"Company website was analyzed: {site_scrape.get('title', 'Company Information')}\n\n"
            
            fallback_content += "## Note\n"
            fallback_content += "This is a fallback report generated due to issues with the main report compilation process. Please try running the research again for a complete report."
            
            # Store the fallback report
            job_status[job_id].update({
                "status": "completed",
                "report": fallback_content,
                "company": data.company,
                "last_update": datetime.now().isoformat(),
                "note": "Fallback report generated due to compilation issues"
            })
            
            if mongodb:
                mongodb.update_job(job_id=job_id, status="completed")
                mongodb.store_report(job_id=job_id, report_data={"report": fallback_content})
            
            await manager.send_status_update(
                job_id=job_id,
                status="completed",
                message="Research completed with fallback report",
                result={
                    "report": fallback_content,
                    "company": data.company,
                    "note": "Fallback report generated due to compilation issues"
                }
            )

    except Exception as e:
        logger.error(f"Research failed for job {job_id}: {str(e)}", exc_info=True)
        error_message = f"Research failed: {str(e)}"
        await manager.send_status_update(
            job_id=job_id,
            status="failed",
            message=error_message,
            error=str(e)
        )
        if mongodb:
            try:
                mongodb.update_job(job_id=job_id, status="failed", error=str(e))
            except Exception as db_error:
                logger.error(f"Failed to update job status in database: {db_error}", exc_info=True)

# @app.get("/")
# async def ping():
#     return {"message": "Alive"}

@app.get("/research/pdf/{filename}")
async def get_pdf(filename: str):
    pdf_path = os.path.join("pdfs", filename)
    if not os.path.exists(pdf_path):
        raise HTTPException(status_code=404, detail="PDF not found")
    return FileResponse(pdf_path, media_type='application/pdf', filename=filename)

@app.websocket("/research/ws/{job_id}")
async def websocket_endpoint(websocket: WebSocket, job_id: str):
    try:
        await websocket.accept()
        await manager.connect(websocket, job_id)

        if job_id in job_status:
            status = job_status[job_id]
            await manager.send_status_update(
                job_id,
                status=status["status"],
                message="Connected to status stream",
                error=status["error"],
                result=status["result"]
            )

        while True:
            try:
                await websocket.receive_text()
            except WebSocketDisconnect:
                manager.disconnect(websocket, job_id)
                break

    except Exception as e:
        logger.error(f"WebSocket error for job {job_id}: {str(e)}", exc_info=True)
        try:
            manager.disconnect(websocket, job_id)
        except Exception as disconnect_error:
            logger.error(f"Error disconnecting WebSocket for job {job_id}: {disconnect_error}", exc_info=True)

@app.get("/research/{job_id}")
async def get_research(job_id: str):
    if not mongodb:
        raise HTTPException(status_code=501, detail="Database persistence not configured")
    try:
        job = mongodb.get_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Research job not found")
        return job
    except Exception as e:
        logger.error(f"Error retrieving job {job_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error retrieving research job")

@app.get("/research/{job_id}/report")
async def get_research_report(job_id: str):
    if not mongodb:
        if job_id in job_status:
            result = job_status[job_id]
            if report := result.get("report"):
                return {"report": report}
        raise HTTPException(status_code=404, detail="Report not found")
    
    try:
        report = mongodb.get_report(job_id)
        if not report:
            raise HTTPException(status_code=404, detail="Research report not found")
        return report
    except Exception as e:
        logger.error(f"Error retrieving report for job {job_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error retrieving research report")

@app.post("/generate-pdf")
async def generate_pdf(data: PDFGenerationRequest):
    """Generate a PDF from markdown content and stream it to the client."""
    try:
        success, result = pdf_service.generate_pdf_stream(data.report_content, data.company_name)
        if success:
            pdf_buffer, filename = result
            return StreamingResponse(
                pdf_buffer,
                media_type='application/pdf',
                headers={
                    'Content-Disposition': f'attachment; filename="{filename}"'
                }
            )
        else:
            raise HTTPException(status_code=500, detail=result)
    except Exception as e:
        logger.error(f"PDF generation error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}")

@app.get("/research/status/{job_id}")
async def get_research_status(job_id: str):
    """Get the status of a research job."""
    if mongodb:
        try:
            job = mongodb.get_job(job_id)
            if job:
                return {
                    "status": job.get("status", "unknown"),
                    "result": job.get("result"),
                    "error": job.get("error"),
                    "company": job.get("inputs", {}).get("company")
                }
        except Exception as e:
            logger.error(f"Error retrieving job status for {job_id}: {str(e)}", exc_info=True)
            # Fall through to in-memory fallback
    
    # Fallback to in-memory status
    if job_id in job_status:
        return job_status[job_id]
    
    raise HTTPException(status_code=404, detail="Research job not found")

@app.post("/research/competitors/modify")
async def modify_competitors(data: CompetitorModificationRequest):
    """Handle competitor modifications and release the workflow pause."""
    try:
        job_id = data.job_id
        modified_competitors = data.competitors
        
        logger.info(f"Received competitor modifications for job {job_id}: {len(modified_competitors)} competitors")
        
        # Store modified competitors
        job_status[job_id]["modified_competitors"] = modified_competitors

        # Buffer the modifications so the workflow node can pull them
        competitor_modifications_pending[job_id] = modified_competitors

        # Release the workflow pause
        if event := competitor_review_events.get(job_id):
            event.set()
            logger.info(f"Set review event to resume workflow for job {job_id}")
        else:
            logger.warning(f"No review event found for job {job_id}")

        # Notify the frontend that review is complete
        await manager.send_status_update(
            job_id=job_id,
            status="competitor_review_completed",
            message=f"Competitor review completed with {len(modified_competitors)} competitors",
            result={
                "competitors": modified_competitors,
                "step": "Competitor Analysis",
            },
        )

        return {
            "status": "success",
            "message": "Competitor modifications saved – workflow resumed",
            "competitor_count": len(modified_competitors),
        }

    except Exception as e:
        logger.error(
            f"Error modifying competitors for job {data.job_id}: {str(e)}", exc_info=True
        )
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/card_chat")
async def card_chat(data: CardChatRequest):
    """Perform a lightweight, on-demand research cycle to answer a card-specific question.

    1. Use an LLM to produce a handful of highly-relevant Tavily search queries based on the
       card's context and the user's question.
    2. Execute those queries with Tavily (max 3 queries × 5 results each).
    3. Aggregate the documents and feed them back to the LLM (o3-mini) together with the
       card context to generate a concise answer.
    """
    try:
        from fastapi import HTTPException
        from langchain_openai import ChatOpenAI
        from langchain_core.prompts import ChatPromptTemplate
        from tavily import AsyncTavilyClient
        import json, asyncio

        if not config.TAVILY_API_KEY:
            raise HTTPException(status_code=500, detail="TAVILY_API_KEY is not configured")

        # Initialise the o3-mini model once (lower temperature for deterministic queries)
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)

        # 1) Generate Tavily search queries
        query_prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                """You create concise web search queries for Tavily search API. "
                "Receive the card context and the user's analytical question and return"
                " EXACTLY a JSON list (array) of up to 3 strings. Each string should be a"
                " standalone query that will help answer the question. Do not add any"
                " other keys or text – return only valid JSON. """,
            ),
            (
                "user",
                """CARD CONTEXT:\n{card}\n\nQUESTION:\n{question}\n""",
            ),
        ])

        query_output = await llm.ainvoke(
            query_prompt.format_messages(card=data.card_context[:4000], question=data.question)
        )

        try:
            queries = json.loads(query_output.content)
            if not isinstance(queries, list):
                raise ValueError("LLM did not return a list")
        except Exception:
            # Fallback: treat the raw output as a single query list
            queries = [query_output.content.strip()]  # type: ignore

        queries = queries[:3]  # safety cap

        # 2) Execute Tavily searches concurrently
        tavily_client = AsyncTavilyClient(api_key=config.TAVILY_API_KEY)

        async def run_search(q):
            try:
                return await tavily_client.search(query=q, max_results=5)
            except Exception as e:
                logger.error(f"Tavily search failed for '{q}': {e}")
                return {"query": q, "results": []}

        search_tasks = [run_search(q) for q in queries]
        search_results = await asyncio.gather(*search_tasks)

        # 3) Aggregate snippets into a single context block
        research_context_parts = []
        for idx, res in enumerate(search_results):
            q = queries[idx]
            docs = res.get("results", []) if isinstance(res, dict) else []
            for doc in docs:
                snippet = doc.get("snippet", "")
                url = doc.get("url", "")
                title = doc.get("title", "")
                research_context_parts.append(f"- {title} ({url}): {snippet}")
        research_context = "\n".join(research_context_parts)[:6000]  # truncate if huge

        # 4) Final answer synthesis
        answer_prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                """You are an expert business analyst. Using only the information in the"
                " CARD CONTEXT and ADDITIONAL RESEARCH sections, answer the user's"
                " question clearly and concisely. If the information is insufficient,"
                " say so. Cite sources with parentheses containing the domain name, e.g.,"
                " (bloomberg.com)."
                """,
            ),
            (
                "user",
                """CARD CONTEXT:\n{card}\n\nADDITIONAL RESEARCH:\n{research}\n\nQUESTION:\n{question}\n""",
            ),
        ])

        answer_output = await llm.ainvoke(
            answer_prompt.format_messages(
                card=data.card_context[:4000],
                research=research_context,
                question=data.question,
            )
        )

        return {
            "queries": queries,
            "answer": answer_output.content.strip(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"card_chat error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to process card chat request")

frontend_path = Path(__file__).parent / "ui" / "dist"
app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=config.PORT)