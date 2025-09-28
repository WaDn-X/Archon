#!/usr/bin/env python3
"""
Simple HTTP Server for Zippy-Archon Platform
This is a simplified version to avoid dependency conflicts.
"""
import os
import json
import logging
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import threading
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ZippyArchonHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Handle GET requests"""
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        
        try:
            if path == "/":
                self.serve_index()
            elif path == "/health":
                self.serve_health()
            elif path == "/docs":
                self.serve_docs()
            elif path == "/static/index.html":
                self.serve_static_file("static/index.html", "text/html")
            elif path.startswith("/static/"):
                self.serve_static_file(path[1:], self.get_content_type(path))
            else:
                self.send_error(404, "Not Found")
        except Exception as e:
            logger.error(f"Error handling GET request: {e}")
            self.send_error(500, "Internal Server Error")
    
    def do_POST(self):
        """Handle POST requests"""
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            
            if path == "/api/v1/specs/generate":
                self.handle_generate_specs(post_data)
            elif path == "/api/v1/ab-test/run":
                self.handle_ab_test(post_data)
            elif path == "/api/v1/marketplace/listings":
                self.handle_marketplace_listings()
            elif path == "/api/v1/trust/validate":
                self.handle_trust_validation(post_data)
            else:
                self.send_error(404, "Not Found")
        except Exception as e:
            logger.error(f"Error handling POST request: {e}")
            self.send_error(500, "Internal Server Error")
    
    def serve_index(self):
        """Serve the main index.html file"""
        try:
            with open("static/index.html", "r", encoding="utf-8") as f:
                content = f.read()
            
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(content.encode('utf-8'))
        except FileNotFoundError:
            self.send_error(404, "index.html not found")
    
    def serve_health(self):
        """Serve health check endpoint"""
        health_data = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "services": {
                "ai_providers": True,
                "database": True,
                "trust_validation": True,
                "marketplace": True
            },
            "version": "1.0.0"
        }
        
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(health_data).encode('utf-8'))
    
    def serve_docs(self):
        """Serve API documentation"""
        docs_html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Zippy-Archon API Documentation</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; }
                .endpoint { background: #f5f5f5; padding: 20px; margin: 20px 0; border-radius: 5px; }
                .method { font-weight: bold; color: #0066cc; }
            </style>
        </head>
        <body>
            <h1>Zippy-Archon Platform API</h1>
            <p>Welcome to the Zippy-Archon platform API documentation.</p>
            
            <div class="endpoint">
                <h2><span class="method">GET</span> /health</h2>
                <p>Check system health and service status</p>
            </div>
            
            <div class="endpoint">
                <h2><span class="method">POST</span> /api/v1/specs/generate</h2>
                <p>Generate requirements, design, and tasks from a feature description</p>
            </div>
            
            <div class="endpoint">
                <h2><span class="method">POST</span> /api/v1/ab-test/run</h2>
                <p>Run A/B testing on different prompt versions</p>
            </div>
            
            <div class="endpoint">
                <h2><span class="method">GET</span> /api/v1/marketplace/listings</h2>
                <p>Get marketplace listings</p>
            </div>
            
            <div class="endpoint">
                <h2><span class="method">POST</span> /api/v1/trust/validate</h2>
                <p>Validate content using ZippyTrust</p>
            </div>
        </body>
        </html>
        """
        
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(docs_html.encode('utf-8'))
    
    def serve_static_file(self, file_path, content_type):
        """Serve static files"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            self.send_response(200)
            self.send_header('Content-Type', content_type)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(content.encode('utf-8'))
        except FileNotFoundError:
            self.send_error(404, f"File {file_path} not found")
    
    def get_content_type(self, path):
        """Get content type based on file extension"""
        if path.endswith('.css'):
            return 'text/css'
        elif path.endswith('.js'):
            return 'application/javascript'
        elif path.endswith('.png'):
            return 'image/png'
        elif path.endswith('.jpg') or path.endswith('.jpeg'):
            return 'image/jpeg'
        elif path.endswith('.svg'):
            return 'image/svg+xml'
        else:
            return 'text/plain'
    
    def handle_generate_specs(self, post_data):
        """Handle requirements generation"""
        try:
            data = json.loads(post_data.decode('utf-8'))
            prompt = data.get('prompt', '')
            provider = data.get('provider', 'grok')
            version = data.get('version', 'v1')
            
            # Mock response
            response = {
                "success": True,
                "provider": provider,
                "version": version,
                "requirements": {
                    "content": f"# Requirements for: {prompt[:50]}...\n\n## Functional Requirements\n- Feature 1: Description\n- Feature 2: Description\n\n## Non-Functional Requirements\n- Performance: Response time < 2s\n- Security: Authentication required"
                },
                "design": {
                    "content": f"# Design Document\n\n## Architecture\n- Frontend: React/TypeScript\n- Backend: FastAPI/Python\n- Database: PostgreSQL\n\n## Components\n- User Interface\n- API Layer\n- Data Layer"
                },
                "tasks": {
                    "content": f"# Implementation Tasks\n\n## Phase 1\n- [ ] Set up project structure\n- [ ] Create basic UI components\n- [ ] Implement API endpoints\n\n## Phase 2\n- [ ] Add authentication\n- [ ] Implement core features\n- [ ] Add testing"
                }
            }
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode('utf-8'))
            
        except json.JSONDecodeError:
            self.send_error(400, "Invalid JSON")
    
    def handle_ab_test(self, post_data):
        """Handle A/B testing"""
        try:
            data = json.loads(post_data.decode('utf-8'))
            prompt = data.get('prompt', '')
            versions = data.get('versions', ['v1', 'v2'])
            
            # Mock response
            scores = {}
            for version in versions:
                scores[version] = round(85 + (hash(version) % 15), 1)  # Random score between 85-100
            
            winner = max(scores, key=scores.get)
            
            response = {
                "success": True,
                "test_id": f"ab_test_{int(time.time())}",
                "results": {
                    "winner": winner,
                    "scores": scores,
                    "prompt": prompt[:100] + "..." if len(prompt) > 100 else prompt
                }
            }
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode('utf-8'))
            
        except json.JSONDecodeError:
            self.send_error(400, "Invalid JSON")
    
    def handle_marketplace_listings(self):
        """Handle marketplace listings"""
        # Mock response
        response = {
            "success": True,
            "total": 3,
            "listings": [
                {
                    "id": "1",
                    "title": "User Authentication Template",
                    "description": "Comprehensive authentication system with OAuth, 2FA, and role-based access control",
                    "price": 150,
                    "trust_score": 95,
                    "category": "security"
                },
                {
                    "id": "2", 
                    "title": "E-commerce Requirements",
                    "description": "Complete e-commerce platform requirements with payment processing and inventory management",
                    "price": 200,
                    "trust_score": 92,
                    "category": "ecommerce"
                },
                {
                    "id": "3",
                    "title": "API Design Patterns",
                    "description": "RESTful API design patterns and best practices for microservices",
                    "price": 75,
                    "trust_score": 88,
                    "category": "api"
                }
            ]
        }
        
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(response).encode('utf-8'))
    
    def handle_trust_validation(self, post_data):
        """Handle trust validation"""
        try:
            data = json.loads(post_data.decode('utf-8'))
            content = data.get('content', '')
            content_type = data.get('content_type', 'requirements')
            
            # Mock validation
            trust_score = min(95, max(70, len(content) % 30 + 70))  # Score between 70-95
            trust_level = "High" if trust_score > 85 else "Medium" if trust_score > 75 else "Low"
            
            response = {
                "success": True,
                "trust_score": trust_score,
                "trust_level": trust_level,
                "metrics": {
                    "clarity": round(trust_score * 0.9, 1),
                    "structure": round(trust_score * 0.95, 1),
                    "testability": round(trust_score * 0.85, 1),
                    "security": round(trust_score * 0.92, 1)
                },
                "insights": [
                    "Content shows good structure and organization",
                    "Requirements are clear and actionable",
                    "Security considerations are well addressed",
                    "Consider adding more specific acceptance criteria"
                ]
            }
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode('utf-8'))
            
        except json.JSONDecodeError:
            self.send_error(400, "Invalid JSON")
    
    def log_message(self, format, *args):
        """Custom logging to avoid default server logs"""
        logger.info(f"{self.address_string()} - {format % args}")

def start_server():
    """Start the HTTP server"""
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8686"))
    
    server = HTTPServer((host, port), ZippyArchonHandler)
    
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║                    Zippy-Archon Platform                    ║")
    print("║                                                              ║")
    print(f"║  🚀 Starting simplified platform on {host}:{port}          ║")
    print("║                                                              ║")
    print("║  📖 API Documentation: http://localhost:8686/docs           ║")
    print("║  🔍 Health Check: http://localhost:8686/health              ║")
    print("║  🌐 Web Interface: http://localhost:8686/                   ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
        server.shutdown()

if __name__ == "__main__":
    start_server()
