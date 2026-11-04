FROM python:3.11-slim

WORKDIR /app

COPY . .

# Everything the image is worth running. The static lint needs no extras at
# all — that is its point — but an image exists to serve the API, and the API
# is only interesting with the alt-text drafter and the language guess behind
# it. A plain `pip install .` built an image that could not serve the thing
# its own CMD named: fastapi and uvicorn live behind the `api` extra so that
# nobody installing the library pays for a web server.
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
