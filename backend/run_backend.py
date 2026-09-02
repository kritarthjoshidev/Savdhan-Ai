#!/usr/bin/env python
"""
Simple backend startup script for local development
Starts the FastAPI server without Docker dependencies
"""
import os
import sys
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Main entry point"""
    logger.info("=" * 60)
    logger.info("SURVEILLANCE BACKEND - LOCAL DEVELOPMENT")
    logger.info("=" * 60)
    
    # Set environment variables for local testing
    os.environ.setdefault("DEBUG", "true")
    os.environ.setdefault("USE_POSTGRES", "0")  # Use SQLite by default
    
    logger.info("Starting FastAPI server...")
    logger.info("API will be available at: http://localhost:8000")
    logger.info("Interactive API docs: http://localhost:8000/docs")
    logger.info("WebSocket alerts: ws://localhost:8000/ws/alerts")
    logger.info("")
    logger.info("Press Ctrl+C to stop the server")
    logger.info("=" * 60)
    
    try:
        import uvicorn
        uvicorn.run(
            "app.api.main:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info"
        )
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
