"""Named configuration base class."""

import json
from abc import ABC
from pathlib import Path
from typing import Self, cast

import yaml
from pydantic_settings import (
    BaseSettings,
    InitSettingsSource,
    JsonConfigSettingsSource,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
    YamlConfigSettingsSource,
)

# MARK: Settings
# =============================================================================


class BaseAppSettings(BaseSettings, ABC):
    model_config = SettingsConfigDict(
        env_prefix="KBM_",
        env_nested_delimiter="__",
        env_file=[".env", ".kbm.env"],
        extra="ignore",
    )

    # Serialization

    def dump(self, full: bool = False) -> dict:
        """Dump configuration as dict, optionally including defaults."""
        return self.model_dump(
            mode="json",
            exclude_computed_fields=not full,
            exclude_defaults=not full,
        )

    # Deserialization

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

        # Used by file-based config models to load from files
        json_file: Path | None = init_src.init_kwargs.pop("_json_file", None)
        yaml_file: Path | None = init_src.init_kwargs.pop("_yaml_file", None)

        # Priority: init > env > dotenv > json > yaml > file secrets
        return (
            init_settings,
            env_settings,
            dotenv_settings,
            JsonConfigSettingsSource(settings_cls, json_file=json_file),
            YamlConfigSettingsSource(settings_cls, yaml_file=yaml_file),
            file_secret_settings,
        )


# MARK: Configuration
# =============================================================================


class BaseAppConfig(BaseAppSettings, ABC):
    # Serialization

    def dump_json(self, full: bool = False) -> str:
        """Dump configuration as JSON string."""
        return json.dumps(self.dump(full=full), indent=2)

    def dump_yaml(self, full: bool = False) -> str:
        """Dump configuration as YAML string."""
        return yaml.dump(self.dump(full=full), sort_keys=False)

    # Deserialization

    @classmethod
    def _from_file(cls, path: Path, **kwargs) -> Self:
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {path}")

        match path.suffix.lower():
            case ".json":
                json_file, yaml_file = path, None
            case ".yaml" | ".yml":
                json_file, yaml_file = None, path
            case _:
                raise ValueError(f"Unsupported file format: {path}")

        return cls(
            _json_file=json_file,  # type: ignore[call-arg]
            _yaml_file=yaml_file,  # type: ignore[call-arg]
            **kwargs,
        )
