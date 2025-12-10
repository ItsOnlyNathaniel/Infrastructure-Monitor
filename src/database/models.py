from fastapi import FastAPI
from pydantic import BaseModel, ValidationError
from datetime import datetime

class Incident(BaseModel):
    id: int
    name: str
    time: datetime
    code: str

class Services(BaseModel):
    id: int
    name: str
    code: str
    is_active: bool
    status: str

class RemediationLogs(BaseModel):
    id: int
    name: str
    time: datetime
    status: str

class Configurations(BaseModel):
    id: int
    name:str
    