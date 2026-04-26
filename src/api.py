from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import time
import os

# Import our generator modules
from src.content_generator import generate_post, generate_image_prompt
from src.image_generator import generate_image
from src.database import init_db, save_post
from src.linkedin_publisher import publish_to_linkedin

app = FastAPI(title="Social Media Auto-Manager")

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure outputs dir exists
os.makedirs("outputs", exist_ok=True)

# Mount static files
app.mount("/dashboard", StaticFiles(directory="dashboard"), name="dashboard")
app.mount("/outputs", StaticFiles(directory="outputs"), name="outputs")

# Initialize database on startup
@app.on_event("startup")
def startup_event():
    init_db()

class GenerateRequest(BaseModel):
    topic: str
    platform: str = "LinkedIn"

class PublishRequest(BaseModel):
    post_id: int

@app.post("/api/generate")
async def api_generate(req: GenerateRequest):
    if not req.topic.strip():
        raise HTTPException(status_code=400, detail="الموضوع مطلوب")
        
    print(f"Generating content for {req.platform} about: {req.topic}")
    
    # 1. Generate text
    content = generate_post(req.topic, req.platform)
    if not content:
        raise HTTPException(status_code=500, detail="فشل في توليد النص")
        
    # 2. Generate image prompt
    img_prompt = generate_image_prompt(req.topic, content)
    
    # 3. Generate image
    safe_filename = f"post_{int(time.time())}"
    image_path = generate_image(img_prompt, safe_filename)
    
    # 4. Save to DB
    post_id = save_post(req.topic, req.platform, content, image_path)
    
    # Clean image path for web URL
    image_url = f"/outputs/{os.path.basename(image_path)}" if image_path else None
    
    return {
        "success": True,
        "post_id": post_id,
        "content": content,
        "image_url": image_url,
        "message": "تم توليد المنشور بنجاح"
    }

@app.post("/api/publish/{post_id}")
async def api_publish(post_id: int):
    # Here we would fetch the post from DB and publish it
    # For now, we just pass the ID to the publisher
    # (Publisher will simulate or actually publish if keys exist)
    success, message = publish_to_linkedin(post_id)
    
    if not success:
        raise HTTPException(status_code=500, detail=message)
        
    return {"success": True, "message": message}
