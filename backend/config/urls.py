"""
URL configuration for Provote project.
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import HttpResponse
from django.shortcuts import redirect
from django.urls import include, path
from string import Template

# Prometheus metrics (optional)
try:
    import django_prometheus

    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)
from rest_framework.decorators import api_view, permission_classes, renderer_classes
from rest_framework.permissions import AllowAny
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response


@api_view(["GET"])
@permission_classes([AllowAny])
@renderer_classes(
    [JSONRenderer]
)  # Only use JSONRenderer to avoid BrowsableAPIRenderer template issues
def health_check(request):
    """Health check endpoint for Docker and load balancers."""
    from django.core.cache import cache
    from django.db import connection

    # Check database connectivity
    db_status = "healthy"
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
    except Exception:
        db_status = "unhealthy"

    # Check cache connectivity
    cache_status = "healthy"
    try:
        cache.set("health_check", "ok", 1)
        cache.get("health_check")
    except Exception:
        cache_status = "unhealthy"

    overall_status = "healthy" if db_status == "healthy" else "unhealthy"
    status_code = 200 if overall_status == "healthy" else 503

    data = {{
        "status": overall_status,
        "checks": {{
            "database": db_status,
            "cache": cache_status,
        }},
        "version": "1.0.0",
    }}

    return Response(data, status=status_code)


@api_view(["GET"])
@permission_classes([AllowAny])
@renderer_classes(
    [JSONRenderer]
)  # Only use JSONRenderer to avoid BrowsableAPIRenderer template issues
def api_root(request):
    """API root endpoint that lists available endpoints."""
    data = {{
        "message": "Welcome to Provote API",
        "version": "1.0.0",
        "documentation": {{
            "swagger_ui": "/api/docs/",
            "redoc": "/api/redoc/",
            "schema": "/api/schema/",
            "schema_viewer": "/api/schema/view/",
        }},
        "endpoints": {{
            "polls": "/api/v1/polls/",
            "votes": "/api/v1/votes/",
            "users": "/api/v1/users/",
            "analytics": "/api/v1/analytics/",
            "notifications": "/api/v1/notifications/",
            "categories": "/api/v1/categories/",
            "tags": "/api/v1/tags/",
        }},
        "info": "For detailed API documentation, visit /api/docs/ or /api/redoc/",
    }}

    return Response(data)


def schema_viewer(request):
    """Display schema in browser-friendly format with links to interactive docs."""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Provote API - Schema</title>
        <style>
            body {{ font-family: Arial, sans-serif; max-width: 1200px; margin: 50px auto; padding: 20px; }}
            .header {{ background: #f5f5f5; padding: 20px; border-radius: 5px; margin-bottom: 20px; }}
            .links {{ margin: 20px 0; }}
            .links a {{ display: inline-block; margin-right: 15px; padding: 10px 20px;
                       background: #007bff; color: white; text-decoration: none; border-radius: 3px; }}
            .links a:hover {{ background: #0056b3; }}
            .info {{ background: #e7f3ff; padding: 15px; border-left: 4px solid #007bff; margin: 20px 0; }}
            .download-links {{ margin-top: 20px; }}
            .download-links a {{ color: #007bff; text-decoration: none; margin-right: 15px; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>Provote API Documentation</h1>
            <p>OpenAPI 3.0 Schema</p>
        </div>

        <div class="info">
            <strong>📖 Interactive Documentation:</strong> Use the links below to explore and test the API interactively.
        </div>

        <div class="links">
            <a href="/api/docs/" target="_blank">📘 Swagger UI (Interactive Explorer)</a>
            <a href="/api/redoc/" target="_blank">📕 ReDoc (Alternative Documentation)</a>
        </div>

        <div class="download-links">
            <h3>Download Schema Files:</h3>
            <a href="/api/schema/?format=json" download="schema.json">📄 Download JSON Schema</a>
            <a href="/api/schema/?format=yaml" download="schema.yaml">📄 Download YAML Schema</a>
        </div>

        <div style="margin-top: 30px;">
            <h3>About the Schema Endpoints:</h3>
            <p>The schema endpoints return raw OpenAPI specification files (JSON/YAML) which are designed for:</p>
            <ul>
                <li>API client code generation</li>
                <li>Importing into API testing tools (Postman, Insomnia, etc.)</li>
                <li>Integration with CI/CD pipelines</li>
                <li>Programmatic API consumption</li>
            </ul>
            <p><strong>For interactive exploration and testing, use Swagger UI or ReDoc above.</strong></p>
        </div>
    </body>
    </html>
    """
    return HttpResponse(html_content, content_type="text/html")


def root_view(request):
    """Root view that shows a welcome page with links to documentation."""
    # Build absolute URLs
    base_url = request.build_absolute_uri("/").rstrip("/")
    api_docs_url = request.build_absolute_uri("/api/docs/")
    api_redoc_url = request.build_absolute_uri("/api/redoc/")
    api_root_url = request.build_absolute_uri("/api/v1/")
    api_schema_url = request.build_absolute_uri("/api/schema/")
    auth_token_url = request.build_absolute_uri("/api/v1/auth/token/")
    polls_url = request.build_absolute_uri("/api/v1/polls/")
    votes_url = request.build_absolute_uri("/api/v1/votes/")
    users_url = request.build_absolute_uri("/api/v1/users/")
    analytics_url = request.build_absolute_uri("/api/v1/analytics/")
    notifications_url = request.build_absolute_uri("/api/v1/notifications/")
    
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Provote API - Welcome</title>
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                padding: 20px;
            }}
            .container {{
                background: white;
                border-radius: 12px;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                max-width: 800px;
                width: 100%;
                padding: 40px;
            }}
            h1 {{
                color: #333;
                margin-bottom: 10px;
                font-size: 2.5em;
            }}
            .subtitle {{
                color: #666;
                margin-bottom: 30px;
                font-size: 1.1em;
            }}
            .section {{
                margin: 30px 0;
                padding: 20px;
                background: #f8f9fa;
                border-radius: 8px;
                border-left: 4px solid #667eea;
            }}
            .section h2 {{
                color: #333;
                margin-bottom: 15px;
                font-size: 1.5em;
            }}
            .section p {{
                color: #555;
                line-height: 1.6;
                margin-bottom: 15px;
            }}
            .links {{
                display: flex;
                flex-wrap: wrap;
                gap: 15px;
                margin-top: 20px;
            }}
            .btn {{
                display: inline-block;
                padding: 12px 24px;
                background: #667eea;
                color: white;
                text-decoration: none;
                border-radius: 6px;
                font-weight: 600;
                transition: all 0.3s;
                border: none;
                cursor: pointer;
            }}
            .btn:hover {{
                background: #5568d3;
                transform: translateY(-2px);
                box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
            }}
            .btn-secondary {{
                background: #6c757d;
            }}
            .btn-secondary:hover {{
                background: #5a6268;
            }}
            .btn-success {{
                background: #28a745;
            }}
            .btn-success:hover {{
                background: #218838;
            }}
            .code {{
                background: #2d2d2d;
                color: #f8f8f2;
                padding: 15px;
                border-radius: 6px;
                font-family: 'Monaco', 'Courier New', monospace;
                font-size: 0.9em;
                overflow-x: auto;
                margin: 10px 0;
            }}
            .step {{
                background: white;
                padding: 15px;
                margin: 10px 0;
                border-radius: 6px;
                border-left: 3px solid #28a745;
            }}
            .step-number {{
                display: inline-block;
                background: #28a745;
                color: white;
                width: 24px;
                height: 24px;
                border-radius: 50%;
                text-align: center;
                line-height: 24px;
                font-weight: bold;
                margin-right: 10px;
            }}
            .endpoint-list {{
                list-style: none;
                padding: 0;
            }}
            .endpoint-list li {{
                padding: 8px 0;
                border-bottom: 1px solid #e9ecef;
            }}
            .endpoint-list li:last-child {{
                border-bottom: none;
            }}
            .endpoint-list code {{
                background: #e9ecef;
                padding: 2px 6px;
                border-radius: 3px;
                color: #d63384;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🚀 Provote API</h1>
            <p class="subtitle">Welcome to the Provote Polling API v1.0.0</p>

            <div class="section">
                <h2>📖 What's Next?</h2>
                <p>You're looking at the API root. Here's how to get started:</p>
                
                <div class="step">
                    <span class="step-number">1</span>
                    <strong>Explore the Documentation</strong>
                    <p>Check out our interactive API documentation to see all available endpoints and try them out.</p>
                </div>

                <div class="step">
                    <span class="step-number">2</span>
                    <strong>Get Authenticated</strong>
                    <p>To use the API, you'll need a Bearer token. Use the authentication endpoint to get one.</p>
                </div>

                <div class="step">
                    <span class="step-number">3</span>
                    <strong>Start Building</strong>
                    <p>Create polls, cast votes, and explore all the features of the Provote API.</p>
                </div>
            </div>

            <div class="section">
                <h2>🔗 Quick Links</h2>
                <div class="links">
                    <a href="{api_docs_url}" class="btn">📘 Swagger UI (Interactive Docs)</a>
                    <a href="{api_redoc_url}" class="btn btn-secondary">📕 ReDoc (Alternative Docs)</a>
                    <a href="{api_root_url}" class="btn btn-success">🔗 API Root (JSON)</a>
                </div>
            </div>

            <div class="section">
                <h2>🔑 Get Started - Authentication</h2>
                <p>To get a Bearer token, make a POST request to:</p>
                <div class="code">POST {auth_token_url}

{{
  "username": "your_username",
  "password": "your_password"
}}</div>
                <p><strong>Full URL:</strong> <a href="{auth_token_url}" style="color: #667eea; word-break: break-all;">{auth_token_url}</a></p>
                <p style="margin-top: 15px;">Then use the token in the Authorization header:</p>
                <div class="code">Authorization: Bearer your_token_here</div>
            </div>

            <div class="section">
                <h2>📋 Available Endpoints</h2>
                <ul class="endpoint-list">
                    <li><code>GET <a href="{polls_url}" style="color: #667eea;">{polls_url}</a></code> - List all polls</li>
                    <li><code>POST {polls_url}</code> - Create a new poll</li>
                    <li><code>GET <a href="{votes_url}" style="color: #667eea;">{votes_url}</a></code> - List votes</li>
                    <li><code>POST {votes_url}</code> - Cast a vote</li>
                    <li><code>GET <a href="{users_url}" style="color: #667eea;">{users_url}</a></code> - User management</li>
                    <li><code>GET <a href="{analytics_url}" style="color: #667eea;">{analytics_url}</a></code> - Poll analytics</li>
                    <li><code>GET <a href="{notifications_url}" style="color: #667eea;">{notifications_url}</a></code> - User notifications</li>
                </ul>
                <p style="margin-top: 15px;"><strong>💡 Tip:</strong> Visit <a href="{api_docs_url}">Swagger UI</a> to see all endpoints with full documentation and try them out interactively!</p>
            </div>

            <div class="section">
                <h2>🛠️ Using the API</h2>
                <p><strong>Option 1: Interactive Documentation (Easiest)</strong></p>
                <p>Visit <a href="{api_docs_url}">Swagger UI</a> to explore and test endpoints directly in your browser.</p>
                
                <p style="margin-top: 15px;"><strong>Option 2: API Clients</strong></p>
                <p>Use tools like Postman, Insomnia, or cURL. Import the OpenAPI schema from:</p>
                <div class="code"><a href="{api_schema_url}?format=json" style="color: #f8f8f2;">{api_schema_url}?format=json</a></div>
                <p style="margin-top: 10px;">Or YAML format: <a href="{api_schema_url}?format=yaml" style="color: #667eea;">{api_schema_url}?format=yaml</a></p>
            </div>
        </div>
    </body>
    </html>
    """.format(
        api_docs_url=api_docs_url,
        api_redoc_url=api_redoc_url,
        api_root_url=api_root_url,
        api_schema_url=api_schema_url,
        auth_token_url=auth_token_url,
        polls_url=polls_url,
        votes_url=votes_url,
        users_url=users_url,
        analytics_url=analytics_url,
        notifications_url=notifications_url,
    )
    return HttpResponse(html_content, content_type="text/html")


urlpatterns = [
    path("", root_view, name="root"),
    path("admin/", admin.site.urls),
    # Health check endpoint for Docker/load balancers
    path("health/", health_check, name="health-check"),
    # Metrics endpoint for Prometheus (if available)
]
if PROMETHEUS_AVAILABLE:
    urlpatterns.append(path("metrics/", include("django_prometheus.urls")))

urlpatterns += [
    # API Root - accessible without authentication
    path("api/v1/", api_root, name="api-root"),
    path("api/v1/", include("apps.polls.urls")),
    path("api/v1/", include("apps.votes.urls")),
    path("api/v1/", include("apps.users.urls")),
    path("api/v1/", include("apps.analytics.urls")),
    path("api/v1/", include("apps.notifications.urls")),
    # API Documentation
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/schema/view/", schema_viewer, name="schema-viewer"
    ),  # Browser-friendly schema page
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
