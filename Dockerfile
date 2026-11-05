FROM python:3.11-slim

WORKDIR /app

COPY . .

# Everything the image is worth running, in one plain install: since
# 2026-11-01 the package has no feature extras, so `pip install .` brings the
# lint, the alt-text drafter, the language guess, FastAPI, uvicorn and
# fastapi-mcp together.
RUN pip install --no-cache-dir "."

EXPOSE 8000

# Serve what the image was built for. A CMD of `--help` is a container that
# starts, prints and exits — which looks like it works and does nothing.
#
# The MCP server, not bare uvicorn on `api:app`: it serves the same FastAPI
# app with the MCP endpoint mounted on it, so one port answers `/v1/...` and
# `/mcp`. Until 2026-11-04 the CMD was uvicorn on `api:app`, which never
# imports `mcp.py`, so the image had no `/mcp` at all.
#
# Override with any of the command lines:
#
#   docker run --rm -v "$PWD:/work" IMAGE sprezzature-accessibility-lint /work/public
CMD ["sprezzature-accessibility-mcp", "--host", "0.0.0.0", "--port", "8000"]
