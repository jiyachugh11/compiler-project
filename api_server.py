"""
Unified API layer for HashSense.

Wraps Backend 1 (CompilerPipeline) and Backend 2 (HashAnalysisPipeline)
behind a single HTTP endpoint, since neither backend exposes one on its
own -- both are plain Python classes that pass objects in memory. This is
the glue neither backend dev owns per the team split, so it lives here.

Install:
    pip install fastapi uvicorn --break-system-packages

Run:
    uvicorn api_server:app --reload --port 8000

Endpoint:
    POST /api/analyze
    Body:     {"source_code": "int x = 1;"}
    Response: {
        "workload": { ...Backend 1 AnalysisResult, JSON-safe... },
        "hash_analysis": { ...Backend 2 HashAnalysisReport, JSON-safe... }
    }

Field names are kept exactly as each backend defines them (snake_case),
not the camelCase from the early contract draft. Frontends should build
against the real names below, not the draft ones.
"""
from dataclasses import asdict
from typing import Dict

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from compiler import CompilerPipeline
from compiler.lexer.lexer import LexerError
from hashing import HashAnalysisPipeline


app = FastAPI(title="HashSense API", version="0.1.0")

# No auth, no DB -- matches the agreed scope (this is a local dev/demo
# tool, not a public multi-tenant service). CORS wide open so the React
# dev server (localhost:3000/5173/etc.) can call it without extra config.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pipelines are stateless per .run() call (each call constructs its own
# fresh Lexer/SymbolTable/StringPool internally -- see CompilerPipeline.run),
# so one shared instance per process is safe.
compiler_pipeline = CompilerPipeline()
hash_pipeline = HashAnalysisPipeline()


class AnalyzeRequest(BaseModel):
    source_code: str


def _serialize_symbol(sym) -> Dict:
    return {
        "name": sym.name,
        "scope_id": sym.scope_id,
        "scope_depth": sym.scope_depth,
        "location": {"line": sym.location.line, "column": sym.location.column},
        "data_type": sym.data_type,
        "role": sym.role.name,
        "intern_id": sym.intern_id,
    }


def _serialize_scope(scope) -> Dict:
    return {
        "scope_id": scope.scope_id,
        "parent_id": scope.parent_id,
        "depth": scope.depth,
        "scope_type": scope.scope_type.name,
        "symbol_names": scope.symbol_names,
        "child_scope_ids": scope.child_scope_ids,
    }


def _serialize_workload(analysis) -> Dict:
    """Backend 1's AnalysisResult -> plain JSON-safe dict for Frontend 1."""
    return {
        "identifier_stream": analysis.identifier_stream,
        "interned_identifiers": analysis.interned_identifiers,
        "symbols": [_serialize_symbol(s) for s in analysis.symbol_table.symbols],
        "scopes": {sid: _serialize_scope(s) for sid, s in analysis.scopes.items()},
        "workload_metrics": asdict(analysis.workload_metrics),
        "source_code": analysis.source_code,
    }


@app.post("/api/analyze")
def analyze(req: AnalyzeRequest):
    """Run the full pipeline: source code -> Backend 1 -> Backend 2 -> JSON.

    Frontend 1 should read response["workload"].
    Frontend 2 should read response["hash_analysis"] (matches the
    HashAnalysisReport shape Backend 2 already produces, unchanged).
    """
    if not req.source_code.strip():
        raise HTTPException(status_code=400, detail="source_code is empty")

    try:
        analysis = compiler_pipeline.run(req.source_code)
    except LexerError as e:
        # Surface lexer errors (unterminated string/comment) as a 422 with
        # the exact source location, so Frontend 1 can point at the line.
        raise HTTPException(
            status_code=422,
            detail={
                "message": e.message,
                "location": {"line": e.location.line, "column": e.location.column},
            },
        )

    hash_report = hash_pipeline.run(analysis)

    return {
        "workload": _serialize_workload(analysis),
        "hash_analysis": asdict(hash_report),
    }


@app.get("/api/health")
def health():
    return {"status": "ok"}
