from typing import Optional, Tuple
from app.common.context import AppContext
from app.common.middleware.logger import Logger
from app.core.strategy.base_sso import BaseSSOStrategy

logger = Logger()


class FacebookSSOStrategy(BaseSSOStrategy):
    def get_auth_url(self, ctx: AppContext) -> Tuple[str, str]:
        logger.error("Not Implemented")
        raise NotImplementedError("Not Implemented")

    def callback(
        self, code: str, state: str, state_cookie: str | None, ctx: AppContext
    ) -> Optional[dict]:
        logger.error("Not Implemented")
        raise NotImplementedError("Not Implemented")
