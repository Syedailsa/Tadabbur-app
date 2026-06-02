#!/usr/bin/env python3
"""
Tadabbur — CI/CD Setup Verification Script
Run from project ROOT:  python check_setup.py
"""

import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))

PASS  = "  ✅"
FAIL  = "  ❌"
WARN  = "  ⚠️ "
INFO  = "  ℹ️ "

errors   = []
warnings = []

def ok(msg):     print(f"{PASS} {msg}")
def fail(msg):   print(f"{FAIL} {msg}"); errors.append(msg)
def warn(msg):   print(f"{WARN} {msg}"); warnings.append(msg)
def info(msg):   print(f"{INFO} {msg}")
def header(msg): print(f"\n{'═'*50}\n  {msg}\n{'═'*50}")

def file_exists(path, label=None):
    full = os.path.join(ROOT, path)
    label = label or path
    if os.path.isfile(full):
        ok(f"Found: {label}")
        return True
    else:
        fail(f"Missing: {label}  →  expected at: {path}")
        return False

def file_contains(path, substring, label):
    full = os.path.join(ROOT, path)
    if not os.path.isfile(full):
        return False
    content = open(full, encoding="utf-8", errors="ignore").read()
    if substring in content:
        ok(f"{label}")
        return True
    else:
        fail(f"{label}  →  '{substring}' not found in {path}")
        return False

def gitignore_covers(gitignore_path, pattern, label):
    full = os.path.join(ROOT, gitignore_path)
    if not os.path.isfile(full):
        warn(f"No .gitignore at {gitignore_path}")
        return
    content = open(full, encoding="utf-8", errors="ignore").read()
    if pattern in content:
        ok(f"{label} is gitignored")
    else:
        warn(f"{label} NOT in {gitignore_path}  →  add: {pattern}")

# ════════════════════════════════════════════════════════
header("1 — Required Files Exist")
# ════════════════════════════════════════════════════════
file_exists(".github/workflows/deploy.yml",  "GitHub Actions workflow")
file_exists("docker-compose.yml",            "docker-compose.yml (root)")
file_exists("nginx/nginx.conf",              "nginx/nginx.conf")
file_exists("backend/Dockerfile",            "backend/Dockerfile")
file_exists("frontend/Dockerfile",           "frontend/Dockerfile")
file_exists(".env.production.example",       ".env.production.example")

# ════════════════════════════════════════════════════════
header("2 — backend/Dockerfile Content")
# ════════════════════════════════════════════════════════
file_contains("backend/Dockerfile", "python:3.11-slim", "Uses python:3.11-slim base image")
file_contains("backend/Dockerfile", "AS builder",       "Builder stage defined")
file_contains("backend/Dockerfile", "AS runtime",       "Runtime stage defined")
file_contains("backend/Dockerfile", "HEALTHCHECK",      "HEALTHCHECK instruction present")
file_contains("backend/Dockerfile", "uvicorn",          "uvicorn CMD present")
file_contains("backend/Dockerfile", "appuser",          "Non-root user defined")

# ════════════════════════════════════════════════════════
header("3 — frontend/Dockerfile Content")
# ════════════════════════════════════════════════════════
file_contains("frontend/Dockerfile", "node:20-alpine", "Uses node:20-alpine base image")
file_contains("frontend/Dockerfile", "AS builder",     "Builder stage defined")
file_contains("frontend/Dockerfile", "standalone",     "Standalone output configured")
file_contains("frontend/Dockerfile", "HEALTHCHECK",    "HEALTHCHECK instruction present")
file_contains("frontend/Dockerfile", "server.js",      "node server.js CMD present")

# ════════════════════════════════════════════════════════
header("4 — frontend/next.config (.ts or .js)")
# ════════════════════════════════════════════════════════
next_config = None
for candidate in ["frontend/next.config.ts", "frontend/next.config.js"]:
    if os.path.isfile(os.path.join(ROOT, candidate)):
        next_config = candidate
        break

if next_config:
    ok(f"Found: {next_config}")
    file_contains(next_config, "standalone",
                  "output: 'standalone' present  ← REQUIRED for Docker")
else:
    fail("Missing: frontend/next.config.ts or next.config.js")

# ════════════════════════════════════════════════════════
header("5 — backend/main.py — Health Endpoint")
# ════════════════════════════════════════════════════════
found_main = None
for m in ["backend/main.py", "backend/app/main.py"]:
    if os.path.isfile(os.path.join(ROOT, m)):
        found_main = m
        break

if found_main:
    ok(f"Found main.py at: {found_main}")
    file_contains(found_main, "/health",
                  "/health endpoint present  ← REQUIRED for deploy health check")
else:
    warn("main.py not found — check manually")

# ════════════════════════════════════════════════════════
header("6 — docker-compose.yml Content")
# ════════════════════════════════════════════════════════
file_contains("docker-compose.yml", "tadabbur-backend",  "Backend image reference correct")
file_contains("docker-compose.yml", "tadabbur-frontend", "Frontend image reference correct")
file_contains("docker-compose.yml", "nginx",             "Nginx service present")
file_contains("docker-compose.yml", "qdrant",            "Qdrant service present")
file_contains("docker-compose.yml", "service_healthy",   "Health-based depends_on present")
file_contains("docker-compose.yml", ".env.production",   "env_file points to .env.production")
file_contains("docker-compose.yml", "tadabbur_net",      "Custom network defined")

# ════════════════════════════════════════════════════════
header("7 — nginx/nginx.conf Content")
# ════════════════════════════════════════════════════════
file_contains("nginx/nginx.conf", "backend.tadabbur.tech", "backend.tadabbur.tech configured")
file_contains("nginx/nginx.conf", "chat.tadabbur.tech",    "chat.tadabbur.tech configured")
file_contains("nginx/nginx.conf", "ssl_certificate",       "SSL certificate configured")
file_contains("nginx/nginx.conf", "upgrade",               "WebSocket upgrade support present")
file_contains("nginx/nginx.conf", "return 301 https",      "HTTP→HTTPS redirect present")

# ════════════════════════════════════════════════════════
header("8 — GitHub Actions Workflow")
# ════════════════════════════════════════════════════════
file_contains(".github/workflows/deploy.yml", "backend-ci",          "backend-ci job present")
file_contains(".github/workflows/deploy.yml", "frontend-ci",         "frontend-ci job present")
file_contains(".github/workflows/deploy.yml", "build-push",          "build-push job present")
file_contains(".github/workflows/deploy.yml", "deploy",              "deploy job present")
file_contains(".github/workflows/deploy.yml", "VPS_HOST",            "VPS_HOST secret referenced")
file_contains(".github/workflows/deploy.yml", "VPS_SSH_KEY",         "VPS_SSH_KEY secret referenced")
file_contains(".github/workflows/deploy.yml", "appleboy/ssh-action", "SSH deploy action present")
file_contains(".github/workflows/deploy.yml", "tadabbur.tech",       "Correct domain in workflow")
file_contains(".github/workflows/deploy.yml", "docker compose pull", "docker compose pull present")

# ════════════════════════════════════════════════════════
header("9 — .gitignore Checks")
# ════════════════════════════════════════════════════════
for gi in [".gitignore", "backend/.gitignore", "frontend/.gitignore"]:
    if os.path.isfile(os.path.join(ROOT, gi)):
        gitignore_covers(gi, ".env",            f".env  [{gi}]")
        gitignore_covers(gi, ".env.production", f".env.production  [{gi}]")

# ════════════════════════════════════════════════════════
header("10 — Security: No Real Secrets Committed")
# ════════════════════════════════════════════════════════
for f in [".env", ".env.production", "backend/.env", "frontend/.env"]:
    full = os.path.join(ROOT, f)
    if os.path.isfile(full):
        warn(f"{f} exists locally — make sure it's in .gitignore (do NOT commit)")
    else:
        ok(f"{f} not present in repo (good)")

if os.path.isfile(os.path.join(ROOT, ".env.production.example")):
    content = open(os.path.join(ROOT, ".env.production.example"), encoding="utf-8", errors="ignore").read()
    for hint in ["gsk_", "fw_", "AIza"]:
        if hint in content:
            warn(f".env.production.example has real key ('{hint}') — use placeholder only")
        else:
            ok(f"No real '{hint}' key in .env.production.example")

# ════════════════════════════════════════════════════════
header("11 — .env.production.example Variables")
# ════════════════════════════════════════════════════════
required_vars = [
    "GROQ_AI_API_KEY",
    "FIREWORKS_AI_API_KEY",
    "HUGGING_FACE_API",
    "QDRANT_API_KEY",
    "QDRANT_URL_ENDPOINT",
    "JWT_SECRET_KEY",
    "SUPABASE_URL",
    "SUPABASE_KEY",
    "WEB_GOOGLE_CLIENT_ID",
    "SMTP_HOST",
    "FRONTEND_URL",
    "DATABASE_URL",
]
if os.path.isfile(os.path.join(ROOT, ".env.production.example")):
    for var in required_vars:
        file_contains(".env.production.example", var, f"{var} present in template")

# frontend .env.example check
fe_env = "frontend/.env.example"
if os.path.isfile(os.path.join(ROOT, fe_env)):
    file_contains(fe_env, "NEXT_PUBLIC_BACKEND_URL", "NEXT_PUBLIC_BACKEND_URL in frontend/.env.example")
else:
    info("frontend/.env.example not found — optional but recommended")

# ════════════════════════════════════════════════════════
# FINAL REPORT
# ════════════════════════════════════════════════════════
print(f"\n{'═'*50}")
print(f"  RESULT")
print(f"{'═'*50}")
print(f"  Errors   : {len(errors)}")
print(f"  Warnings : {len(warnings)}")

if errors:
    print(f"\n  ❌ FIX THESE FIRST:")
    for i, e in enumerate(errors, 1):
        print(f"     {i}. {e}")

if warnings:
    print(f"\n  ⚠️  REVIEW THESE:")
    for i, w in enumerate(warnings, 1):
        print(f"     {i}. {w}")

if not errors:
    print(f"\n  🚀 All checks passed — ready for next step!")
    print(f"     Next: GitHub Secrets add karo")
else:
    print(f"\n  Fix errors above, phir dobara run karo")
    sys.exit(1)