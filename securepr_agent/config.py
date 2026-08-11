import os
from dataclasses import dataclass
from typing import Dict


def _int(name: str, default: int) -> int:
    value = int(os.getenv(name, str(default)))
    if value <= 0:
        raise ValueError("%s must be positive" % name)
    return value


def _bool(name: str, default: bool = False) -> bool:
    return os.getenv(name, str(default)).strip().lower() in {"1", "true", "yes", "on"}


def _non_negative_int(name: str, default: int) -> int:
    value = int(os.getenv(name, str(default)))
    if value < 0:
        raise ValueError("%s must be non-negative" % name)
    return value


@dataclass(frozen=True)
class Settings:
    host: str
    port: int
    db_path: str
    max_diff_bytes: int
    max_steps: int
    timeout_seconds: int
    llm_base_url: str
    llm_api_key: str
    llm_model: str
    github_webhook_secret: str
    github_token: str
    auto_post_review: bool
    database_url: str = ""
    redis_url: str = ""
    async_workers: int = 2
    skills_dir: str = "skills"
    github_app_id: str = ""
    github_app_slug: str = ""
    github_private_key_path: str = ""
    public_base_url: str = "http://127.0.0.1:8080"
    llm_provider: str = "local"
    deepseek_api_key: str = ""
    openrouter_api_key: str = ""
    openrouter_site_url: str = ""
    openrouter_app_name: str = "SecurePR Agent"
    eval_max_cases: int = 5
    eval_min_cases: int = 3
    eval_min_improvement: float = 0.01
    eval_min_holdout_cases: int = 2
    eval_max_metric_regression: float = 0.0
    auth_required: bool = False
    auth_secret: str = ""
    bootstrap_admin_username: str = ""
    bootstrap_admin_password: str = ""
    default_tenant_id: str = "default"
    session_ttl_seconds: int = 3600
    webhook_max_age_seconds: int = 600
    queue_max_attempts: int = 3
    queue_lease_seconds: int = 60
    skill_timeout_seconds: int = 30
    skill_memory_mb: int = 256
    skill_sandbox: bool = True
    skill_signing_key: str = ""
    skill_container_image: str = ""
    repair_test_command: str = ""
    repair_verify_timeout_seconds: int = 120
    otel_endpoint: str = ""
    otel_service_name: str = "securepr"
    alert_failure_rate: float = 0.20
    alert_min_samples: int = 10
    alert_window_seconds: int = 900
    alert_webhook_url: str = ""
    alert_smtp_host: str = ""
    alert_email_to: str = ""
    continuous_eval_seconds: int = 0

    def resolved_llm(self) -> Dict[str, object]:
        """Resolve a named provider to the existing OpenAI-compatible transport."""
        provider = self.llm_provider.strip().lower()
        if provider in {"", "local", "none"}:
            if self.llm_base_url or self.llm_api_key or self.llm_model:
                provider = "custom"
            else:
                return {}

        if provider == "deepseek":
            api_key = self.deepseek_api_key or self.llm_api_key
            if not api_key:
                raise ValueError("DeepSeek requires SECUREPR_DEEPSEEK_API_KEY")
            return {
                "provider": "deepseek",
                "base_url": self.llm_base_url or "https://api.deepseek.com",
                "api_key": api_key,
                "model": self.llm_model or "deepseek-v4-flash",
                "headers": {},
            }

        if provider in {"openrouter-deepseek-free", "openrouter_deepseek_free"}:
            api_key = self.openrouter_api_key or self.llm_api_key
            if not api_key:
                raise ValueError("OpenRouter requires SECUREPR_OPENROUTER_API_KEY")
            headers = {}
            if self.openrouter_site_url:
                headers["HTTP-Referer"] = self.openrouter_site_url
            if self.openrouter_app_name:
                headers["X-Title"] = self.openrouter_app_name
            return {
                "provider": "openrouter-deepseek-free",
                "base_url": self.llm_base_url or "https://openrouter.ai/api/v1",
                "api_key": api_key,
                "model": self.llm_model or "deepseek/deepseek-chat-v3-0324:free",
                "headers": headers,
            }

        if provider == "openrouter-free":
            api_key = self.openrouter_api_key or self.llm_api_key
            if not api_key:
                raise ValueError("OpenRouter requires SECUREPR_OPENROUTER_API_KEY")
            headers = {}
            if self.openrouter_site_url:
                headers["HTTP-Referer"] = self.openrouter_site_url
            if self.openrouter_app_name:
                headers["X-Title"] = self.openrouter_app_name
            return {
                "provider": "openrouter-free",
                "base_url": self.llm_base_url or "https://openrouter.ai/api/v1",
                "api_key": api_key,
                "model": self.llm_model or "openrouter/free",
                "headers": headers,
            }

        if provider == "custom":
            if not (self.llm_base_url and self.llm_api_key and self.llm_model):
                raise ValueError(
                    "Custom LLM requires SECUREPR_LLM_BASE_URL, "
                    "SECUREPR_LLM_API_KEY and SECUREPR_LLM_MODEL"
                )
            return {
                "provider": "custom",
                "base_url": self.llm_base_url,
                "api_key": self.llm_api_key,
                "model": self.llm_model,
                "headers": {},
            }
        raise ValueError("unsupported SECUREPR_LLM_PROVIDER: %s" % self.llm_provider)

    def validate_evolution(self) -> None:
        if self.eval_min_cases > self.eval_max_cases:
            raise ValueError("SECUREPR_EVAL_MIN_CASES cannot exceed SECUREPR_EVAL_MAX_CASES")
        if not 0.0 <= self.eval_min_improvement <= 1.0:
            raise ValueError("SECUREPR_EVAL_MIN_IMPROVEMENT must be between 0 and 1")
        if self.eval_min_holdout_cases > self.eval_max_cases:
            raise ValueError("SECUREPR_EVAL_MIN_HOLDOUT_CASES cannot exceed SECUREPR_EVAL_MAX_CASES")
        if not 0.0 <= self.eval_max_metric_regression <= 1.0:
            raise ValueError("SECUREPR_EVAL_MAX_METRIC_REGRESSION must be between 0 and 1")
        if self.auth_required and len(self.auth_secret.encode("utf-8")) < 32:
            raise ValueError(
                "SECUREPR_AUTH_SECRET must contain at least 32 bytes when authentication is enabled"
            )
        if bool(self.bootstrap_admin_username) != bool(self.bootstrap_admin_password):
            raise ValueError("bootstrap admin username and password must be configured together")
        if not 0.0 <= self.alert_failure_rate <= 1.0:
            raise ValueError("SECUREPR_ALERT_FAILURE_RATE must be between 0 and 1")

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            host=os.getenv("SECUREPR_HOST", "127.0.0.1"),
            port=_int("SECUREPR_PORT", 8080),
            db_path=os.getenv("SECUREPR_DB_PATH", "securepr.db"),
            max_diff_bytes=_int("SECUREPR_MAX_DIFF_BYTES", 1024 * 1024),
            max_steps=_int("SECUREPR_MAX_STEPS", 8),
            timeout_seconds=_int("SECUREPR_TIMEOUT_SECONDS", 120),
            llm_base_url=os.getenv("SECUREPR_LLM_BASE_URL", "").rstrip("/"),
            llm_api_key=os.getenv("SECUREPR_LLM_API_KEY", ""),
            llm_model=os.getenv("SECUREPR_LLM_MODEL", ""),
            github_webhook_secret=os.getenv("SECUREPR_GITHUB_WEBHOOK_SECRET", ""),
            github_token=os.getenv("SECUREPR_GITHUB_TOKEN", ""),
            auto_post_review=_bool("SECUREPR_AUTO_POST_REVIEW"),
            database_url=os.getenv("SECUREPR_DATABASE_URL", ""),
            redis_url=os.getenv("SECUREPR_REDIS_URL", ""),
            async_workers=_int("SECUREPR_ASYNC_WORKERS", 2),
            skills_dir=os.getenv("SECUREPR_SKILLS_DIR", "skills"),
            github_app_id=os.getenv("SECUREPR_GITHUB_APP_ID", ""),
            github_app_slug=os.getenv("SECUREPR_GITHUB_APP_SLUG", ""),
            github_private_key_path=os.getenv("SECUREPR_GITHUB_PRIVATE_KEY_PATH", ""),
            public_base_url=os.getenv("SECUREPR_PUBLIC_BASE_URL", "http://127.0.0.1:8080").rstrip("/"),
            llm_provider=os.getenv("SECUREPR_LLM_PROVIDER", "local"),
            deepseek_api_key=os.getenv("SECUREPR_DEEPSEEK_API_KEY", ""),
            openrouter_api_key=os.getenv("SECUREPR_OPENROUTER_API_KEY", ""),
            openrouter_site_url=os.getenv("SECUREPR_OPENROUTER_SITE_URL", ""),
            openrouter_app_name=os.getenv("SECUREPR_OPENROUTER_APP_NAME", "SecurePR Agent"),
            eval_max_cases=_int("SECUREPR_EVAL_MAX_CASES", 5),
            eval_min_cases=_int("SECUREPR_EVAL_MIN_CASES", 3),
            eval_min_improvement=float(os.getenv("SECUREPR_EVAL_MIN_IMPROVEMENT", "0.01")),
            eval_min_holdout_cases=_non_negative_int("SECUREPR_EVAL_MIN_HOLDOUT_CASES", 2),
            eval_max_metric_regression=float(
                os.getenv("SECUREPR_EVAL_MAX_METRIC_REGRESSION", "0")
            ),
            auth_required=_bool("SECUREPR_AUTH_REQUIRED", True),
            auth_secret=os.getenv("SECUREPR_AUTH_SECRET", ""),
            bootstrap_admin_username=os.getenv("SECUREPR_BOOTSTRAP_ADMIN_USERNAME", ""),
            bootstrap_admin_password=os.getenv("SECUREPR_BOOTSTRAP_ADMIN_PASSWORD", ""),
            default_tenant_id=os.getenv("SECUREPR_DEFAULT_TENANT_ID", "default"),
            session_ttl_seconds=_int("SECUREPR_SESSION_TTL_SECONDS", 3600),
            webhook_max_age_seconds=_int("SECUREPR_WEBHOOK_MAX_AGE_SECONDS", 600),
            queue_max_attempts=_int("SECUREPR_QUEUE_MAX_ATTEMPTS", 3),
            queue_lease_seconds=_int("SECUREPR_QUEUE_LEASE_SECONDS", 60),
            skill_timeout_seconds=_int("SECUREPR_SKILL_TIMEOUT_SECONDS", 30),
            skill_memory_mb=_int("SECUREPR_SKILL_MEMORY_MB", 256),
            skill_sandbox=_bool("SECUREPR_SKILL_SANDBOX", True),
            skill_signing_key=os.getenv("SECUREPR_SKILL_SIGNING_KEY", ""),
            skill_container_image=os.getenv("SECUREPR_SKILL_CONTAINER_IMAGE", ""),
            repair_test_command=os.getenv("SECUREPR_REPAIR_TEST_COMMAND", ""),
            repair_verify_timeout_seconds=_int("SECUREPR_REPAIR_VERIFY_TIMEOUT_SECONDS", 120),
            otel_endpoint=os.getenv("SECUREPR_OTEL_ENDPOINT", ""),
            otel_service_name=os.getenv("SECUREPR_OTEL_SERVICE_NAME", "securepr"),
            alert_failure_rate=float(os.getenv("SECUREPR_ALERT_FAILURE_RATE", "0.20")),
            alert_min_samples=_int("SECUREPR_ALERT_MIN_SAMPLES", 10),
            alert_window_seconds=_int("SECUREPR_ALERT_WINDOW_SECONDS", 900),
            alert_webhook_url=os.getenv("SECUREPR_ALERT_WEBHOOK_URL", ""),
            alert_smtp_host=os.getenv("SECUREPR_ALERT_SMTP_HOST", ""),
            alert_email_to=os.getenv("SECUREPR_ALERT_EMAIL_TO", ""),
            continuous_eval_seconds=_non_negative_int(
                "SECUREPR_CONTINUOUS_EVAL_SECONDS", 0
            ),
        )
