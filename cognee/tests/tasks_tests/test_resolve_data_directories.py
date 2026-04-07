import asyncio
import os
import tempfile
from unittest.mock import patch

from cognee.tasks.ingestion.config import get_ingestion_config
from cognee.tasks.ingestion.resolve_data_directories import resolve_data_directories


def test_resolve_data_directories_skips_hidden_paths():
    with patch.dict(os.environ, {"IGNORED_DIRECTORY_NAMES": ".git,.venv"}):
        get_ingestion_config.cache_clear()
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                top_level_path = os.path.join(temp_dir, "top.txt")
                hidden_path = os.path.join(temp_dir, ".DS_Store")
                nested_dir = os.path.join(temp_dir, "nested")
                nested_path = os.path.join(nested_dir, "child.md")
                git_dir = os.path.join(temp_dir, ".git")
                git_nested_path = os.path.join(git_dir, "config")
                venv_dir = os.path.join(temp_dir, ".venv")
                venv_nested_path = os.path.join(venv_dir, "pyvenv.cfg")

                os.mkdir(nested_dir)
                os.mkdir(git_dir)
                os.mkdir(venv_dir)

                with open(top_level_path, "w", encoding="utf-8") as file_handle:
                    file_handle.write("top")
                with open(hidden_path, "w", encoding="utf-8") as file_handle:
                    file_handle.write("hidden")
                with open(nested_path, "w", encoding="utf-8") as file_handle:
                    file_handle.write("child")
                with open(git_nested_path, "w", encoding="utf-8") as file_handle:
                    file_handle.write("ignored")
                with open(venv_nested_path, "w", encoding="utf-8") as file_handle:
                    file_handle.write("ignored")

                resolved_files = asyncio.run(resolve_data_directories(temp_dir))

                assert set(resolved_files) == {top_level_path, nested_path}
        finally:
            get_ingestion_config.cache_clear()
