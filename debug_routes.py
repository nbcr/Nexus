import asyncio
import sys
import os

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from app.main import app

def debug_routes():
    print("Registered routes:")
    for route in app.routes:
        if hasattr(route, 'path'):
            methods = getattr(route, 'methods', ['ANY'])
            print(f"  {methods}: {route.path}")
    
    print(f"\nTotal routes: {len(app.routes)}")
    
    # Check if trending routes exist
    trending_routes = [r for r in app.routes if '/api/v1/trending' in getattr(r, 'path', '')]
    print(f"\nTrending routes found: {len(trending_routes)}")
    for route in trending_routes:
        print(f"  {route.path}")

if __name__ == "__main__":
    debug_routes()
