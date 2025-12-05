"""
Application Settings and Configuration

Loads environment variables and provides centralized configuration
for the Formula Student AI Pipeline.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional
from pathlib import Path


class Settings(BaseSettings):
    """Application configuration loaded from environment variables"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # ============================================================================
    # GOOGLE CLOUD PLATFORM
    # ============================================================================

    google_cloud_project: str = ""
    google_application_credentials: Optional[str] = None
    vertex_ai_location: str = "us-central1"

    # ============================================================================
    # GEMINI API
    # ============================================================================

    gemini_api_key: str = ""

    # Model names
    gemini_pro_model: str = "gemini-3.0-pro"
    gemini_flash_model: str = "gemini-2.5-flash"
    embedding_model: str = "text-embedding-004"

    # ============================================================================
    # VECTOR STORE
    # ============================================================================

    vector_search_index_id: str = ""
    vector_search_endpoint: str = ""

    # ============================================================================
    # APPLICATION
    # ============================================================================

    app_env: str = "development"
    debug: bool = True
    log_level: str = "INFO"

    # ============================================================================
    # API CONFIGURATION
    # ============================================================================

    api_host: str = "0.0.0.0"
    api_port: int = 8000
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:5173"]

    # ============================================================================
    # RAG CONFIGURATION
    # ============================================================================

    chunk_size: int = 2000
    chunk_overlap: int = 200
    top_k_retrieval: int = 5
    rerank_enabled: bool = True

    # ============================================================================
    # FORMULA STUDENT RULES
    # ============================================================================

    fsa_handbook_path: str = "data/raw/FSA-Competition-Handbook-2025-version-1.3.0-8jmtzk3ybtb5j86b98z119ekyo.pdf"
    fs_rules_path: str = "data/raw/FS-Rules_2025_v1.1-opt973ooyjn77k8smjqu8ec4ur.pdf"

    # ============================================================================
    # CACHE SETTINGS
    # ============================================================================

    enable_cache: bool = True
    cache_ttl_seconds: int = 3600

    # ============================================================================
    # COMPUTED PROPERTIES
    # ============================================================================

    @property
    def base_dir(self) -> Path:
        """Get the base directory of the project"""
        return Path(__file__).parent.parent

    @property
    def fsa_handbook_full_path(self) -> Path:
        """Get full path to FSA Handbook"""
        return self.base_dir / self.fsa_handbook_path

    @property
    def fs_rules_full_path(self) -> Path:
        """Get full path to FS Rules"""
        return self.base_dir / self.fs_rules_path

    @property
    def is_production(self) -> bool:
        """Check if running in production"""
        return self.app_env == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development"""
        return self.app_env == "development"


# ============================================================================
# GLOBAL SETTINGS INSTANCE
# ============================================================================

settings = Settings()


# ============================================================================
# VALIDATION
# ============================================================================

def validate_settings() -> List[str]:
    """
    Validates critical settings and returns list of errors.

    Returns:
        List of error messages (empty if all valid)
    """
    errors = []

    # Check API keys
    if not settings.gemini_api_key and not settings.google_cloud_project:
        errors.append("Either GEMINI_API_KEY or GOOGLE_CLOUD_PROJECT must be set")

    # Check PDF files exist
    if not settings.fsa_handbook_full_path.exists():
        errors.append(f"FSA Handbook not found at {settings.fsa_handbook_full_path}")

    if not settings.fs_rules_full_path.exists():
        errors.append(f"FS Rules not found at {settings.fs_rules_full_path}")

    # Check chunk size is reasonable
    if settings.chunk_size < 100:
        errors.append("CHUNK_SIZE too small (minimum 100)")

    if settings.chunk_size > 10000:
        errors.append("CHUNK_SIZE too large (maximum 10000)")

    return errors


def print_settings_summary():
    """Prints a summary of current settings (safe, no secrets)"""
    print("=" * 60)
    print("Formula Student AI Pipeline - Configuration Summary")
    print("=" * 60)
    print(f"Environment: {settings.app_env}")
    print(f"Debug Mode: {settings.debug}")
    print(f"Log Level: {settings.log_level}")
    print(f"API Host: {settings.api_host}:{settings.api_port}")
    print(f"\nModels:")
    print(f"  - Reasoning: {settings.gemini_pro_model}")
    print(f"  - Router: {settings.gemini_flash_model}")
    print(f"  - Embeddings: {settings.embedding_model}")
    print(f"\nRAG Configuration:")
    print(f"  - Chunk Size: {settings.chunk_size}")
    print(f"  - Chunk Overlap: {settings.chunk_overlap}")
    print(f"  - Top-K Retrieval: {settings.top_k_retrieval}")
    print(f"  - Reranking: {'Enabled' if settings.rerank_enabled else 'Disabled'}")
    print(f"\nDocuments:")
    print(f"  - FSA Handbook: {'✓' if settings.fsa_handbook_full_path.exists() else '✗'}")
    print(f"  - FS Rules: {'✓' if settings.fs_rules_full_path.exists() else '✗'}")

    # Check for errors
    errors = validate_settings()
    if errors:
        print(f"\n⚠️  Configuration Errors:")
        for error in errors:
            print(f"  - {error}")
    else:
        print(f"\n✓ Configuration valid")

    print("=" * 60)
