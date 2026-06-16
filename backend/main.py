import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.database.connection import connect_db, disconnect_db
from app.routes.auth import router as auth_router
from app.routes.employee import router as employee_router
from app.routes.department import router as department_router
from app.routes.schedule import router as schedule_router
from app.routes.attendance import router as attendance_router
from app.routes.leave import router as leave_router
from app.routes.notification import router as notification_router
from app.routes.analytics import router as analytics_router
from app.routes.settings import router as settings_router
from app.routes.ip_settings import router as ip_settings_router
from app.routes.sales import router as sales_router
from app.routes.finance import router as finance_router
from app.routes.expense import router as expense_router
from app.routes.payroll import router as payroll_router
from app.routes.reports import router as reports_router
from app.routes.assets import router as assets_router
from app.routes.performance import router as performance_router
from app.routes.offboarding import router as offboarding_router
from app.routes.audit_log import router as audit_log_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_db()
    from app.deepface_service.face_recognition import preload_model
    preload_model()
    yield
    await disconnect_db()

import logging
logging.getLogger("uvicorn.access").setLevel(logging.WARNING)

app = FastAPI(
    title="Synvex Business Management System",
    description="Unified Business Management Web Application - Sales, Finance, HR, Assets, Attendance",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(employee_router)
app.include_router(department_router)
app.include_router(schedule_router)
app.include_router(attendance_router)
app.include_router(leave_router)
app.include_router(notification_router)
app.include_router(analytics_router)
app.include_router(settings_router)
app.include_router(ip_settings_router)
app.include_router(sales_router)
app.include_router(finance_router)
app.include_router(expense_router)
app.include_router(payroll_router)
app.include_router(reports_router)
app.include_router(assets_router)
app.include_router(performance_router)
app.include_router(offboarding_router)
app.include_router(audit_log_router)

@app.get("/")
async def root():
    return {"message": "Synvex Business Management System API is running!"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)