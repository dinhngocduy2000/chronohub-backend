from uuid import uuid4
from app.common.context import AppContext
from app.common.enum.context_actions import FACEBOOK_AUTHENTICATE, GOOGLE_AUTHENTICATE
from app.common.enum.sso_providers import SSO_PROVIDERS
from app.core.sso_providers.base_sso import BaseSSOStrategy
from app.core.sso_providers.facebook_sso import FacebookSSOStrategy
from app.core.sso_providers.google_sso import GoogleSSOStrategy
