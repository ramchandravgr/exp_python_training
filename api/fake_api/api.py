"""
Main entry point for the Fake Enterprise API.

Students should only need to instantiate FakeAPI and then use the
resource collections (customers, applications, cases, alerts).
"""

from __future__ import annotations

from .config import APIConfig
from .resources.alerts import AlertsResource
from .resources.applications import ApplicationsResource
from .resources.cases import CasesResource
from .resources.customers import CustomersResource


class FakeAPI:
    """
    Main SDK class.

    Example:
        api = FakeAPI(api_key="training-key")

        response = api.customers.list(
            page=1,
            page_size=25,
        )
    """

    def __init__(
        self,
        api_key: str = "",
    ) -> None:
        # Server configuration
        self.config = APIConfig(
            client_api_key=api_key,
        )

        # Resources
        self.customers = CustomersResource(self.config)
        self.applications = ApplicationsResource(self.config)
        self.cases = CasesResource(self.config)
        self.alerts = AlertsResource(self.config)

    def __repr__(self) -> str:
        return (
            f"<FakeAPI "
            f"authenticated={self.config.client_api_key == self.config.expected_api_key}>"
        )
