from fastapi import FastAPI
import uvicorn
from flows.workflow_run import start_workflow


app = FastAPI()


@app.post("/start")
def start_loop():
    print("📩 /start API called")
    start_workflow()
    return {"status": "already running"}


@app.post("/stop")
def stop_loop():
    global running
    running = False
    return {"status": "stopped"}


@app.get("/status")
def get_status():
    return {"running": running}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
