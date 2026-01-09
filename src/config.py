"""
配置加载模块（中文注释）：
- 优先从 `.env` 读取环境变量（如 OPENAI_API_KEY）
- 再从 `config/config.yaml` 读取其他配置
- 若关键信息缺失，给出友好提示
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import os

try:
    # 加载 .env 文件中的环境变量（如果存在）
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    # 若未安装 python-dotenv，不影响基本功能
    pass

try:
    import yaml  # 用于读取 YAML 配置文件
except Exception as e:
    raise RuntimeError("缺少 PyYAML 依赖，请先安装后再运行。") from e


@dataclass
class OpenAISettings:
    api_key: Optional[str] = None
    model: Optional[str] = None
    temperature: float = 0.2


@dataclass
class DashScopeSettings:
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    model: Optional[str] = None
    temperature: float = 0.2


@dataclass
class LangfuseSettings:
    secret_key: Optional[str] = None
    public_key: Optional[str] = None
    host: Optional[str] = "https://cloud.langfuse.com"


@dataclass
class AppConfig:
    provider: str
    openai: OpenAISettings
    dashscope: "DashScopeSettings"
    langfuse: "LangfuseSettings"


def load_yaml_config() -> dict:
    """读取 YAML 配置文件为字典。"""
    config_path = Path("config/config.yaml")
    if not config_path.exists():
        return {}
    with config_path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def load_config() -> AppConfig:
    """合并环境变量与 YAML，生成最终配置对象。"""
    data = load_yaml_config()
    provider = (data.get("provider") or "dashscope").strip()
    openai_cfg = (data.get("openai") or {})
    dashscope_cfg = (data.get("dashscope") or {})
    langfuse_cfg = (data.get("langfuse") or {})

    # 环境变量优先（如果存在）
    # OpenAI
    api_key = os.getenv("OPENAI_API_KEY") or openai_cfg.get("api_key")
    model = openai_cfg.get("model")
    temperature = float(openai_cfg.get("temperature") or 0.2)

    # DashScope (Qwen)
    ds_api_key = os.getenv("DASHSCOPE_API_KEY") or dashscope_cfg.get("api_key")
    ds_base_url = os.getenv("DASHSCOPE_BASE_URL") or dashscope_cfg.get("base_url")
    ds_model = dashscope_cfg.get("model")
    ds_temperature = float(dashscope_cfg.get("temperature") or 0.2)

    # Langfuse
    lf_secret_key = os.getenv("LANGFUSE_SECRET_KEY") or langfuse_cfg.get("secret_key")
    lf_public_key = os.getenv("LANGFUSE_PUBLIC_KEY") or langfuse_cfg.get("public_key")
    lf_host = os.getenv("LANGFUSE_HOST") or langfuse_cfg.get("host") or langfuse_cfg.get("base_url") or "https://cloud.langfuse.com"

    return AppConfig(
        provider=provider,
        openai=OpenAISettings(
            api_key=api_key,
            model=model,
            temperature=temperature,
        ),
        dashscope=DashScopeSettings(
            api_key=ds_api_key,
            base_url=ds_base_url,
            model=ds_model,
            temperature=ds_temperature,
        ),
        langfuse=LangfuseSettings(
            secret_key=lf_secret_key,
            public_key=lf_public_key,
            host=lf_host,
        ),
    )


def validate_config(cfg: AppConfig) -> list[str]:
    """校验配置，返回错误列表。"""
    errors: list[str] = []
    provider = (cfg.provider or "dashscope").lower()
    if provider == "openai":
        if not cfg.openai.api_key:
            errors.append("OPENAI_API_KEY 未设置，请在 .env 或 config/config.yaml 中填写")
        if not cfg.openai.model:
            errors.append("OpenAI 模型未设置，请在 config/config.yaml 的 openai.model 中填写")
    elif provider == "dashscope":
        if not cfg.dashscope.api_key:
            errors.append("DASHSCOPE_API_KEY 未设置，请在 .env 或 config/config.yaml 中填写")
        if not cfg.dashscope.base_url:
            errors.append("DashScope base_url 未设置，请在 .env 的 DASHSCOPE_BASE_URL 或 config.yaml 中填写")
        if not cfg.dashscope.model:
            errors.append("DashScope 模型未设置，请在 config/config.yaml 的 dashscope.model 中填写，例如 qwen-plus")
    else:
        errors.append("provider 配置不正确，请使用 openai 或 dashscope")

    # Langfuse 校验 (如果配置了 key 则校验完整性)
    if cfg.langfuse.secret_key or cfg.langfuse.public_key:
        if not cfg.langfuse.secret_key:
            errors.append("Langfuse secret_key 未设置")
        if not cfg.langfuse.public_key:
            errors.append("Langfuse public_key 未设置")
    
    return errors
