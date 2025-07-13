#!/usr/bin/env bash
set -e
render login --api-key "$RENDER_API_KEY"
render blueprint apply render.yaml
render domains add toolcases.com
render domains add www.toolcases.com 