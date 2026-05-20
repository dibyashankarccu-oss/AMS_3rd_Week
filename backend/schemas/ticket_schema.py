from pydantic import BaseModel
from typing import Optional

class TicketRequest(BaseModel):

    name: str
    email: str

    summary: str
    description: str = ""

    # application mapping
    app_name: Optional[str] = ""
    app_code: Optional[str] = None

    # component mapping
    component_name: Optional[str] = ""
    component_code: Optional[str] = None

    urgency: str
    impact: str