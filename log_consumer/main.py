from fastapi import FastAPI, Body

from pydantic import BaseModel

class LogMessage(BaseModel):
    level: str
    id: str
    message: str

class LogStatus(BaseModel):
    status: str

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.post("/log/message", response_model=LogStatus)
async def post_log_message(message: LogMessage = Body(LogMessage(
    level='INFO',
    id='42',
    message='hello log'
))):

    print(message)

    return LogStatus(status='ok')

