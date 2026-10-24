import asyncio

import httpx

from echomind.api.main import app
from echomind.api.routes import BrowserAnalysisRequest, TextAnalysisRequest


def test_health_and_text_api():
    routes = {}
    for route in app.routes:
        nested = getattr(route, "original_router", None)
        candidates = nested.routes if nested is not None else [route]
        for candidate in candidates:
            if hasattr(candidate, "path") and hasattr(candidate, "endpoint"):
                routes[candidate.path] = candidate.endpoint
    assert routes["/health"]()["local_only"] is True
    response = routes["/analyze/text"](TextAnalysisRequest(text="Monday, no, Tuesday"))
    assert response["semantic_interpretation"]["self_correction"]["detected"] is True


def test_browser_dashboard_demo_returns_explainable_payload():
    routes = {route.path: route.endpoint for route in app.routes for route in getattr(getattr(route, "original_router", None), "routes", []) if hasattr(route, "path")}
    page = routes["/dashboard"]()
    payload = routes["/dashboard/analyze"](BrowserAnalysisRequest(demo_mode=True, scenario="multilingual"))
    assert page.status_code == 200
    assert b"EchoMind" in page.body
    assert b"/static/echomind-anime-engineer.png" in page.body
    assert payload["semantic_interpretation"]["code_switching"] == "mixed"
    assert "timeline_html" in payload


def test_dashboard_artwork_is_served_locally():
    async def get_artwork():
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            return await client.get("/static/echomind-anime-engineer.png")

    response = asyncio.run(get_artwork())

    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    assert response.content.startswith(b"\x89PNG\r\n\x1a\n")
