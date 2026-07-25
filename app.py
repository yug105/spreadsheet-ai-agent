#!/usr/bin/env python3
"""
Enhanced Sheets AI Backend using existing sheetsai system
"""

import os
import sys
import json
import logging
import traceback
from datetime import datetime
from typing import Optional, Dict, Any

from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv

from sheetsai.quadratic_engine import ExactQuadraticEngine
from sheetsai.enhanced_sheets_api import EnhancedGoogleSheetsManager

from google.oauth2 import id_token
from google.auth.transport import requests as google_requests


load_dotenv()

# Environment Variables
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
SERVICE_ACCOUNT_FILE = os.getenv("SERVICE_ACCOUNT_FILE", "test_sheetsai.json")
DEFAULT_SPREADSHEET_ID = os.getenv("DEFAULT_SPREADSHEET_ID", "")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
MODEL_NAME = os.getenv("MODEL_NAME", "anthropic/claude-3.5-sonnet")
MAX_TURNS = int(os.getenv("MAX_TURNS", "8"))

# Configure logging
logging.basicConfig(level=getattr(logging, LOG_LEVEL))
logger = logging.getLogger(__name__)

# Log environment status
logger.info(f"🔧 Environment Configuration:")
logger.info(f"   - API Key Configured: {bool(OPENROUTER_API_KEY)}")
logger.info(f"   - Service Account File: {SERVICE_ACCOUNT_FILE}")
logger.info(f"   - Default Spreadsheet ID: {DEFAULT_SPREADSHEET_ID}")
logger.info(f"   - Model Name: {MODEL_NAME}")
logger.info(f"   - Max Turns: {MAX_TURNS}")
logger.info(f"   - Log Level: {LOG_LEVEL}")

app = FastAPI(title="Enhanced Sheets AI Backend", version="1.0.0")

async def verify_token(req: Request):
    auth_header = req.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        raise HTTPException(
            status_code=401,
            detail="Authorization token is missing or invalid."
        )
    token = auth_header.split('Bearer ')[1]
    try:
        id_token.verify_oauth2_token(token, google_requests.Request())
    except ValueError as e:
        raise HTTPException(
            status_code=401,
            detail=f"Invalid token: {e}"
        )



app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

class QueryRequest(BaseModel):
    spreadsheet_id: Optional[str] = Field(None)
    sheet_name: str = Field(...)
    user_query: str = Field(...)

class QueryResponse(BaseModel):
    success: bool
    result: dict
    execution_time: float
    turns_completed: int
    error_message: str = None

def process_query_with_correct_sheet(spreadsheet_id: str, sheet_name: str, user_query: str) -> dict:
    """Process query with FIXED sheet selection"""
    
    try:
        # Use existing sheetsai system
        manager = EnhancedGoogleSheetsManager(
            credential_file=SERVICE_ACCOUNT_FILE,
            spreadsheet_id=spreadsheet_id
        )
        
        # Get available sheets for debugging
        all_sheets = [ws.title for ws in manager.spreadsheet.worksheets()]
        logger.info(f"🔍 Available sheets: {all_sheets}")
        
        # CRITICAL FIX: Use the proper method to set current worksheet
        success = manager.set_current_worksheet(sheet_name)
        
        if not success:
            return {
                "response": f"Sheet '{sheet_name}' not found. Available sheets: {', '.join(all_sheets)}",
                "error": "Sheet not found",
                "available_sheets": all_sheets
            }
        
        logger.info(f"✅ Successfully set current worksheet to: '{sheet_name}'")
        logger.info(f"✅ Manager current_sheet: {manager.current_sheet}")
        logger.info(f"✅ Manager _current_worksheet: {manager._current_worksheet.title if manager._current_worksheet else 'None'}")
        
        # Verify fix with test data from the correct sheet
        test_data = manager._current_worksheet.get("A1:C3")
        logger.info(f"🔍 Direct test data from '{sheet_name}': {test_data}")
        
        # Initialize AI engine with the properly configured manager
        engine = ExactQuadraticEngine(
            manager=manager,
            api_key=OPENROUTER_API_KEY,
            model_name=MODEL_NAME
        )
        
        # Execute query - the engine will use the manager's current sheet
        result = engine.execute_query(user_query, sheet_name)
        
        # Add verification data
        if result and isinstance(result, dict):
            result['sheet_name'] = sheet_name
            result['requested_sheet'] = sheet_name
            result['available_sheets'] = all_sheets
            result['verification_data'] = {
                'sheet_title': sheet_name,
                'manager_current_sheet': manager.current_sheet,
                'sample_data_A1_C3': test_data,
                'timestamp': datetime.now().isoformat()
            }
        
        logger.info(f"✅ Query processed for sheet: {sheet_name}")
        return result
        
    except Exception as e:
        logger.error(f"❌ Query processing error: {str(e)}")
        logger.error(f"❌ Traceback: {traceback.format_exc()}")
        return {
            "response": f"Error processing query for sheet '{sheet_name}': {str(e)}",
            "error": str(e),
            "sheet_name": sheet_name
        }
        
@app.post("/api/process_query", response_model=QueryResponse, dependencies=[Depends(verify_token)])
async def process_query(request: QueryRequest):
    """Process query with correct sheet selection"""
    
    spreadsheet_id = request.spreadsheet_id or DEFAULT_SPREADSHEET_ID
    start_time = datetime.now()
    
    logger.info(f"🚀 Processing query for sheet: '{request.sheet_name}'")
    
    try:
        result = process_query_with_correct_sheet(
            spreadsheet_id, 
            request.sheet_name, 
            request.user_query
        )
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        return QueryResponse(
            success=True,
            result=result,
            execution_time=execution_time,
            turns_completed=result.get('turns_completed', 1)
        )
        
    except Exception as e:
        execution_time = (datetime.now() - start_time).total_seconds()
        
        return QueryResponse(
            success=False,
            result={"error_details": str(e)},
            execution_time=execution_time,
            turns_completed=0,
            error_message=str(e)
        )

@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "message": "Enhanced Sheets AI Backend is running",
        "timestamp": datetime.now().isoformat(),
        "environment": {
            "api_key_configured": bool(OPENROUTER_API_KEY),
            "service_account_file": SERVICE_ACCOUNT_FILE,
            "default_spreadsheet_id": DEFAULT_SPREADSHEET_ID,
            "model_name": MODEL_NAME,
            "max_turns": MAX_TURNS,
            "log_level": LOG_LEVEL
        }
    }

@app.get("/")
async def root():
    return {
        "service": "Enhanced Sheets AI Backend",
        "version": "1.0.0",
        "status": "running",
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080) 