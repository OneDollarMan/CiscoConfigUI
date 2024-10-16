from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, UploadFile, File
from fastapi_users import fastapi_users
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.requests import Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles

from src.db import create_db_and_tables, get_async_session
from src.models import User
from src.schemas import UserRead, UserCreate, UserUpdate, DeviceRead, DeviceCreate, DeviceConfigRead, DeviceUpdate
from src.users import auth_backend, get_user_manager, authenticator, current_active_user
import src.service as service
from fastapi.templating import Jinja2Templates


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_db_and_tables()
    yield


app = FastAPI(lifespan=lifespan)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

app.include_router(
    fastapi_users.get_auth_router(auth_backend, get_user_manager, authenticator), prefix="/api/auth/jwt", tags=["auth"]
)
app.include_router(
    fastapi_users.get_register_router(get_user_manager, UserRead, UserCreate),
    prefix="/api/auth",
    tags=["auth"],
)
app.include_router(
    fastapi_users.get_reset_password_router(get_user_manager),
    prefix="/api/auth",
    tags=["auth"],
)
app.include_router(
    fastapi_users.get_verify_router(get_user_manager, UserRead),
    prefix="/api/auth",
    tags=["auth"],
)
app.include_router(
    fastapi_users.get_users_router(get_user_manager, UserRead, UserUpdate, authenticator),
    prefix="/api/users",
    tags=["users"],
)


@app.get("/api/devices", tags=['devices'], response_model=list[DeviceRead])
async def get_all_devices(
        user: User = Depends(current_active_user),
        session: AsyncSession = Depends(get_async_session)
):
    return await service.get_all_devices(session)


@app.post("/api/devices", tags=['devices'], response_model=DeviceRead)
async def post_create_device(
        device_schema: DeviceCreate,
        user: User = Depends(current_active_user),
        session: AsyncSession = Depends(get_async_session)
):
    return await service.create_device(session, device_schema)


@app.patch("/api/devices/{device_id}", tags=['devices'], response_model=DeviceRead)
async def patch_device(
        device_id: int,
        device_schema: DeviceUpdate,
        user: User = Depends(current_active_user),
        session: AsyncSession = Depends(get_async_session)
):
    return await service.update_device(session, device_id, device_schema)


@app.delete("/api/devices/{device_id}", tags=['devices'])
async def delete_device(
        device_id: int,
        user: User = Depends(current_active_user),
        session: AsyncSession = Depends(get_async_session)
):
    return await service.delete_device(session, device_id)


@app.post("/api/devices/{device_id}/upload_config", tags=['devices'], response_model=DeviceRead)
async def post_device_upload_config(
        device_id: int,
        config_file: UploadFile = File(media_type='text/plain'),
        user: User = Depends(current_active_user),
        session: AsyncSession = Depends(get_async_session)
):
    return await service.upload_device_config(session, device_id, config_file)


@app.get("/api/devices/{device_id}/get_config", tags=['devices'], response_model=DeviceConfigRead)
async def get_device_config(
        device_id: int,
        user: User = Depends(current_active_user),
        session: AsyncSession = Depends(get_async_session)
):
    return await service.get_device_config(session, device_id)


@app.get("/api/devices/{device_id}/download_config", tags=['devices'], response_model=DeviceConfigRead)
async def download_device_config(
        device_id: int,
        user: User = Depends(current_active_user),
        session: AsyncSession = Depends(get_async_session)
):
    device, file = await service.get_device_config_path(session, device_id)
    return FileResponse(path=file, filename=file.name, media_type='text/plain')


# Frontend pages
@app.get('/', tags=['pages'], response_class=HTMLResponse)
async def get_index(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")


@app.get('/devices', tags=['pages'], response_class=HTMLResponse)
async def get_devices_list(
        request: Request,
        user: User = Depends(current_active_user),
        session: AsyncSession = Depends(get_async_session)
):
    return templates.TemplateResponse(request=request, name="devices.html", context={'user': user, 'devices': await service.get_all_devices(session)})


@app.get('/devices/{device_id}', tags=['pages'], response_class=HTMLResponse)
async def get_device(
        device_id: int,
        request: Request,
        session: AsyncSession = Depends(get_async_session),
        user: User = Depends(current_active_user)
):
    device = await service.get_device_by_id(session, device_id)
    config = await service.get_device_config(session, device_id)
    return templates.TemplateResponse(request=request, name="device.html", context={'user': user, 'device': device, 'config': config.config_content.splitlines() })


@app.get('/compare', tags=['pages'], response_class=HTMLResponse)
async def get_compare(
        request: Request,
        device1_id: int = None,
        device2_id: int = None,
        session: AsyncSession = Depends(get_async_session),
        user: User = Depends(current_active_user)
):
    context = {'user': user}
    if device1_id and device2_id:
        context['diff'] = await service.compare_strings_to_html(session, device1_id, device2_id)
    else:
        context['devices'] = await service.get_all_devices(session)
    return templates.TemplateResponse(request=request, name="compare.html", context=context)
