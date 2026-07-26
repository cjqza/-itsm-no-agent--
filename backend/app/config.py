from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "公司桌面IT服务台"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    SECRET_KEY: str = "change-this-to-a-random-secret-key-in-production"

    # Database (默认SQLite，无需安装MySQL)
    DB_TYPE: str = "sqlite"  # sqlite 或 mysql
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_USER: str = "root"
    DB_PASSWORD: str = ""
    DB_NAME: str = "it_ops"

    @property
    def DATABASE_URL(self) -> str:
        if self.DB_TYPE == "sqlite":
            return "sqlite+aiosqlite:///./it_ops.db"
        return f"mysql+aiomysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}?charset=utf8mb4"

    @property
    def SYNC_DATABASE_URL(self) -> str:
        if self.DB_TYPE == "sqlite":
            return "sqlite:///./it_ops.db"
        return f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}?charset=utf8mb4"

    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0

    @property
    def REDIS_URL(self) -> str:
        if not self.REDIS_HOST:
            return ""
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    # Feishu
    FEISHU_APP_ID: str = ""
    FEISHU_APP_SECRET: str = ""
    FEISHU_VERIFICATION_TOKEN: str = ""
    FEISHU_ENCRYPT_KEY: str = ""
    FEISHU_BOT_NAME: str = "IT服务台助手"

    # JWT
    JWT_SECRET_KEY: str = "jwt-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 480  # 8 hours

    # Security
    TRUST_PROXY: bool = False  # 是否信任 X-Forwarded-For 头（生产环境反向代理后设为 True）

    # CORS
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:5174,http://localhost:5175,http://localhost:5176"

    # SLA Default (hours)
    DEFAULT_SLA_HOURS: int = 4
    SLA_WARNING_PERCENT: int = 50  # 超过50%变红色
    ACCEPT_TIMEOUT_MINUTES: int = 5  # 5分钟未接单超时
    PENDING_SLA_YELLOW_MINUTES: int = 10  # 待接单SLA变黄（分钟）
    PENDING_SLA_RED_MINUTES: int = 20     # 待接单SLA变红（分钟）
    PENDING_SLA_BLACK_MINUTES: int = 30   # 待接单SLA超时（分钟）

    # Frontend
    FRONTEND_URL: str = "http://localhost:5173"

    # AI / RAG
    AI_EMBEDDING_PROVIDER: str = "bge"  # bge 或 openai
    AI_EMBEDDING_MODEL: str = "BAAI/bge-small-zh-v1.5"
    AI_EMBEDDING_API_KEY: str = ""
    AI_EMBEDDING_BASE_URL: str = "https://api.openai.com/v1"
    AI_EMBEDDING_DIMENSION: int = 512

    AI_LLM_PROVIDER: str = "deepseek"  # deepseek 或 gguf
    AI_LLM_MODEL_PATH: str = ""  # GGUF 模型路径
    AI_LLM_API_KEY: str = ""
    AI_LLM_BASE_URL: str = "https://api.deepseek.com"
    AI_LLM_MODEL_NAME: str = "deepseek-chat"
    AI_LLM_MAX_TOKENS: int = 1024
    AI_LLM_TEMPERATURE: float = 0.7

    AI_VECTORSTORE_PATH: str = "./chroma_db"
    AI_RAG_TOP_K: int = 5
    AI_RAG_SCORE_THRESHOLD: float = 0.5
    AI_RAG_MAX_HISTORY_TURNS: int = 5

    AI_RATE_LIMIT_PER_MINUTE: int = 20  # AI 聊天限流

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
