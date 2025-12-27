from pydantic import BaseModel, Field


class PromptRequest(BaseModel):
    """
    Kullanıcıdan gelen kod üretim isteği.
    """
    prompt: str = Field(
        ...,
        min_length=3,
        description="LLM'lerin kod üretmesi için verilen doğal dil isteği"
    )