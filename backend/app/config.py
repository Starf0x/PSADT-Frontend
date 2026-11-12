from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="PSADT_", env_file=".env", extra="ignore")

    data_dir: Path = Path("./data")
    static_dir: Path = Path("../frontend/dist")
    admin_username: str = "admin"
    admin_password: str | None = None
    # Zet op false voor lokaal testen zonder HTTPS
    cookie_secure: bool = True
    session_hours: int = 12
    max_failed_logins: int = 5
    lockout_minutes: int = 15
    max_upload_mb: int = 4096
    pwsh_path: str = "pwsh"
    # Officiële PSAppDeployToolkit_Template_v4.zip (wordt in Docker/LXC automatisch gedownload)
    toolkit_zip: Path = Path("/opt/psadt/PSAppDeployToolkit_Template_v4.zip")

    @property
    def db_url(self) -> str:
        return f"sqlite:///{self.data_dir / 'psadt.db'}"


settings = Settings()
