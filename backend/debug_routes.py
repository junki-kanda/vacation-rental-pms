"""Debug script to check registered routes"""

from api.main import app

print("Registered routes:")
for route in app.routes:
    if hasattr(route, 'path') and hasattr(route, 'methods'):
        print(f"  {route.methods} {route.path}")
    elif hasattr(route, 'path'):
        print(f"  {route.path}")
        
print("\nTotal routes:", len(app.routes))