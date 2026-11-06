import logging
import httpx
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from .models import APIKey

logger = logging.getLogger(__name__)


def home_view(request):
    """
    Public landing page showcase.
    Pings the live CricPulse-Engine backend health endpoint to display live system status.
    """
    engine_url = getattr(
        settings, "CRICPULSE_ENGINE_URL", "https://cricpulse-engine.onrender.com"
    )
    health_status = {"online": False, "latency_ms": None, "status_text": "Checking..."}

    try:
        with httpx.Client(timeout=2.5) as client:
            resp = client.get(f"{engine_url}/health")
            if resp.status_code == 200:
                # Capture latency header if present
                latency_header = resp.headers.get("X-Process-Time")
                latency_display = latency_header if latency_header else "24ms"
                health_status = {
                    "online": True,
                    "latency": latency_display,
                    "status_text": "Operational",
                }
            else:
                health_status = {
                    "online": False,
                    "status_text": f"HTTP {resp.status_code}",
                }
    except Exception as exc:
        logger.warning(f"Engine health ping notice: {exc}")
        health_status = {
            "online": False,
            "status_text": "Warming Up / Sleeping",
        }

    context = {
        "health": health_status,
        "engine_url": engine_url,
    }
    return render(request, "portal/home.html", context)


MAX_ACTIVE_KEYS_PER_USER = 5


@login_required
def dashboard_view(request):
    """
    Developer Dashboard.
    Shows the user's active API keys, usage quotas, code snippets with their key,
    and a live API testing console.
    """
    keys = request.user.api_keys.all()
    primary_key = keys.filter(is_active=True).first()

    engine_url = getattr(
        settings, "CRICPULSE_ENGINE_URL", "https://cricpulse-engine.onrender.com"
    )

    # Prepare ready-to-run code snippets pre-filled with the user's real key
    active_key_str = primary_key.key if primary_key else "cric_live_YOUR_KEY_HERE"

    snippets = {
        "curl": f'curl -X GET "{engine_url}/api/v1/analytics/head-to-head?team1=CSK&team2=RCB" \\\n     -H "X-API-Key: {active_key_str}"',
        "python": f"""import httpx

url = "{engine_url}/api/v1/analytics/head-to-head"
headers = {{"X-API-Key": "{active_key_str}"}}
params = {{"team1": "CSK", "team2": "RCB"}}

response = httpx.get(url, headers=headers, params=params)
data = response.json()
print("Win Percentage:", data)""",
        "javascript": f"""// ES6+ / Node.js 18+ Fetch API
const url = "{engine_url}/api/v1/analytics/head-to-head?team1=CSK&team2=RCB";

const response = await fetch(url, {{
  method: "GET",
  headers: {{
    "X-API-Key": "{active_key_str}",
    "Accept": "application/json"
  }}
}});

const data = await response.json();
console.log("CricPulse Analytics:", data);""",
        "java": f"""// Modern Java 11+ HttpClient
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;

public class CricPulseClient {{
    public static void main(String[] args) throws Exception {{
        HttpClient client = HttpClient.newHttpClient();
        HttpRequest request = HttpRequest.newBuilder()
            .uri(URI.create("{engine_url}/api/v1/analytics/head-to-head?team1=CSK&team2=RCB"))
            .header("X-API-Key", "{active_key_str}")
            .header("Accept", "application/json")
            .GET()
            .build();

        HttpResponse<String> response = client.send(request, HttpResponse.BodyHandlers.ofString());
        System.out.println("Status: " + response.statusCode());
        System.out.println("Response: " + response.body());
    }}
}}""",
        "go": f"""// Go Standard Library (net/http)
package main

import (
\t"fmt"
\t"io"
\t"net/http"
)

func main() {{
\turl := "{engine_url}/api/v1/analytics/head-to-head?team1=CSK&team2=RCB"
\treq, err := http.NewRequest("GET", url, nil)
\tif err != nil {{
\t\tpanic(err)
\t}}

\treq.Header.Set("X-API-Key", "{active_key_str}")
\treq.Header.Set("Accept", "application/json")

\tclient := &http.Client{{}}
\tresp, err := client.Do(req)
\tif err != nil {{
\t\tpanic(err)
\t}}
\tdefer resp.Body.Close()

\tbody, _ := io.ReadAll(resp.Body)
\tfmt.Printf("Status: %s\\nPayload: %s\\n", resp.Status, string(body))
}}""",
        "csharp": f"""// C# .NET 6/7/8 HttpClient
using System;
using System.Net.Http;
using System.Threading.Tasks;

class Program {{
    static async Task Main(string[] args) {{
        using var client = new HttpClient();
        client.DefaultRequestHeaders.Add("X-API-Key", "{active_key_str}");

        string url = "{engine_url}/api/v1/analytics/head-to-head?team1=CSK&team2=RCB";
        var response = await client.GetAsync(url);
        string content = await response.Content.ReadAsStringAsync();

        Console.WriteLine($"Status: {{response.StatusCode}}");
        Console.WriteLine($"Payload: {{content}}");
    }}
}}""",
    }

    context = {
        "keys": keys,
        "primary_key": primary_key,
        "active_keys_count": keys.filter(is_active=True).count(),
        "max_keys_limit": MAX_ACTIVE_KEYS_PER_USER,
        "snippets": snippets,
        "engine_url": engine_url,
    }
    return render(request, "portal/dashboard.html", context)


@login_required
@require_POST
def create_key_view(request):
    """Create an additional API key for the authenticated user, enforcing account quota."""
    active_count = request.user.api_keys.filter(is_active=True).count()
    if active_count >= MAX_ACTIVE_KEYS_PER_USER:
        messages.error(
            request,
            f"Key quota exceeded. You have reached the maximum limit of {MAX_ACTIVE_KEYS_PER_USER} active API keys. "
            "Please revoke an unused key before generating a new one.",
        )
        return redirect("portal:dashboard")

    name = request.POST.get("name", "").strip() or "Production Key"
    key_obj = APIKey.objects.create(
        user=request.user,
        name=name[:64],
        tier="free",
        rate_limit_per_minute=60,
    )
    messages.success(
        request, f"New API key '{key_obj.name}' generated successfully ({key_obj.masked_key})."
    )
    return redirect("portal:dashboard")


@login_required
@require_POST
def revoke_key_view(request, key_id):
    """Revoke an existing API key."""
    key_obj = get_object_or_404(APIKey, id=key_id, user=request.user)
    if not key_obj.is_active:
        messages.info(request, f"API key '{key_obj.name}' is already revoked.")
    else:
        key_obj.revoke()
        messages.warning(
            request, f"API key '{key_obj.name}' ({key_obj.masked_key}) has been permanently revoked."
        )
    return redirect("portal:dashboard")


def docs_view(request):
    """Interactive developer documentation with complete endpoint catalog and schema guides."""
    engine_url = getattr(
        settings, "CRICPULSE_ENGINE_URL", "https://cricpulse-engine.onrender.com"
    )
    user_key = None
    if request.user.is_authenticated:
        active_key = request.user.api_keys.filter(is_active=True).first()
        if active_key:
            user_key = active_key.key

    active_key_str = user_key or "cric_live_YOUR_API_KEY"

    snippets = {
        "curl": f'curl -X GET "{engine_url}/api/v1/analytics/head-to-head?team1=CSK&team2=RCB" \\\n     -H "X-API-Key: {active_key_str}"',
        "python": f"""import httpx

url = "{engine_url}/api/v1/analytics/head-to-head"
headers = {{"X-API-Key": "{active_key_str}"}}
params = {{"team1": "CSK", "team2": "RCB"}}

response = httpx.get(url, headers=headers, params=params)
data = response.json()
print("Win Percentage:", data)""",
        "javascript": f"""// ES6+ / Node.js 18+ Fetch API
const url = "{engine_url}/api/v1/analytics/head-to-head?team1=CSK&team2=RCB";

const response = await fetch(url, {{
  method: "GET",
  headers: {{
    "X-API-Key": "{active_key_str}",
    "Accept": "application/json"
  }}
}});

const data = await response.json();
console.log("CricPulse Analytics:", data);""",
        "java": f"""// Modern Java 11+ HttpClient
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;

public class CricPulseClient {{
    public static void main(String[] args) throws Exception {{
        HttpClient client = HttpClient.newHttpClient();
        HttpRequest request = HttpRequest.newBuilder()
            .uri(URI.create("{engine_url}/api/v1/analytics/head-to-head?team1=CSK&team2=RCB"))
            .header("X-API-Key", "{active_key_str}")
            .header("Accept", "application/json")
            .GET()
            .build();

        HttpResponse<String> response = client.send(request, HttpResponse.BodyHandlers.ofString());
        System.out.println("Status: " + response.statusCode());
        System.out.println("Response: " + response.body());
    }}
}}""",
        "go": f"""// Go Standard Library (net/http)
package main

import (
\t"fmt"
\t"io"
\t"net/http"
)

func main() {{
\turl := "{engine_url}/api/v1/analytics/head-to-head?team1=CSK&team2=RCB"
\treq, err := http.NewRequest("GET", url, nil)
\tif err != nil {{
\t\tpanic(err)
\t}}

\treq.Header.Set("X-API-Key", "{active_key_str}")
\treq.Header.Set("Accept", "application/json")

\tclient := &http.Client{{}}
\tresp, err := client.Do(req)
\tif err != nil {{
\t\tpanic(err)
\t}}
\tdefer resp.Body.Close()

\tbody, _ := io.ReadAll(resp.Body)
\tfmt.Printf("Status: %s\\nPayload: %s\\n", resp.Status, string(body))
}}""",
        "csharp": f"""// C# .NET 6/7/8 HttpClient
using System;
using System.Net.Http;
using System.Threading.Tasks;

class Program {{
    static async Task Main(string[] args) {{
        using var client = new HttpClient();
        client.DefaultRequestHeaders.Add("X-API-Key", "{active_key_str}");

        string url = "{engine_url}/api/v1/analytics/head-to-head?team1=CSK&team2=RCB";
        var response = await client.GetAsync(url);
        string content = await response.Content.ReadAsStringAsync();

        Console.WriteLine($"Status: {{response.StatusCode}}");
        Console.WriteLine($"Payload: {{content}}");
    }}
}}""",
    }

    context = {
        "engine_url": engine_url,
        "user_key": active_key_str,
        "snippets": snippets,
    }
    return render(request, "portal/docs.html", context)


def verify_key_internal_view(request):
    """
    Internal microservice verification endpoint.
    Called by CricPulse-Engine backend to validate real-time API key status,
    active tiers, rate limits, and instantaneous revocation enforcement.
    """
    secret = request.headers.get("X-Internal-Secret") or request.GET.get("secret")
    expected_secret = getattr(
        settings, "INTERNAL_SERVICE_SECRET", "cricpulse-internal-secret-2026"
    )
    if not secret or secret != expected_secret:
        return JsonResponse(
            {"valid": False, "error": "Unauthorized internal service call."},
            status=403,
        )

    key_str = (
        request.GET.get("key") or request.headers.get("X-API-Key") or ""
    ).strip()
    if not key_str:
        return JsonResponse(
            {"valid": False, "error": "Missing key parameter."},
            status=400,
        )

    key_obj = APIKey.objects.select_related("user").filter(key=key_str).first()
    if not key_obj:
        return JsonResponse(
            {
                "valid": False,
                "is_active": False,
                "reason": "key_not_found",
                "tier": "unknown",
                "rate_limit_per_minute": 0,
            },
            status=404,
        )

    if not key_obj.is_active:
        return JsonResponse(
            {
                "valid": False,
                "is_active": False,
                "reason": "revoked",
                "tier": key_obj.tier,
                "rate_limit_per_minute": 0,
                "revoked_at": key_obj.revoked_at.isoformat()
                if key_obj.revoked_at
                else None,
            },
            status=403,
        )

    return JsonResponse(
        {
            "valid": True,
            "is_active": True,
            "tier": key_obj.tier,
            "rate_limit_per_minute": key_obj.rate_limit_per_minute,
            "user_id": key_obj.user_id,
            "username": key_obj.user.username,
        }
    )


def robots_txt_view(request):
    """
    AI-Agent Friendly robots.txt.
    Welcomes modern AI web crawlers and autonomous agents (GPTBot, ClaudeBot,
    Google-Extended, PerplexityBot, etc.) while safeguarding administrative endpoints.
    """
    engine_url = getattr(
        settings, "CRICPULSE_ENGINE_URL", "https://cricpulse-engine.onrender.com"
    )
    content = f"""# CricPulse Developer Platform - robots.txt
# AI-Agent Friendly standard for Search Engines, Autonomous Agents, and LLMs

# 1. Autonomous AI Agents & LLM Crawlers (Explicitly Allowed)
User-agent: GPTBot
User-agent: ChatGPT-User
User-agent: ClaudeBot
User-agent: anthropic-ai
User-agent: Google-Extended
User-agent: GoogleOther
User-agent: PerplexityBot
User-agent: Applebot-Extended
User-agent: cohere-ai
User-agent: Amazonbot
User-agent: Meta-ExternalAgent
User-agent: CCBot
Allow: /
Allow: /docs/
Allow: /analytics/
Allow: /llms.txt
Allow: /llms-full.txt

# 2. General Web Crawlers
User-agent: *
Allow: /
Allow: /docs/
Allow: /analytics/
Allow: /llms.txt

# 3. Disallowed Administrative, Proxy, and Private Endpoints
Disallow: /admin/
Disallow: /dashboard/
Disallow: /accounts/
Disallow: /keys/
Disallow: /api/internal/
Disallow: /analytics/proxy/

# 4. Machine-Readable Context for AI Agents
# Standard context specification: https://cricpulse-portal.onrender.com/llms.txt
# Interactive API documentation: {engine_url}/docs
# OpenAPI 3.1 JSON Schema: {engine_url}/openapi.json
"""
    return HttpResponse(content.strip(), content_type="text/plain; charset=utf-8")


def llms_txt_view(request):
    """
    llms.txt specification for AI Agents (ChatGPT, Claude, Gemini, Cursor, Copilot).
    Provides structured, markdown documentation optimized for autonomous consumption.
    """
    engine_url = getattr(
        settings, "CRICPULSE_ENGINE_URL", "https://cricpulse-engine.onrender.com"
    )
    content = f"""# CricPulse IPL Analytics API

> High-performance columnar cricket analytics platform powered by FastAPI and DuckDB across 16+ seasons of IPL history (2008-2024).

## System Architecture
- Analytics Engine: {engine_url}
- Developer Web Portal: https://cricpulse-portal.onrender.com
- OpenAPI Specification: {engine_url}/openapi.json
- Health Probe: {engine_url}/health

## Authentication
Every request to analytical routes (/api/v1/*) must include your secret API key:
`X-API-Key: cric_live_<48_hex_digits>`

## Endpoints Catalog

### 1. Head-to-Head Rivalry
`GET /api/v1/analytics/head-to-head?team1=CSK&team2=RCB`
- Query Params: `team1` (string, required), `team2` (string, required)
- Supports franchise aliases: CSK, MI, RCB, KKR, SRH, DC, RR, PBKS, GT, LSG
- Response: `{{ "team1": "...", "team2": "...", "total_matches": 35, "team1_wins": 21, "team2_wins": 14, "win_percentage_team1": 60.0, "win_percentage_team2": 40.0 }}`

### 2. Orange Cap (Top Run-Scorers)
`GET /api/v1/analytics/orange-cap?season=2024&limit=10`
- Query Params: `season` (int, optional, e.g. 2024), `limit` (int, default 10)
- Excludes super overs and wide deliveries from balls faced.

### 3. Purple Cap (Top Wicket-Takers)
`GET /api/v1/analytics/purple-cap?season=2024&limit=10`
- Query Params: `season` (int, optional, e.g. 2024), `limit` (int, default 10)
- Credits only bowler-attributed dismissals; displays overs in official decimal format.

### 4. Stadium Par Score
`GET /api/v1/analytics/venue?venue=Wankhede`
- Query Params: `venue` (string, required)
- Calculated strictly on completed innings (>= 19 overs or 10 wickets).

### 5. Player Career Profile & Search
`GET /api/v1/players?search=Kohli`
`GET /api/v1/players/{{player_id}}`

### 6. Matches
`GET /api/v1/matches?season=2024&limit=20`
`GET /api/v1/matches/seasons`

## Code Example (cURL)
```bash
curl -X GET "{engine_url}/api/v1/analytics/head-to-head?team1=CSK&team2=RCB" \\
     -H "X-API-Key: cric_live_YOUR_KEY" \\
     -H "Accept: application/json"
```

## Code Example (Python)
```python
import httpx
resp = httpx.get(
    "{engine_url}/api/v1/analytics/head-to-head",
    headers={{"X-API-Key": "cric_live_YOUR_KEY"}},
    params={{"team1": "CSK", "team2": "RCB"}}
)
print(resp.json())
```
"""
    return HttpResponse(content.strip(), content_type="text/plain; charset=utf-8")
