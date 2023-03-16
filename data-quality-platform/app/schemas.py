from typing import Optional
from pydantic import BaseModel, EmailStr
from datetime import datetime


class Project(BaseModel):
    project_name: str
    description: str
    file: str
    data_check: str
    link_project: str

    class Config:
        orm_mode = True


class ProjectsList(BaseModel):
    id: int
    project_name: str
    description: str
    file: str
    data_check: str
    link_project: str
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class DataReportingProject(BaseModel):
    project_name: str

    class Config:
        orm_mode = True


class DataReportingProjectList(BaseModel):
    id: int
    project_name: str
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
