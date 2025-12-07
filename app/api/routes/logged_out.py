from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
import os

router = APIRouter()
templates = Jinja2Templates(
    directory=os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "templates"
    )
)


@router.get("/logged-out.html", include_in_schema=False)
async def logged_out_page(request: Request):
    return templates.TemplateResponse("logged-out.html", {"request": request})
