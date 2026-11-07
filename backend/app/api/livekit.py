import uuid

from fastapi import APIRouter, HTTPException
from livekit.api import AccessToken, RoomAgentDispatch, RoomConfiguration, VideoGrants

from app.config import settings
from app.schemas import LiveKitTokenResponse

router = APIRouter()


@router.post("/livekit/token", response_model=LiveKitTokenResponse)
def create_livekit_token():
    if not settings.livekit_api_key.strip() or not settings.livekit_api_secret.strip():
        raise HTTPException(status_code=503, detail="LiveKit API key/secret are not configured.")
    if not settings.livekit_url.strip():
        raise HTTPException(status_code=503, detail="LIVEKIT_URL is not configured.")

    room = f"{settings.livekit_room_prefix}-{uuid.uuid4().hex[:8]}"
    identity = f"visitor-{uuid.uuid4().hex[:8]}"
    token = (
        AccessToken(settings.livekit_api_key, settings.livekit_api_secret)
        .with_identity(identity)
        .with_name("Portfolio visitor")
        .with_grants(
            VideoGrants(
                room_join=True,
                room=room,
                can_publish=True,
                can_subscribe=True,
                can_publish_data=True,
            )
        )
        .with_room_config(RoomConfiguration(agents=[RoomAgentDispatch()]))
        .to_jwt()
    )
    return LiveKitTokenResponse(url=settings.livekit_url, token=token, room=room, identity=identity)
