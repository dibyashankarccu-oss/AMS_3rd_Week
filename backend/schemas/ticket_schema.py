from pydantic import BaseModel
from typing import Optional

class TicketRequest(BaseModel):

    name: str
    email: str

    summary: str
    description: str = ""

    app_name: Optional[str] = ""
    component_name: Optional[str] = ""

    urgency: str
    impact: str