#!/bin/bash
# Render startup script
cd /opt/render/project/src
export PYTHONPATH=/opt/render/project/src:$PYTHONPATH
uvicorn backend.api:app --host 0.0.0.0 --port ${PORT:-10000}
