from fastapi import FastAPI

app = FastAPI()

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello, {name}!"}