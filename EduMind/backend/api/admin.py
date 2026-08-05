"""Administrator authentication and protected model configuration endpoints."""

import httpx
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.dependencies import get_current_admin, get_db
from core.exceptions import ServiceUnavailableError, UnauthorizedError, ValidationError
from core.security import create_access_token, hash_password, verify_password
from models.admin import AdminUser, SystemModelConfig
from schemas.admin import (
    AdminLoginRequest,
    AdminPasswordChangeRequest,
    AdminSessionResponse,
    ModelConfigResponse,
    ModelConfigUpdateRequest,
    ModelConnectionTestRequest,
    ModelConnectionTestResponse,
)
from schemas.response import StandardResponse
from services.model_config import model_config_service

router = APIRouter(prefix="/admin", tags=["admin"])


def _config_response(row: SystemModelConfig) -> ModelConfigResponse:
    runtime = model_config_service.runtime
    return ModelConfigResponse(
        llm_api_key_configured=bool(runtime.llm_api_key),
        llm_api_key_masked=model_config_service.mask(runtime.llm_api_key),
        llm_base_url=row.llm_base_url,
        llm_model=row.llm_model,
        llm_max_tokens=row.llm_max_tokens,
        llm_temperature=row.llm_temperature,
        llm_enable_thinking=row.llm_enable_thinking,
        llm_timeout_seconds=row.llm_timeout_seconds,
        embedding_api_key_configured=bool(runtime.embedding_api_key),
        embedding_api_key_masked=model_config_service.mask(runtime.embedding_api_key),
        embedding_base_url=row.embedding_base_url,
        embedding_model=row.embedding_model,
        embedding_dimensions=row.embedding_dimensions,
        updated_at=row.updated_at,
    )


@router.post("/login", response_model=StandardResponse[AdminSessionResponse])
async def admin_login(payload: AdminLoginRequest, db: AsyncSession = Depends(get_db)) -> StandardResponse:
    admin = await db.scalar(select(AdminUser).where(AdminUser.username == payload.username))
    if not admin or not admin.is_active or not verify_password(payload.password, admin.hashed_password):
        raise UnauthorizedError("管理员账号或密码错误")
    token = create_access_token({"sub": str(admin.id), "role": "admin"})
    return StandardResponse.ok(
        data=AdminSessionResponse(
            access_token=token,
            username=admin.username,
            display_name=admin.display_name,
            must_change_password=admin.must_change_password,
        ),
        message="管理员登录成功",
    )


@router.get("/config", response_model=StandardResponse[ModelConfigResponse])
async def get_model_config(
    admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> StandardResponse:
    row = await model_config_service.load(db)
    if row is None:
        raise ValidationError("模型配置尚未初始化")
    return StandardResponse.ok(data=_config_response(row), message="模型配置读取成功")


@router.put("/config", response_model=StandardResponse[ModelConfigResponse])
async def update_model_config(
    payload: ModelConfigUpdateRequest,
    admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> StandardResponse:
    row = await db.get(SystemModelConfig, 1)
    if row is None:
        raise ValidationError("模型配置尚未初始化")

    if payload.clear_llm_api_key:
        row.llm_api_key_encrypted = None
    elif payload.llm_api_key and payload.llm_api_key.strip():
        row.llm_api_key_encrypted = model_config_service.encrypt(payload.llm_api_key)

    if payload.clear_embedding_api_key:
        row.embedding_api_key_encrypted = None
    elif payload.embedding_api_key and payload.embedding_api_key.strip():
        row.embedding_api_key_encrypted = model_config_service.encrypt(payload.embedding_api_key)

    row.llm_base_url = str(payload.llm_base_url).rstrip("/")
    row.llm_model = payload.llm_model.strip()
    row.llm_max_tokens = payload.llm_max_tokens
    row.llm_temperature = payload.llm_temperature
    row.llm_enable_thinking = payload.llm_enable_thinking
    row.llm_timeout_seconds = payload.llm_timeout_seconds
    row.embedding_base_url = str(payload.embedding_base_url).rstrip("/")
    row.embedding_model = payload.embedding_model.strip()
    row.embedding_dimensions = payload.embedding_dimensions
    row.updated_by = admin.id
    await db.flush()
    model_config_service._apply_row(row)
    return StandardResponse.ok(data=_config_response(row), message="模型配置已安全保存")


@router.post("/config/test", response_model=StandardResponse[ModelConnectionTestResponse])
async def test_model_connection(
    payload: ModelConnectionTestRequest,
    admin: AdminUser = Depends(get_current_admin),
) -> StandardResponse:
    runtime = model_config_service.runtime
    api_key = (payload.api_key or "").strip()
    if not api_key:
        api_key = runtime.llm_api_key if payload.service == "llm" else runtime.embedding_api_key
    if not api_key:
        raise ValidationError("请先填写或保存对应的 API Key")

    base_url = str(payload.base_url).rstrip("/")
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            if payload.service == "llm":
                response = await client.post(
                    f"{base_url}/chat/completions",
                    headers=headers,
                    json={
                        "model": payload.model,
                        "messages": [{"role": "user", "content": "只回复：连接成功"}],
                        "max_tokens": 32,
                        "temperature": 0,
                        "enable_thinking": False,
                    },
                )
                if response.status_code != 200:
                    raise ValidationError(f"对话模型连接失败（HTTP {response.status_code}）")
                detail = "对话模型连接成功"
                dimensions = None
            else:
                response = await client.post(
                    f"{base_url}/embeddings",
                    headers=headers,
                    json={"model": payload.model, "input": ["EduMind 连接测试"]},
                )
                if response.status_code != 200:
                    raise ValidationError(f"向量模型连接失败（HTTP {response.status_code}）")
                vector = response.json()["data"][0]["embedding"]
                dimensions = len(vector)
                if payload.embedding_dimensions and dimensions != payload.embedding_dimensions:
                    raise ValidationError(
                        f"向量维度不一致：模型返回 {dimensions}，当前配置为 {payload.embedding_dimensions}"
                    )
                detail = f"向量模型连接成功，维度 {dimensions}"
    except ValidationError:
        raise
    except Exception as exc:
        raise ServiceUnavailableError(f"模型连接测试（{type(exc).__name__}）") from exc

    return StandardResponse.ok(
        data=ModelConnectionTestResponse(
            service=payload.service,
            connected=True,
            model=payload.model,
            detail=detail,
            dimensions=dimensions,
        ),
        message=detail,
    )


@router.put("/password", response_model=StandardResponse)
async def change_admin_password(
    payload: AdminPasswordChangeRequest,
    admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> StandardResponse:
    if not verify_password(payload.current_password, admin.hashed_password):
        raise UnauthorizedError("当前管理员密码不正确")
    admin.hashed_password = hash_password(payload.new_password)
    admin.must_change_password = False
    await db.flush()
    return StandardResponse.ok(message="管理员密码已更新")
