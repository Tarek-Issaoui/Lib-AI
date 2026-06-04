from fastapi import FastAPI
from .routes import router as livres_router
app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World"}

app.include_router(livres_router)