"""Configuration model for the bilifanscache connection."""

from pydantic import BaseModel, Field


class Config(BaseModel):
    """Configuration read from the NoneBot host environment."""

    bili_fans_overlap_api_base: str = Field(
        default="https://fans.harei.cn",
        min_length=1,
        description="bilifanscache 服务地址",
    )
    bili_fans_overlap_http_timeout: float = Field(
        default=10.0,
        gt=0,
        description="bilifanscache 请求超时时间（秒）",
    )
