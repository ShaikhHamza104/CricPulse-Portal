import ipaddress
import logging
import time
import httpx
from django.conf import settings
from django.contrib import messages
from django.core.cache import cache
from django.http import JsonResponse
from django.shortcuts import render
from .player_names import humanize_player_name

logger = logging.getLogger(__name__)

# Rate limiter configuration for live query workbench proxy
_PROXY_RATE_LIMIT = 60
_PROXY_WINDOW = 60.0


def _get_client_ip(request) -> str:
    """
    Extract real client IP behind trusted reverse proxies (e.g. Render, Cloudflare).
    Render appends the genuine client IP to the end of the X-Forwarded-For chain.
    Reads NUM_PROXIES from settings (default 1), validates with ipaddress, and falls back to REMOTE_ADDR.
    """
    forwarded = request.headers.get("x-forwarded-for") or request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        parts = [p.strip() for p in forwarded.split(",") if p.strip()]
        num_proxies = getattr(settings, "NUM_PROXIES", 1)
        if parts:
            candidate = parts[-num_proxies] if len(parts) >= num_proxies else parts[-1]
            try:
                ipaddress.ip_address(candidate)
                return candidate
            except ValueError:
                pass

    remote_addr = request.META.get("REMOTE_ADDR", "127.0.0.1")
    try:
        ipaddress.ip_address(remote_addr)
        return remote_addr
    except ValueError:
        return "127.0.0.1"

# Standard IPL Franchise Aliases
IPL_TEAMS = [
    ("CSK", "Chennai Super Kings (CSK)"),
    ("MI", "Mumbai Indians (MI)"),
    ("RCB", "Royal Challengers Bengaluru (RCB)"),
    ("KKR", "Kolkata Knight Riders (KKR)"),
    ("SRH", "Sunrisers Hyderabad (SRH)"),
    ("DC", "Delhi Capitals (DC)"),
    ("RR", "Rajasthan Royals (RR)"),
    ("PBKS", "Punjab Kings (PBKS)"),
    ("GT", "Gujarat Titans (GT)"),
    ("LSG", "Lucknow Super Giants (LSG)"),
]

IPL_SEASONS = [str(y) for y in range(2024, 2007, -1)]


def get_engine_client(timeout: float = 6.0) -> httpx.Client:
    engine_url = getattr(
        settings, "CRICPULSE_ENGINE_URL", "https://cricpulse-engine.onrender.com"
    )
    return httpx.Client(base_url=engine_url, timeout=timeout)


def showcase_view(request):
    """
    Interactive Cricket Analytics Hub.
    Fetches real aggregate data from CricPulse-Engine backend with graceful fallback.
    """
    tab = request.GET.get("tab", "rivalry")
    engine_url = getattr(
        settings, "CRICPULSE_ENGINE_URL", "https://cricpulse-engine.onrender.com"
    )

    rivalry_data = None
    caps_data = {"orange": None, "purple": None}
    player_data = None
    error_message = None

    team1 = request.GET.get("team1", "CSK").upper()
    team2 = request.GET.get("team2", "MI").upper()
    season = request.GET.get("season", "2024")
    player_query = request.GET.get("player", "").strip()

    try:
        with get_engine_client() as client:
            if tab == "rivalry":
                if team1 and team2 and team1 != team2:
                    resp = client.get(
                        "/api/v1/analytics/head-to-head",
                        params={"team1": team1, "team2": team2},
                    )
                    if resp.status_code == 200:
                        rivalry_data = resp.json()
                    elif resp.status_code == 404:
                        error_message = f"No historical matches found between {team1} and {team2}."
                    else:
                        error_message = f"Engine returned status code {resp.status_code}."
                elif team1 == team2:
                    error_message = "Please select two different franchises for comparison."

            elif tab == "caps":
                # Fetch Orange Cap leaderboard
                orange_resp = client.get(
                    "/api/v1/analytics/orange-cap", params={"season": season}
                )
                if orange_resp.status_code == 200:
                    raw_orange = orange_resp.json()
                    orange_list = raw_orange if isinstance(raw_orange, list) else raw_orange.get("items", [])
                    for p in orange_list:
                        if isinstance(p, dict):
                            raw_pname = p.get("player_name") or p.get("name") or p.get("batsman") or "Unknown"
                            p["display_name"] = humanize_player_name(raw_pname)
                            p["display_runs"] = p.get("total_runs") or p.get("runs") or 0
                            p["display_balls"] = p.get("balls_faced") or p.get("balls") or 0
                            p["display_sr"] = p.get("strike_rate") or p.get("sr") or "0.0"
                    caps_data["orange"] = orange_list

                # Fetch Purple Cap leaderboard
                purple_resp = client.get(
                    "/api/v1/analytics/purple-cap", params={"season": season}
                )
                if purple_resp.status_code == 200:
                    raw_purple = purple_resp.json()
                    purple_list = raw_purple if isinstance(raw_purple, list) else raw_purple.get("items", [])
                    for b in purple_list:
                        if isinstance(b, dict):
                            raw_bname = b.get("player_name") or b.get("name") or b.get("bowler") or "Unknown"
                            b["display_name"] = humanize_player_name(raw_bname)
                            b["display_wickets"] = b.get("wickets") or b.get("total_wickets") or 0
                            b["display_overs"] = b.get("overs_bowled") if b.get("overs_bowled") is not None else (b.get("overs") or "0.0")
                            b["display_econ"] = b.get("economy_rate") if b.get("economy_rate") is not None else (b.get("economy") or b.get("econ") or "0.0")
                    caps_data["purple"] = purple_list

            elif tab == "player" and player_query:
                # 1. Search player by name
                search_resp = client.get(
                    "/api/v1/players", params={"search": player_query, "limit": 5}
                )
                if search_resp.status_code == 200:
                    results = search_resp.json()
                    items = results.get("items", results) if isinstance(results, dict) else results
                    if items and len(items) > 0:
                        first_player = items[0]
                        player_id = first_player.get("id") or first_player.get("player_id")
                        if player_id:
                            profile_resp = client.get(f"/api/v1/players/{player_id}")
                            if profile_resp.status_code == 200:
                                player_data = profile_resp.json()
                            else:
                                player_data = first_player
                        else:
                            player_data = first_player

                        if isinstance(player_data, dict):
                            raw_name = player_data.get("name") or player_data.get("player_name") or player_query
                            player_data["display_name"] = humanize_player_name(raw_name)
                            player_data["display_id"] = player_data.get("id") or player_data.get("player_id") or "N/A"
                            player_data["display_runs"] = player_data.get("total_runs") or player_data.get("runs") or 0
                            player_data["display_sr"] = player_data.get("strike_rate") or player_data.get("sr") or "N/A"
                            player_data["display_wickets"] = player_data.get("wickets") or player_data.get("total_wickets") or 0
                            player_data["display_econ"] = player_data.get("economy_rate") or player_data.get("economy") or player_data.get("econ") or "N/A"
                    else:
                        error_message = f"No cricketer found matching '{player_query}'."

    except httpx.ConnectError:
        error_message = (
            "Cannot connect to the CricPulse Engine. The backend cloud instance might be starting up (takes ~30s on initial cold start)."
        )
    except httpx.TimeoutException:
        error_message = (
            "Request to CricPulse Engine timed out. The free backend server is waking up—please refresh in a few seconds."
        )
    except Exception as exc:
        logger.error(f"Error communicating with CricPulse engine: {exc}")
        error_message = f"Analytics service notice: {str(exc)}"

    context = {
        "tab": tab,
        "ipl_teams": IPL_TEAMS,
        "ipl_seasons": IPL_SEASONS,
        "team1": team1,
        "team2": team2,
        "season": season,
        "player_query": player_query,
        "rivalry_data": rivalry_data,
        "caps_data": caps_data,
        "player_data": player_data,
        "error_message": error_message,
        "engine_url": engine_url,
    }
    return render(request, "analytics/showcase.html", context)


def live_query_proxy(request):
    """
    Unbounded JSON proxy workbench for the interactive API playground.
    Forwards developer requests to CricPulse-Engine with custom parameters,
    captures response headers, execution latency, status codes, and payload.
    Defends against SSRF, directory traversal, and rate exhaustion.
    """
    client_ip = _get_client_ip(request)
    now = time.time()

    # Cache-backed sliding-window rate limit check
    cache_key = f"rate_limit:proxy:{client_ip}"
    timestamps = cache.get(cache_key) or []
    timestamps = [t for t in timestamps if now - t < _PROXY_WINDOW]

    if len(timestamps) >= _PROXY_RATE_LIMIT:
        retry_after = int(_PROXY_WINDOW - (now - timestamps[0]))
        return JsonResponse(
            {
                "status_code": 429,
                "status_text": "Too Many Requests",
                "error": f"Workbench rate limit exceeded ({_PROXY_RATE_LIMIT} req/min). Try again in {max(1, retry_after)} seconds.",
            },
            status=429,
            headers={"Retry-After": str(max(1, retry_after))},
        )

    timestamps.append(now)
    cache.set(cache_key, timestamps, timeout=int(_PROXY_WINDOW) + 5)

    endpoint = request.GET.get("endpoint", "/health").strip()

    # Re-append extra query parameters if '&' was not percent-encoded by the client
    extra_params = {k: v for k, v in request.GET.items() if k != "endpoint"}
    if extra_params:
        separator = "&" if "?" in endpoint else "?"
        from urllib.parse import urlencode
        endpoint = f"{endpoint}{separator}{urlencode(extra_params)}"

    # SSRF & Path Traversal Defensive Validation:
    # Strictly prohibit protocols, authority redirects, directory traversals, or userinfo
    if (
        "://" in endpoint
        or endpoint.startswith("//")
        or endpoint.startswith("\\\\")
        or ".." in endpoint
        or "@" in endpoint
    ):
        return JsonResponse(
            {
                "status_code": 400,
                "status_text": "Bad Request",
                "error": "Invalid endpoint target. Protocols, backslashes, and path traversals are strictly prohibited.",
            },
            status=400,
        )

    if not endpoint.startswith("/"):
        endpoint = f"/{endpoint}"

    # Whitelist valid API engine route prefixes
    allowed_prefixes = ("/api/v1/", "/health", "/db-health")
    if not any(endpoint.startswith(p) for p in allowed_prefixes):
        return JsonResponse(
            {
                "status_code": 403,
                "status_text": "Forbidden",
                "error": "Access denied. Only CricPulse Engine endpoints (/api/v1/*, /health, /db-health) are allowed.",
            },
            status=403,
        )

    engine_url = getattr(
        settings, "CRICPULSE_ENGINE_URL", "https://cricpulse-engine.onrender.com"
    )

    # Resolve API Key from request header or authenticated user's active key
    api_key = request.headers.get("X-API-Key")
    if not api_key and request.user.is_authenticated:
        active_key_obj = request.user.api_keys.filter(is_active=True).first()
        if active_key_obj:
            api_key = active_key_obj.key

    headers = {
        "User-Agent": "CricPulse-Portal-Workbench/1.0",
        "Accept": "application/json",
    }
    if api_key:
        headers["X-API-Key"] = api_key

    target_url = f"{engine_url}{endpoint}"

    try:
        with httpx.Client(timeout=10.0) as client:
            resp = client.get(target_url, headers=headers)
            process_time = resp.headers.get("X-Process-Time", "N/A")
            request_id = resp.headers.get("X-Request-ID", "N/A")

            try:
                data = resp.json()
            except Exception:
                data = {"raw_text": resp.text}

            captured_headers = {
                "x-process-time": process_time,
                "x-request-id": request_id,
                "content-type": resp.headers.get("Content-Type", "application/json"),
                "content-length": str(len(resp.content)),
                "x-frame-options": resp.headers.get("X-Frame-Options", "DENY"),
                "x-content-type-options": resp.headers.get("X-Content-Type-Options", "nosniff"),
            }

            return JsonResponse(
                {
                    "status_code": resp.status_code,
                    "status_text": "OK" if resp.status_code == 200 else f"HTTP {resp.status_code}",
                    "process_time": process_time,
                    "request_id": request_id,
                    "target_url": target_url,
                    "size_bytes": len(resp.content),
                    "headers": captured_headers,
                    "data": data,
                },
                status=resp.status_code,
            )
    except httpx.ConnectError:
        return JsonResponse(
            {
                "status_code": 503,
                "status_text": "Connection Failed",
                "process_time": "Error",
                "target_url": target_url,
                "error": "Could not connect to CricPulse Engine. Backend cloud container is waking up.",
            },
            status=503,
        )
    except httpx.TimeoutException:
        return JsonResponse(
            {
                "status_code": 504,
                "status_text": "Gateway Timeout",
                "process_time": "> 10s",
                "target_url": target_url,
                "error": "Engine request timed out (>10s). Container is spinning up from cold sleep.",
            },
            status=504,
        )
    except Exception as exc:
        return JsonResponse(
            {
                "status_code": 500,
                "status_text": "Workbench Error",
                "process_time": "Error",
                "target_url": target_url,
                "error": f"Failed to execute query: {str(exc)}",
            },
            status=500,
        )
