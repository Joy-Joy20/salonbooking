from app import app

# ✅ correct handler for Flask in Vercel
def handler(environ, start_response):
    return app(environ, start_response)