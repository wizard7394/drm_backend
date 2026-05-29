import uuid
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timezone
from app.models.license import License
from app.models.device import HardwareDevice
from app.schemas.auth import HardwareAuthRequest

async def verify_and_register_device(request: HardwareAuthRequest, db: AsyncSession) -> str:
    device_query = await db.execute(select(HardwareDevice).where(HardwareDevice.hardware_hash == request.hardware_hash))
    device = device_query.scalars().first()

    if device:
        if device.is_revoked:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied. Device is revoked.")
        
        device.last_online = datetime.now(timezone.utc)
        await db.commit()
        return f"jwt_{uuid.uuid4().hex}"

    license_query = await db.execute(select(License).where(License.license_key == request.license_key))
    db_license = license_query.scalars().first()

    if not db_license:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid license key.")
    
    if db_license.is_revoked:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="License is revoked.")

    devices_count_query = await db.execute(select(HardwareDevice).where(HardwareDevice.license_id == db_license.id))
    current_devices_count = len(devices_count_query.scalars().all())

    if current_devices_count >= db_license.max_devices:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Maximum device limit reached for this license.")

    new_device = HardwareDevice(
        license_id=db_license.id,
        hardware_hash=request.hardware_hash,
        platform=request.platform
    )
    db.add(new_device)
    await db.commit()
    
    return f"jwt_{uuid.uuid4().hex}"