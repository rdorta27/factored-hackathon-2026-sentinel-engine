"""
Compatibility aliases: /auth/login, /auth/logout, /auth/me
           and:       /api/v1/auth/login, /api/v1/auth/logout, /api/v1/auth/me

The sentinel-login frontend calls POST /auth/login. These thin routers mount
the same session handler functions at the /auth prefix (and at /api/v1/auth)
so the sentinel-login app.js works against sentinel-ai-core without any UI
changes.  All business logic remains in app/session/router.py.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.session.router import login, logout, me

# /auth/... — primary alias used by sentinel-login's app.js
auth_router = APIRouter(prefix="/auth", tags=["auth (compatibility)"])
auth_router.add_api_route("/login", login, methods=["POST"])
auth_router.add_api_route("/logout", logout, methods=["POST"])
auth_router.add_api_route("/me", me, methods=["GET"])

# /api/v1/auth/... — versioned alias requested by the integration spec
api_v1_auth_router = APIRouter(prefix="/api/v1/auth", tags=["auth (v1 compatibility)"])
api_v1_auth_router.add_api_route("/login", login, methods=["POST"])
api_v1_auth_router.add_api_route("/logout", logout, methods=["POST"])
api_v1_auth_router.add_api_route("/me", me, methods=["GET"])
