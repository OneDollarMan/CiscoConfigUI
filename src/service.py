import difflib
import os
from pathlib import Path
from typing import Sequence

from fastapi import HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import aiofiles
from config import UPLOAD_DIRECTORY
from src.models import Device
from src.schemas import DeviceCreate, DeviceConfigRead, DeviceUpdate


async def check_device_name_exists(session: AsyncSession, device_name: str) -> bool:
    device = await session.execute(select(Device).filter(Device.name == device_name).limit(1))
    return device.scalar() is not None


async def get_device_by_id(session: AsyncSession, device_id: int) -> Device | None:
    device = await session.execute(select(Device).filter(Device.id == device_id))
    return device.scalar()


async def get_all_devices(session: AsyncSession) -> Sequence[Device]:
    devices = await session.execute(select(Device))
    return devices.scalars().all()


async def create_device(session: AsyncSession, device_schema: DeviceCreate) -> Device:
    if await check_device_name_exists(session, device_schema.name):
        raise HTTPException(status_code=400, detail="Device already exists")

    device = Device(**device_schema.model_dump())
    session.add(device)
    await session.commit()
    await session.refresh(device)
    return device


async def update_device(session: AsyncSession, device_id: int, device_schema: DeviceUpdate):
    device = await get_device_by_id(session, device_id)
    if not device:
        raise HTTPException(status_code=404, detail=f"Device with {device_id=} not found")

    device.ip_address = device_schema.ip_address

    await session.commit()
    await session.refresh(device)
    return device


async def delete_device(session: AsyncSession, device_id: int) -> bool:
    device = await get_device_by_id(session, device_id)
    if not device:
        raise HTTPException(status_code=404, detail=f"Device with {device_id=} not found")

    await session.delete(device)
    await session.commit()
    if device.config_file_path:
        os.remove(str(device.config_file_path))
    return True


async def upload_device_config(session: AsyncSession, device_id: int, config_file: UploadFile) -> Device:
    device = await get_device_by_id(session, device_id)
    if not device:
        raise HTTPException(status_code=404, detail=f"Device with {device_id=} not found")

    if config_file.content_type != 'text/plain':
        raise HTTPException(status_code=400, detail="File must be .txt")

    config_file_path = f"{UPLOAD_DIRECTORY}/{device.name}.txt"
    async with aiofiles.open(config_file_path, mode='wb+') as f:
        await f.write(config_file.file.read())

    device.config_file_path = config_file_path
    await session.commit()
    return device


async def get_device_config_path(session: AsyncSession, device_id: int) -> (Device, Path):
    device = await get_device_by_id(session, device_id)
    if not device:
        raise HTTPException(status_code=404, detail=f"Device with {device_id=} not found")

    if not device.config_file_path:
        raise HTTPException(status_code=404, detail=f"No config found for device with {device_id=}")

    file = Path(str(device.config_file_path))
    if not file.exists() or not file.suffix == '.txt':
        raise HTTPException(status_code=404, detail="File not found or not a text file")

    return device, file


async def get_device_config(session: AsyncSession, device_id: int) -> DeviceConfigRead:
    device, file = await get_device_config_path(session, device_id)

    async with aiofiles.open(file, mode='r') as f:
        content = await f.read()

    return DeviceConfigRead(device_name=device.name, config_content=content)


async def compare_strings_to_html(session: AsyncSession, device1_id: int, device2_id: int):
    device1_config, device2_config = await get_device_config(session, device1_id), await get_device_config(session, device2_id)
    file1_lines = device1_config.config_content.splitlines()
    file2_lines = device2_config.config_content.splitlines()
    diff = difflib.HtmlDiff().make_file(file1_lines, file2_lines, fromdesc=device1_config.device_name, todesc=device2_config.device_name)
    return diff
