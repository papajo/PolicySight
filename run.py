#!/usr/bin/env python3
"""
PolicySight — Development Server Runner
Run this from the project root to start the backend.
"""

import uvicorn
import os
import sys

if __name__ == "__main__":
    backend_dir = os.path.join(os.path.dirname(__file__), "backend")
    os.chdir(backend_dir)
    sys.path.insert(0, backend_dir)
    uvicorn.run(
        "src.main:app",
        host="127.0.0.1",
        port=9999,
        reload=True,
    )
