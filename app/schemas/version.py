from typing import Annotated

from pydantic import BaseModel, Field


class VersionSchema(BaseModel):
    version: Annotated[
        str,
        Field(
            pattern=r"^v?\d+\.\d+\.\d+(-[a-zA-Z]+(-\d+)?)?$|^v?\d+\.\d+\.[a-zA-Z]+-\d+$",
            description=(
                "Version must follow one of these formats: "
                "v*.*.*, *.*.*, v*.*.[word]-*, *.*.[word]-*, or v*.*.*-[word].*."
            ),
        ),
    ]
