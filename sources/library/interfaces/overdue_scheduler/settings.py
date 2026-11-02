from pydantic_settings import BaseSettings


class OverdueSchedulerSettings(BaseSettings):
    OVERDUE_CRON: str = '0 9 * * *'
