""" "Application configuration core."""

import json
from pathlib import Path
from typing import Self, cast

import yaml
from pydantic import Field
from pydantic_settings import (
    BaseSettings,
    DotEnvSettingsSource,
    InitSettingsSource,
    JsonConfigSettingsSource,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
    YamlConfigSettingsSource,
)

from .app_settings import KBM_ENV_BASE


class AppConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix=KBM_ENV_BASE,
        env_nested_delimiter="__",
        env_file=".env",
        extra="ignore",
    )

    file_path: Path = Field(..., exclude=True)
    """Path to the config file."""

    @classmethod
    def from_config(cls, config: Path) -> Self:
        config = config.expanduser().resolve()
        if not config.exists():
            raise FileNotFoundError(f"Config not found: {config}")

        return cls(
            file_path=config,
            _yaml_file=config,  # type: ignore[call-arg]
            _json_file=config.with_suffix(".json"),  # type: ignore[call-arg]
            _env_file=config.with_suffix(".env"),  # type: ignore[call-arg]
        )

    def dump(self, full: bool = False) -> dict:
        return self.model_dump(
            mode="json",
            exclude_computed_fields=True,
            exclude_defaults=not full,
        )

    def dump_json(self, full: bool = False) -> str:
        return json.dumps(self.dump(full=full), indent=2)

    def dump_yaml(self, full: bool = False) -> str:
        return yaml.dump(self.dump(full=full), sort_keys=False)

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        init_src = cast(InitSettingsSource, init_settings)

        env_file: Path | None = init_src.init_kwargs.pop("_env_file", None)
        yaml_file: Path | None = init_src.init_kwargs.pop("_yaml_file", None)
        json_file: Path | None = init_src.init_kwargs.pop("_json_file", None)

        # Priority: init > env > dotenv > config files > secrets
        return (
            init_settings,
            env_settings,
            dotenv_settings,
            DotEnvSettingsSource(settings_cls, env_file=env_file),
            YamlConfigSettingsSource(settings_cls, yaml_file=yaml_file),
            JsonConfigSettingsSource(settings_cls, json_file=json_file),
            file_secret_settings,
        )
