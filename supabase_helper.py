from supabase import create_client, Client
import os

def get_supabase() -> Client:
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    if not url or not key:
        raise Exception("SUPABASE_URL or SUPABASE_KEY is missing from environment variables")
    return create_client(url, key)
