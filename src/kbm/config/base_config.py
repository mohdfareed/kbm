"""Named configuration base class."""

import json
from abc import ABC
from pathlib import Path
from typing import Self, cast

import yaml
from pydantic import Field
from pydantic_settings import (
    BaseSettings,
    InitSettingsSource,
    JsonConfigSettingsSource,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
    YamlConfigSettingsSource,
)


class BaseConfig(BaseSettings, ABC):
    model_config = SettingsConfigDict(
        env_prefix="KBM_",
        env_nested_delimiter="__",
        env_file=".env",
        extra="ignore",
    )

    # MARK: Serialization

    def dump(self, full: bool = False) -> dict:
        """Dump configuration as dict, optionally including defaults."""
        return self.model_dump(
            mode="json",
            exclude_computed_fields=not full,
            exclude_defaults=not full,
        )

    def dump_json(self, full: bool = False) -> str:
        """Dump configuration as JSON string."""
        return json.dumps(self.dump(full=full), indent=2)

    def dump_yaml(self, full: bool = False) -> str:
        """Dump configuration as YAML string."""
        return yaml.dump(self.dump(full=full), sort_keys=False)

    # MARK: Deserialization

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

        yaml_file: Path | None = init_src.init_kwargs.pop("_yaml_file", None)
        json_file: Path | None = init_src.init_kwargs.pop("_json_file", None)

        # Priority: init > env > dotenv (.env) > yaml > json > file secrets
        return (
            init_settings,
            env_settings,
            dotenv_settings,
            YamlConfigSettingsSource(settings_cls, yaml_file=yaml_file),
            JsonConfigSettingsSource(settings_cls, json_file=json_file),
            file_secret_settings,
        )


class NamedFileConfig(BaseConfig, ABC):
    name: str
    """Unique name for this configuration."""
    file_path: Path = Field(..., exclude=True)
    """Path to the configuration file."""

    # MARK: Loading

    @classmethod
    def from_file(cls, config: Path, **kwargs) -> Self:
        """Load configuration from file path."""
        if not config.exists():
            raise FileNotFoundError(f"Config not found: {config}")

        match config.suffix.lower():
            case ".json":
                json_file, yaml_file = config, None
            case ".yaml" | ".yml":
                json_file, yaml_file = None, config
            case _:
                raise ValueError(f"Unsupported config file format: {config}")

        return cls(
            file_path=config,
            _yaml_file=yaml_file,  # type: ignore[call-arg]
            _json_file=json_file,  # type: ignore[call-arg]
            **kwargs,
        )

    @classmethod
    def from_name(cls, name: str, **kwargs) -> Self:
        from kbm.config.app_settings import app_settings

        for config in app_settings.memories:
            try:
                cfg = cls.from_file(config, **kwargs)
            except Exception as e:
                from kbm.config import app_settings

                app_settings.logger.warning(
                    f"Failed to load config '{config.name}': {e}", exc_info=True
                )
                continue  # skip invalid config files

            if cfg.name == name:
                return cfg

        raise FileNotFoundError(f"Memory not found: {name}")
