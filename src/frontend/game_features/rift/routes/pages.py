"""Legacy node Rift routes have been retired; Hex test routes are separate."""

from fastapi import APIRouter

router = APIRouter(tags=["Rift-Retired"])
