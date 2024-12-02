import logging
from typing import List, Literal, Optional
from urllib.parse import urljoin

import requests
from requests import Session

from .models import (
    Adapters,
    ApiSingleRecordResponseModel,
    ResourceRecordModel,
)

log = logging.getLogger()


USER_AGENT = "autocrt/2.0"
BASE_URL_PROD = "https://api.regfish.de/dns/"


class RegfishClient:
    """Client for Regfish's DNS API.

    Client implementation for Regfish DNS API [1]_.

    References
    ----------
    .. [1] Regfish API Documentation: https://regfish.readme.io/reference
    """

    def __init__(self, api_key, base_url=BASE_URL_PROD):
        self.api_key = api_key
        self.base_url = base_url

        self.session = Session()
        self.session.headers.update(
            {
                "user-agent": USER_AGENT,
                "x-api-key": self.api_key,
                "accept": "application/json",
            }
        )

    def _domain_endpoint(self, domain: str) -> str:
        return urljoin(self.base_url, f"{domain}/rr")

    def _rr_endpoint(self, rrid: Optional[int] = None) -> str:
        return urljoin(self.base_url, f"rr/{rrid}" if rrid else "rr")

    def get_all_records(self, domain: str) -> List[ResourceRecordModel]:
        """Get records by domain.

        Retrieves all records from endpoint [1]_.

        Parameters
        ----------
        domain : str
            Fully Qualified Domain Name to get records for.

        Returns
        -------
        List[ResourceRecordModel]
            A list with all records in given domain.

        References
        ----------
        .. [1] Get DNS records - Regfish DNS: https://regfish.readme.io/reference/getrecordsbydomain
        """
        domain_endpoint = self._domain_endpoint(domain)

        response = self.session.get(domain_endpoint)
        response.raise_for_status()

        return Adapters.BatchResponse.validate_json(response.text, strict=True).response

    def get_record(self, rrid: int) -> ResourceRecordModel:
        """Get DNS record by rrid.

        Retrieve details about the resource record specified by `rrid` [1]_.

        Parameters
        ----------
        rrid : int
            The resource record id.

        Returns
        -------
        ResourceRecordModel
            The resource record.

        References
        ----------
        .. [1] Get DNS record - Regfish DNS: https://regfish.readme.io/reference/getrecordbyrrid
        """
        rr_endpoint = self._rr_endpoint(rrid)

        response = self.session.get(rr_endpoint)
        response.raise_for_status()

        return Adapters.SingleResponse.validate_json(
            response.text, strict=True
        ).response

    def create_record(
        self,
        type_: Literal["A", "AAAA", "CNAME", "CAA", "ALIAS", "TXT", "MX"],
        name: str,
        data: str,
        ttl: int,
        annotation: Optional[str] = None,
        priority: Optional[int] = None,
    ) -> ResourceRecordModel:
        """Create DNS record.

        Create a new DNS record and automatically detect the zone based on the fqdn
        specified in the name parameter [1]_.

        Parameters
        ----------
        type_ : Literal["A", "AAAA", "CNAME", "CAA", "ALIAS", "TXT", "MX"]
            The DNS records' type.
        name : str
            Fully Qualified Domain Name (FQDN, ending with a period).
        data : str
            The DNS records' data.
        ttl : int
            Time To Live (60-604800).
        annotation : Optional[str] = None, optional
            A custom note for this particular record, by default None.
        priority : Optional[int] = None, optional
            If `type_` is `MX`, the priority of this MX record, by default None.

        Returns
        -------
        ResourceRecordModel
            The created resource record.

        References
        ----------
        .. [1] Create DNS record - Regfish DNS: https://regfish.readme.io/reference/addrecord
        """
        record_endpoint = self._rr_endpoint()
        rr: ResourceRecordModel = Adapters.ResourceRecord.validate_python(
            {
                "id": 0,  # not used in request, but required for validation currently
                "type": type_,
                "name": name,
                "data": data,
                "ttl": ttl,
                "annotation": annotation,
                "priority": priority,
            },
        )

        response = self.session.post(
            record_endpoint,
            data=rr.model_dump_json(
                include={"type_", "name", "ttl", "annotation", "data", "priority"},
                exclude_none=True,
                exclude_unset=True,
                by_alias=True,
            ),
            headers={"content-type": "application/json"},
        )

        parsed_response: ApiSingleRecordResponseModel = (
            Adapters.SingleResponse.validate_json(response.text, strict=True)
        )

        if not parsed_response.success:
            log.error("HTTP %d - GET %s", response.status_code, response.request.url)
            log.debug("request: %s", response.request.body)
            log.error("error: %s", parsed_response.error)  # type: ignore
            log.error("message: %s", parsed_response.message)  # type: ignore
            response.raise_for_status()

        return parsed_response.response  # type: ignore

    def update_record(
        self,
        rrid: int,
        type_: Literal["A", "AAAA", "CNAME", "CAA", "ALIAS", "TXT", "MX"],
        name: str,
        data: str,
        ttl: int,
        annotation: Optional[str] = None,
        priority: Optional[int] = None,
    ) -> ResourceRecordModel:
        """Update DNS record by rrid.

        Update a specific Resource Record (rrid). This is useful for modifying the
        record's name or type, or when managing multiple records with the same name and
        type combination [1]_.

        Parameters
        ----------
        rrid : int
            The resource record id of record to update.
        type_ : Literal["A", "AAAA", "CNAME", "CAA", "ALIAS", "TXT", "MX"]
            The DNS records' type.
        name : str
            Fully Qualified Domain Name (FQDN, ending with a period).
        data : str
            The DNS records' data.
        ttl : int
            Time To Live (60-604800).
        annotation : Optional[str], optional
            A custom note for this particular record, by default None.
        priority : Optional[int], optional
            If `type_` is `MX`, the priority of this MX record, by default None.

        Returns
        -------
        ResourceRecordModel
            _description_

        References
        ----------
        .. [1] Update DNS record - Regfish DNS: https://regfish.readme.io/reference/patchrecord
        """
        record_endpoint = self._rr_endpoint(rrid)

        rr: ResourceRecordModel = Adapters.ResourceRecord.validate_python(
            {
                "id": rrid,  # not used in request, but required for validation currently
                "type": type_,
                "name": name,
                "data": data,
                "ttl": ttl,
                "annotation": annotation,
                "priority": priority,
            },
        )

        response = self.session.patch(
            record_endpoint,
            data=rr.model_dump_json(
                include={"type_", "name", "ttl", "annotation", "data", "priority"},
                exclude_none=True,
                exclude_unset=True,
                by_alias=True,
            ),
            headers={"content-type": "application/json"},
        )

        parsed_response: ApiSingleRecordResponseModel = (
            Adapters.SingleResponse.validate_json(response.text, strict=True)
        )

        if not parsed_response.success:
            log.error("HTTP %d - GET %s", response.status_code, response.request.url)
            log.debug("request: %s", response.request.body)
            log.error("error: %s", parsed_response.error)  # type: ignore
            log.error("message: %s", parsed_response.message)  # type: ignore
            response.raise_for_status()

        return parsed_response.response  # type: ignore

    def delete_record(self, rrid: int) -> requests.Response:
        """Delete DNS record by rrid.

        Delete a specific Resource Record (rrid) [1]_.

        Parameters
        ----------
        rrid : int
            The resource record id of record to delete.

        Returns
        -------
        requests.Response
            The response object.

        References
        ----------
        .. [1] Delete DNS record - Regfish DNS: https://regfish.readme.io/reference/deleterecordbyrrid
        """
        record_endpoint = self._rr_endpoint(rrid)

        response = self.session.delete(record_endpoint)
        response.raise_for_status()
        return response
