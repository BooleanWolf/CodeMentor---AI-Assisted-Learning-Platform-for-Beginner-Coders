from fastapi import FastAPI
from routers import users, topics


app = FastAPI()

# Include routers
app.include_router(users.router)
# app.include_router(contents.router)
app.include_router(topics.router)

@app.get("/")
def root():
    return {"message": "API is running"}