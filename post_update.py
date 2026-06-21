import os
from src.app import app, make_event_image, make_caption, post_to_fb

# Use Flask app context to ensure everything is loaded
with app.app_context():
    data = {
        "event": "fulltime",
        "home": "Argentina",
        "away": "Croatia",
        "home_code": "ar",
        "away_code": "hr",
        "sh": "3",
        "sa": "0",
        "comp": "World Cup"
    }
    
    print("Generating Brand-Aligned Image...")
    img_path = make_event_image(data["event"], data)
    
    if img_path:
        caption = make_caption(data["event"], data)
        print(f"Posting to Facebook: {caption}")
        result = post_to_fb(img_path, caption)
        print(f"Result: {result}")
        
        # Cleanup
        if os.path.exists(img_path):
            os.remove(img_path)
    else:
        print("Failed to generate image.")
