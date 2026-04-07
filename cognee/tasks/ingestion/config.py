from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class IngestionConfig(BaseSettings):
    dlt_max_rows_per_table: int = 50
    ignored_directory_names: str = ""

    model_config = SettingsConfigDict(env_file=".env", extra="allow")

    def get_ignored_directory_names(self) -> set[str]:
        return {
            directory_name.strip()
            for directory_name in self.ignored_directory_names.split(",")
            if directory_name.strip()
        }

    def to_dict(self) -> dict:
        return {
            "dlt_max_rows_per_table": self.dlt_max_rows_per_table,
            "ignored_directory_names": self.ignored_directory_names,
        }


@lru_cache
def get_ingestion_config():
    return IngestionConfig()
