from fastapi import FastAPI

app = FastAPI(
    title="AI Interview Copilot",
    version="1.0.0"
)

@app.get("/")
def root():
    return {"message" : "AI Interview Copilot API"}