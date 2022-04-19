from typing import Optional
from pydantic import BaseModel, Field

from csv import DictReader


class PlayStoreElement(BaseModel):
    app: str = Field(alias="App")
    category: str = Field(alias="Category")
    rating: float = Field(alias="Rating")
    reviews: str = Field(alias="Reviews")
    size: str = Field("Size")
    installs: str = Field(alias="Installs")
    app_type: str = Field(alias="Type")
    price: str = Field(alias="Price")
    content_rating: str = Field(alias="Content Rating")
    genres: str = Field(alias="Genres")
    last_updated: str = Field(alias="Last Updated")
    current_ver: str = Field(alias="Current Ver")
    android_ver: Optional[str] = Field(alias="Android Ver")


with open("playstoredata.csv", "r") as data_file:
    x = list(map(lambda x: PlayStoreElement(**x), list(DictReader(data_file))))
    print(x[-1].json())
