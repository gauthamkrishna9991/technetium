from enum import Enum
from types import NoneType
from typing import Optional, Union
from pydantic import BaseModel, Field


class AppType(str, Enum):
    Free = "Free"
    Paid = "Paid"


class ContentRatingType(str, Enum):
    ADULTS_ONLLY_18_PLUS = "Adults only 18+"
    MATURE_17_PLUS = "Mature 17+"
    UNRATED = "Unrated"
    TEEN = "Teen"
    EVERYONE = "Everyone"
    EVERYONE_10_PLUS = "Everyone 10+"
    NONE = ""


class RatingRoundoff(Enum):
    R1 = 1
    R2 = 2
    R3 = 3
    R4 = 4
    R5 = 5
    ERROR = None


class PlayStoreElement(BaseModel):
    app: str = Field(alias="App")
    category: str = Field(alias="Category")
    rating: float = Field(alias="Rating")
    reviews: str = Field(alias="Reviews")
    size: Optional[str] = Field("Size")
    installs: str = Field(alias="Installs")
    app_type: Union[AppType, str] = Field(alias="Type")
    price: Union[float, str] = Field(alias="Price")
    rating_roundoff: ContentRatingType = Field(alias="Content Rating")
    genres: str = Field(alias="Genres")
    last_updated: str = Field(alias="Last Updated")
    current_ver: str = Field(alias="Current Ver")
    android_ver: Optional[str] = Field(alias="Android Ver")
    rating_roundoff: Optional[int] = Field(alias="Rating Roundoff")

    class Config:
        use_enum_values = True
