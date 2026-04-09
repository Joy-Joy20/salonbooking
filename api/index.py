from app import app

# Vercel expects this
def handler(request, context):
    return app