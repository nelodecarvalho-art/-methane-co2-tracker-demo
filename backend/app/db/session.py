from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker


class Settings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")

    db_user: str
    db_password: str
    db_name: str
    db_host: str = "localhost"
    db_port: int = 5432

    mqtt_broker_host: str = "localhost"
    mqtt_broker_port: int = 1883
    mqtt_topic_pattern: str = "sensors/+/readings"
    mqtt_username: str = ""
    mqtt_password: str = ""
    mqtt_use_tls: bool = False

    alert_window_seconds: int = 120
    alert_threshold_ppm_ch4: float = 500.0
    alert_threshold_ppm_co2: float = 5000.0

    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 480

    smtp_host: str = "localhost"
    smtp_port: int = 1025
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_use_tls: bool = False
    alert_email_from: str = "alerts@methane-co2-tracker.local"
    alert_email_to: str = "oncall@methane-co2-tracker.local"

    # Provedores de nuvem (Render incluso) costumam bloquear saída na porta
    # 587 por padrão anti-spam — SMTP puro trava em timeout de conexão TCP,
    # nunca chega a negociar. Quando True, usa a API HTTP do Resend
    # (porta 443) em vez de smtplib. `smtp_password` é reaproveitado como
    # API key do Resend (é o mesmo valor usado como senha SMTP na
    # integração deles). Default False não afeta o Mailpit local.
    use_resend_http_api: bool = False
    alert_webhook_url: str = ""

    # Isolation Forest por sensor+gás, treinado sob demanda a cada leitura
    # com o histórico recente (ver app/anomaly/detector.py).
    anomaly_min_history: int = 50
    anomaly_history_limit: int = 500
    anomaly_contamination: float = 0.02

    # Vazio = desabilitado. Separado do alert_webhook_url pois anomalia é
    # severidade menor que o alerta de segurança — pode valer a pena rotear
    # para um sistema diferente (ex: manutenção, não escalonamento de risco).
    anomaly_webhook_url: str = ""

    # Lista separada por vírgula. Usado pelo CORSMiddleware da API pro
    # dashboard (origem diferente, ex: localhost:5173) poder chamar a API.
    cors_allowed_origins: str = "http://localhost:5173"

    @property
    def cors_allowed_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_allowed_origins.split(",") if o.strip()]

    @property
    def alert_thresholds_ppm(self) -> dict[str, float]:
        return {"CH4": self.alert_threshold_ppm_ch4, "CO2": self.alert_threshold_ppm_co2}

    # Parâmetros extras de conexão (ex: "sslmode=require&channel_binding=require"
    # exigidos por hosts gerenciados como Neon). Vazio = nenhum, comportamento
    # local/docker-compose inalterado.
    db_extra_query: str = ""

    @property
    def database_url(self) -> str:
        base = (
            f"postgresql+psycopg2://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )
        return f"{base}?{self.db_extra_query}" if self.db_extra_query else base


settings = Settings()
engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
