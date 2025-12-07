from fastapi import Request
from app.main import app, templates


@app.get("/logged-out.html", include_in_schema=False)
async def logged_out_page(request: Request):
    return templates.TemplateResponse("logged-out.html", {"request": request})
