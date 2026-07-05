from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import uuid
import time

app = FastAPI()

ALLOWED_ORIGIN = "https://dash-0gz2k3.example.com"

EMAIL = "22f3001083@ds.study.iitm.ac.in"

app.add_middleware(
    CORSMiddleware,
    allow_origins=[ALLOWED_ORIGIN],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

class HeaderMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request, call_next):

        start = time.time()

        response = await call_next(request)

        response.headers["X-Request-ID"] = str(uuid.uuid4())

        response.headers["X-Process-Time"] = str(time.time() - start)

        return response

app.add_middleware(HeaderMiddleware)

@app.get("/stats")
async def stats(values: str):

    nums = [int(x) for x in values.split(",")]

    return {
        "email": EMAIL,
        "count": len(nums),
        "sum": sum(nums),
        "min": min(nums),
        "max": max(nums),
        "mean": sum(nums)/len(nums)
    }