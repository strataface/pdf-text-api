#!/usr/bin/env bash
# Upload this directory to Koyeb (no GitHub, no registry) and build with the Dockerfile on the free instance.
# Prereqs: koyeb CLI installed, KOYEB_TOKEN exported (created in the Koyeb dashboard), RAPIDAPI_PROXY_SECRET exported (optional).
# NOT run by the agent: this is a deployment (externally visible).
set -euo pipefail
cd "$(dirname "$0")/.."
koyeb deploy . pdf-text/api \
  --archive-builder docker \
  --archive-ignore-dir .git --archive-ignore-dir .venv --archive-ignore-dir .pytest_cache --archive-ignore-dir __pycache__ \
  --instance-type free --regions fra --ports 8000:http --routes /:8000 \
  --checks 8000:http:/health \
  --env PDFTEXT_TRUST_PROXY=1 ${RAPIDAPI_PROXY_SECRET:+--env RAPIDAPI_PROXY_SECRET=$RAPIDAPI_PROXY_SECRET} \
  --wait
