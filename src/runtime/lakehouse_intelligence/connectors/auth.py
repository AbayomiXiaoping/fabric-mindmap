"""Microsoft Entra ID authentication manager for Microsoft Fabric APIs."""

from __future__ import annotations

from typing import Any, Optional
from azure.core.credentials import TokenCredential
from azure.identity import (
    AzureCliCredential,
    ClientSecretCredential,
    DefaultAzureCredential,
    DeviceCodeCredential,
    InteractiveBrowserCredential,
)
from pydantic import BaseModel

from lakehouse_intelligence.config import settings
from lakehouse_intelligence.logging.logger import get_logger

logger = get_logger("fabric_auth")

FABRIC_SCOPE = "https://api.fabric.microsoft.com/.default"
ONELAKE_SCOPE = "https://storage.azure.com/.default"


class AuthStatus(BaseModel):
    is_authenticated: bool
    auth_method: str
    tenant_id: Optional[str] = None
    account_name: Optional[str] = None
    token_expiry: Optional[str] = None
    error: Optional[str] = None


class FabricAuthManager:
    """Manages Microsoft Entra ID token acquisition across interactive and non-interactive flows."""

    def __init__(self):
        self._credential: Optional[TokenCredential] = None
        self._auth_method: str = "none"
        self._cached_status: Optional[AuthStatus] = None

    def configure_credentials(
        self,
        method: str = "default",
        tenant_id: Optional[str] = None,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
    ) -> None:
        """Sets up the token credential based on the chosen authentication strategy."""
        t_id = tenant_id or settings.fabric_tenant_id
        self._auth_method = method

        if method == "client_secret" and client_id and client_secret and t_id:
            logger.info("Configured Service Principal (ClientSecretCredential)")
            self._credential = ClientSecretCredential(
                tenant_id=t_id,
                client_id=client_id,
                client_secret=client_secret,
            )
        elif method == "azure_cli":
            logger.info("Configured Azure CLI Credential")
            self._credential = AzureCliCredential(tenant_id=t_id)
        elif method == "interactive_browser":
            logger.info("Configured Interactive Browser Credential")
            self._credential = InteractiveBrowserCredential(tenant_id=t_id)
        elif method == "device_code":
            logger.info("Configured Device Code Credential")
            self._credential = DeviceCodeCredential(tenant_id=t_id)
        else:
            logger.info("Configured DefaultAzureCredential fallback chain")
            self._credential = DefaultAzureCredential(
                exclude_interactive_browser_credential=True,
                shared_cache_tenant_id=t_id,
            )

    def get_credential(self) -> TokenCredential:
        if not self._credential:
            self.configure_credentials()
        return self._credential

    async def get_access_token(self, scope: str = FABRIC_SCOPE) -> str:
        """Acquires a valid Bearer token for the requested Fabric / OneLake scope."""
        cred = self.get_credential()
        token = cred.get_token(scope)
        return token.token

    async def verify_authentication(self) -> AuthStatus:
        """Attempts to obtain a token to verify credentials without logging the token itself."""
        try:
            cred = self.get_credential()
            token = cred.get_token(FABRIC_SCOPE)
            status = AuthStatus(
                is_authenticated=True,
                auth_method=self._auth_method,
                tenant_id=settings.fabric_tenant_id,
                token_expiry=str(token.expires_on),
            )
            self._cached_status = status
            return status
        except Exception as e:
            logger.warn(f"Authentication verification failed: {e}")
            status = AuthStatus(
                is_authenticated=False,
                auth_method=self._auth_method,
                error=str(e),
            )
            self._cached_status = status
            return status

