from __future__ import annotations

from mangum import Mangum

from backend.main import app as fastapi_app

# Expose the FastAPI app for `vercel dev` / local testing.
app = fastapi_app

# AWS Lambda style handler used by Vercel's Python runtime.
handler = Mangum(fastapi_app)


