from pathlib import Path
from typing import Any
import yaml
from pydantic import BaseModel, Field

CONFIG_DIR = Path("config")


class RuntimeConfig(BaseModel):
    headless: bool = False
    submit_final: bool = False
    max_pages: int = 100
    timeout_seconds: int = 30


class LogConfig(BaseModel):
    level: str = "INFO"
    screenshot_dir: str = "logs/screenshots"
    html_dir: str = "logs/html"
    run_dir: str = "logs/runs"


class StorageConfig(BaseModel):
    format: str = "sqlite"
    db_path: str = "logs/survey.db"
    screenshot_dir: str = "logs/screenshots"
    html_dir: str = "logs/html"


class IdentityPolicyConfig(BaseModel):
    condition: str = "honest_ai"


class TextPolicyConfig(BaseModel):
    min_length: int = 10
    max_length: int = 500


class DemographicPolicyConfig(BaseModel):
    allow_skip: bool = False


class FactualPolicyConfig(BaseModel):
    require_source: bool = True


class ToogleConfig(BaseModel):
    enabled: bool = True


class PoliciesConfig(BaseModel):
    identity: IdentityPolicyConfig = Field(default_factory=IdentityPolicyConfig)
    text: TextPolicyConfig = Field(default_factory=TextPolicyConfig)
    demographic: DemographicPolicyConfig = Field(
        default_factory=DemographicPolicyConfig
    )
    factual: FactualPolicyConfig = Field(default_factory=FactualPolicyConfig)
    attention_check: ToogleConfig = Field(default_factory=ToogleConfig)
    ai_disclosure: ToogleConfig = Field(default_factory=ToogleConfig)


class ToolsConfig(BaseModel):
    calculator: ToogleConfig = Field(default_factory=ToogleConfig)
    local_context: ToogleConfig = Field(default_factory=ToogleConfig)
    rag: ToogleConfig = Field(default_factory=lambda: ToogleConfig(enabled=False))
    llm: ToogleConfig = Field(default_factory=lambda: ToogleConfig(enabled=False))
    web_search: ToogleConfig = Field(
        default_factory=lambda: ToogleConfig(enabled=False)
    )


class AppConfig(BaseModel):
    runtime: RuntimeConfig = Field(default_factory=RuntimeConfig)
    logging: LogConfig = Field(default_factory=LogConfig)
    storage: StorageConfig = Field(default_factory=StorageConfig)
    policies: PoliciesConfig = Field(default_factory=PoliciesConfig)
    tools: ToolsConfig = Field(default_factory=ToolsConfig)


def load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}

    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def load_config(config_dir: Path = CONFIG_DIR) -> AppConfig:
    config_data = load_yaml(config_dir / "config.yaml")
    policies_data = load_yaml(config_dir / "policies.yaml")
    tools_data = load_yaml(config_dir / "tools.yaml")
    merged = {
        **config_data,
        "policies": policies_data,
        "tools": tools_data,
    }
    return AppConfig.model_validate(merged)
