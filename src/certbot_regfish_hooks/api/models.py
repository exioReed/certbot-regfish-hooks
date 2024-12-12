"""
Models for Regfish's DNS API [1]_.

This module provides Pydantic models for parsing and validating resource records and
Regfish API responses.

It supports these record types:
- A
- AAAA
- CNAME
- CAA
- ALIAS
- TXT
- MX

References
----------
.. [1] Regfish API Documentation: https://regfish.readme.io/reference
"""

from typing import List, Literal, Optional, Union

from pydantic import BaseModel, Field, TypeAdapter
from typing_extensions import Annotated


# Base Models
class DnsRecordBase(BaseModel):
    """Base model for all DNS resource records."""

    name: str
    ttl: int = Field(ge=60, le=604800)
    annotation: Optional[str] = None
    data: str
    auto: bool = False
    active: bool = True
    rrid: int = Field(alias="id")


# DNS Record Types
class StandardDnsRecord(DnsRecordBase):
    """Model for standard DNS record types (A, AAAA, CNAME, CAA, ALIAS, TXT)."""

    type_: Literal["A", "AAAA", "CNAME", "CAA", "ALIAS", "TXT"] = Field(
        alias="type", description="Standard DNS record type"
    )


class MxDnsRecord(DnsRecordBase):
    """Model for MX (Mail Exchange) records."""

    type_: Literal["MX"] = Field(alias="type", description="MX record type")
    priority: int = Field(
        ge=0, le=10000, description="MX priority (0-10000, lower is higher priority)"
    )


# API Response Models
class SuccessResponseBase(BaseModel):
    """Base model for successful API responses."""

    success: Literal[True]
    code: int


class ErrorResponse(BaseModel):
    """Error response from the API."""

    success: Literal[False]
    code: Optional[int] = None
    message: Optional[str] = None
    error: Optional[str] = None


class DnsRecordSuccessResponse(SuccessResponseBase):
    """Success response containing a single DNS record."""

    response: Union[StandardDnsRecord, MxDnsRecord]


class DnsRecordBatchSuccessResponse(SuccessResponseBase):
    """Success response containing multiple DNS records."""

    response: List[Union[StandardDnsRecord, MxDnsRecord]]


# Type Annotations
ResourceRecordModel = Annotated[
    Union[StandardDnsRecord, MxDnsRecord], Field(discriminator="type_")
]

ApiSingleRecordResponseModel = Annotated[
    Union[DnsRecordSuccessResponse, ErrorResponse], Field(discriminator="success")
]

ApiBatchRecordResponseModel = Annotated[
    Union[DnsRecordBatchSuccessResponse, ErrorResponse], Field(discriminator="success")
]


# Type Adapters
class Adapters:
    """Collection of TypeAdapters for DNS record models."""

    ResourceRecord = TypeAdapter(ResourceRecordModel)
    SingleResponse = TypeAdapter(ApiSingleRecordResponseModel)
    BatchResponse = TypeAdapter(ApiBatchRecordResponseModel)
