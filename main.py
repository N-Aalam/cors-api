import jwt
from jwt import ExpiredSignatureError
from jwt import InvalidTokenError
from fastapi import HTTPException


from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from starlette.middleware.base import BaseHTTPMiddleware
import uuid
import time

import os
import yaml
from dotenv import load_dotenv
from typing import List

app = FastAPI()

load_dotenv()

ALLOWED_ORIGIN = "https://dash-0gz2k3.example.com"

EMAIL = "22f3001083@ds.study.iitm.ac.in"

PUBLIC_KEY = """
-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA2okOHspNjgA+2rTLbeuY
cxiP/hG8C6Sb9iwg3yiLAA4HCnpITcbWCSelbvbYGuc3EbNy4xFyf5Cbj5DHJMID
EkryOgyd2giIIIBOUBj8S63uGcnRpOBh9NFatfNwheKuzsPuVNldu6A9cNteNpXc
WyJjG2axVfmq7i6SuKr1JoWYG7xTTAvKPujSl4OtsQfO3h5NepzdfXpr28oNnzfW
ed+zclR6BcmNNo/WVfJ4xyCLSf0BCOgdTgW6PdaChd1l9VDetJZVEgC5tkyvXsfI
SI6iyrYbKR0NEBSqq4XkadEjsCs4F1RncsS4LlgniT7GlkL9Mce3b0wGLs9/7ZIX
dQIDAQAB
-----END PUBLIC KEY-----
"""

def to_bool(value):
    return str(value).lower() in ["true", "1", "yes", "on"]


def coerce(key, value):
    if key in ["port", "workers"]:
        return int(value)

    if key == "debug":
        return to_bool(value)

    return str(value)

ISSUER = "https://idp.exam.local"

AUDIENCE = "tds-66eeudqb.apps.exam.local"

class TokenRequest(BaseModel):
    token: str

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://dash-0gz2k3.example.com"
    ],
    allow_credentials=False,
    allow_methods=["GET", "OPTIONS"],
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

@app.post("/verify")
async def verify(request: TokenRequest):

    try:

        payload = jwt.decode(
            request.token,
            PUBLIC_KEY,
            algorithms=["RS256"],
            issuer=ISSUER,
            audience=AUDIENCE,
        )

        return {
            "valid": True,
            "email": payload.get("email"),
            "sub": payload.get("sub"),
            "aud": payload.get("aud")
        }

    except (ExpiredSignatureError, InvalidTokenError):

        return JSONResponse(
            status_code=401,
            content={
                "valid": False
            }
        )

@app.get("/effective-config")
async def effective_config(set: List[str] = Query(default=[])):

    config = {
        "port": 8000,
        "workers": 1,
        "debug": False,
        "log_level": "info",
        "api_key": "default-secret-000",
    }

    if os.path.exists("config.development.yaml"):
        with open("config.development.yaml") as f:
            config.update(yaml.safe_load(f))

    if os.getenv("NUM_WORKERS"):
        config["workers"] = int(os.getenv("NUM_WORKERS"))

    for key, value in os.environ.items():
        if key.startswith("APP_"):
            actual = key[4:].lower()

            if actual in ("port", "workers"):
                config[actual] = int(value)

            elif actual == "debug":
                config[actual] = value.lower() in (
                    "true",
                    "1",
                    "yes",
                    "on",
                )

            else:
                config[actual] = value

    for item in set:
        if "=" not in item:
            continue

        key, value = item.split("=", 1)

        if key == "port":
            config["port"] = int(value)

        elif key == "workers":
            config["workers"] = int(value)

        elif key == "debug":
            config["debug"] = value.strip().lower() in (
                "true",
                "1",
                "yes",
                "on",
            )

        else:
            config[key] = value

    config["port"] = int(config["port"])
    config["workers"] = int(config["workers"])

    if not isinstance(config["debug"], bool):
        config["debug"] = str(config["debug"]).lower() in (
            "true",
            "1",
            "yes",
            "on",
        )

    config["api_key"] = "****"

    return config


