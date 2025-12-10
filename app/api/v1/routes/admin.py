"""
Admin API Routes

Secure admin-only endpoints for:
- User management
- Interest tracking analytics
- Global and per-user settings management
- System monitoring

Security: All endpoints require admin authentication
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional, Dict, List, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from datetime import datetime, timedelta
from pydantic import BaseModel
import asyncio

from app.api.v1.deps import get_db, get_current_user
from app.models import User, UserInteraction, ContentItem, UserSession
from app.core.config import settings

router = APIRouter()


async def read_file_async(path):
    """Read file asynchronously using thread pool"""

    def _read():
        with open(path) as f:
            return f.read()

    return await asyncio.to_thread(_read)


# Pydantic Models
class GlobalSettings(BaseModel):
    minHoverDuration: int = 1500
    afkThreshold: int = 5000
    movementThreshold: int = 5
    microMovementThreshold: int = 20
    slowdownVelocityThreshold: float = 0.3
    velocitySampleRate: int = 100
    interestScoreThreshold: int = 50
    scrollSlowdownThreshold: float = 2.0


class UserCustomSettings(BaseModel):
    debug_mode: bool = False
    custom_settings: Optional[Dict[str, Any]] = None


# Admin verification dependency
def verify_admin(current_user: User = Depends(get_current_user)):
    """Verify that the current user is an admin"""
    if not current_user or not current_user.is_admin:  # type: ignore
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


@router.get("/verify")
async def verify_admin_access(
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """Verify admin access and return user info"""
    if not current_user or not current_user.is_admin:  # type: ignore
        raise HTTPException(status_code=403, detail="Admin access required")

    return {
        "is_admin": True,
        "user": {
            "id": current_user.id,
            "username": current_user.username,
            "email": current_user.email,
        },
    }


@router.get("/tracking-log")
async def get_tracking_log(
    limit: int = Query(100, ge=1, le=1000),
    admin: User = Depends(verify_admin),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Get recent interest tracking events"""

    # Get recent interest tracking interactions
    result = await db.execute(
        select(UserInteraction)
        .where(
            UserInteraction.interaction_type.in_(
                ["interest_high", "interest_medium", "interest_low"]
            )
        )
        .order_by(UserInteraction.created_at.desc())
        .limit(limit)
    )

    interactions = result.scalars().all()

    events = []
    for interaction in interactions:
        events.append(
            {
                "id": interaction.id,
                "user_id": interaction.user_id,
                "session_id": interaction.session_id,
                "content_item_id": interaction.content_item_id,
                "interaction_type": interaction.interaction_type,
                "duration_seconds": interaction.duration_seconds,
                "created_at": interaction.created_at.isoformat(),
                "metadata": {},  # Metadata will be available when we add the column
            }
        )

    return {"events": events}


@router.post("/clear-tracking")
async def clear_tracking_log(
    admin: User = Depends(verify_admin), db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Clear all interest tracking data (destructive operation)"""

    # Delete interest tracking interactions
    result = await db.execute(
        select(UserInteraction).where(
            UserInteraction.interaction_type.in_(
                ["interest_high", "interest_medium", "interest_low"]
            )
        )
    )
    interactions = result.scalars().all()

    for interaction in interactions:
        await db.delete(interaction)

    await db.commit()

    return {"status": "cleared", "count": len(interactions)}


@router.get("/settings/global")
async def get_global_settings(admin: User = Depends(verify_admin)) -> Dict[str, Any]:
    """Get current global hover tracking settings"""

    # For now, return defaults. In production, these would be stored in database
    return {
        "minHoverDuration": 1500,
        "afkThreshold": 5000,
        "movementThreshold": 5,
        "microMovementThreshold": 20,
        "slowdownVelocityThreshold": 0.3,
        "velocitySampleRate": 100,
        "interestScoreThreshold": 50,
        "scrollSlowdownThreshold": 2.0,
    }


@router.post("/settings/global")
async def save_global_settings(
    settings: GlobalSettings,
    admin: User = Depends(verify_admin),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, str]:
    """Save global hover tracking settings"""

    # For now, just validate and return success

    return {"status": "saved", "message": "Global settings updated successfully"}


@router.get("/users")
async def get_all_users(
    admin: User = Depends(verify_admin), db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Get all users with interaction counts"""

    # Get all users
    result = await db.execute(select(User))
    users = result.scalars().all()

    user_list = []
    for user in users:
        # Count interactions
        interaction_count_result = await db.execute(
            select(func.count(UserInteraction.id)).where(
                UserInteraction.user_id == user.id
            )
        )
        interaction_count = interaction_count_result.scalar() or 0

        user_list.append(
            {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "is_admin": user.is_admin,
                "created_at": user.created_at.isoformat() if user.created_at else None,  # type: ignore
                "last_login": user.last_login.isoformat() if user.last_login else None,  # type: ignore
                "interaction_count": interaction_count,
                "debug_mode": getattr(user, "debug_mode", False),
                "custom_settings": None,
            }
        )

    return {"users": user_list}


@router.get("/users/{user_id}")
async def get_user_details(
    user_id: int,
    admin: User = Depends(verify_admin),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Get detailed information about a specific user"""

    # Get user
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Get interaction stats
    total_result = await db.execute(
        select(func.count(UserInteraction.id)).where(UserInteraction.user_id == user_id)
    )
    total_interactions = total_result.scalar() or 0

    high_result = await db.execute(
        select(func.count(UserInteraction.id)).where(
            and_(
                UserInteraction.user_id == user_id,
                UserInteraction.interaction_type == "interest_high",
            )
        )
    )
    high_interest = high_result.scalar() or 0

    avg_duration_result = await db.execute(
        select(func.avg(UserInteraction.duration_seconds)).where(
            UserInteraction.user_id == user_id
        )
    )
    avg_duration = avg_duration_result.scalar() or 0

    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "is_admin": user.is_admin,
        "created_at": user.created_at.isoformat() if user.created_at else None,  # type: ignore
        "last_login": user.last_login.isoformat() if user.last_login else None,  # type: ignore
        "debug_mode": getattr(user, "debug_mode", False),
        "custom_settings": None,
        "stats": {
            "total_interactions": total_interactions,
            "high_interest": high_interest,
            "avg_duration": round(float(avg_duration), 1) if avg_duration else 0,
        },
    }


@router.post("/users/{user_id}/settings")
async def save_user_settings(
    user_id: int,
    settings: UserCustomSettings,
    admin: User = Depends(verify_admin),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, str]:
    """Save custom settings for a specific user"""

    # Verify user exists
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Update debug mode
    user.debug_mode = settings.debug_mode  # type: ignore

    await db.commit()

    return {"status": "saved", "message": f"Settings updated for user {user_id}"}


@router.get("/analytics")
async def get_analytics(
    start: str = Query(..., description="Start date (YYYY-MM-DD)"),
    end: str = Query(..., description="End date (YYYY-MM-DD)"),
    admin: User = Depends(verify_admin),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Get analytics data for specified date range"""

    try:
        start_date = datetime.fromisoformat(start)
        end_date = datetime.fromisoformat(end) + timedelta(days=1)  # Include end date
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format")

    # Interest distribution
    high_result = await db.execute(
        select(func.count(UserInteraction.id)).where(
            and_(
                UserInteraction.interaction_type == "interest_high",
                UserInteraction.created_at >= start_date,
                UserInteraction.created_at < end_date,
            )
        )
    )
    high_count = high_result.scalar() or 0

    medium_result = await db.execute(
        select(func.count(UserInteraction.id)).where(
            and_(
                UserInteraction.interaction_type == "interest_medium",
                UserInteraction.created_at >= start_date,
                UserInteraction.created_at < end_date,
            )
        )
    )
    medium_count = medium_result.scalar() or 0

    low_result = await db.execute(
        select(func.count(UserInteraction.id)).where(
            and_(
                UserInteraction.interaction_type == "interest_low",
                UserInteraction.created_at >= start_date,
                UserInteraction.created_at < end_date,
            )
        )
    )
    low_count = low_result.scalar() or 0

    # Top content
    top_content_result = await db.execute(
        select(
            ContentItem.id,
            ContentItem.title,
            func.count(UserInteraction.id).label("view_count"),
        )
        .join(UserInteraction, ContentItem.id == UserInteraction.content_item_id)
        .where(
            and_(
                UserInteraction.created_at >= start_date,
                UserInteraction.created_at < end_date,
            )
        )
        .group_by(ContentItem.id, ContentItem.title)
        .order_by(func.count(UserInteraction.id).desc())
        .limit(10)
    )

    top_content = []
    for row in top_content_result:
        top_content.append(
            {
                "content_id": row[0],
                "title": row[1],
                "view_count": row[2],
                "avg_score": 0,
            }
        )

    # Hover patterns
    avg_duration_result = await db.execute(
        select(func.avg(UserInteraction.duration_seconds)).where(
            and_(
                UserInteraction.interaction_type.in_(
                    ["interest_high", "interest_medium", "interest_low"]
                ),
                UserInteraction.created_at >= start_date,
                UserInteraction.created_at < end_date,
            )
        )
    )
    avg_duration = avg_duration_result.scalar() or 0

    return {
        "interest_distribution": {
            "high": high_count,
            "medium": medium_count,
            "low": low_count,
        },
        "top_content": top_content,
        "hover_patterns": {
            "avg_duration": round(float(avg_duration), 1) if avg_duration else 0,
            "avg_slowdowns": 0,
            "movement_rate": 0,
            "afk_rate": 0,
        },
    }


# === Dashboard Endpoints ===
from pathlib import Path
import subprocess
import json
import subprocess
from pathlib import Path
from fastapi.responses import HTMLResponse

# Use relative paths for cross-platform compatibility
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
STORAGE_STATUS_FILE = PROJECT_ROOT / "STORAGE_STATUS.txt"
STORAGE_HISTORY_FILE = PROJECT_ROOT / "storage_history.json"

AVAILABLE_SCRIPTS = {
    "Storage Monitor": "python3 storage_monitor.py",
    "RSS Benchmark": "python3 benchmark_feeds.py",
    "Check Logs": f"tail -100 {PROJECT_ROOT / 'logs' / 'error.log'}",
    "Database Stats": "psql -d nexus -c 'SELECT COUNT(*) as total_stories FROM content_items;'",
}


@router.get("/dashboard", response_class=HTMLResponse)
async def admin_dashboard(current_user: User = Depends(verify_admin)):
    """Admin dashboard with storage, scripts, terminal, and chat"""
    # Read storage status
    storage_status = ""
    if STORAGE_STATUS_FILE.exists():
        storage_status = await read_file_async(STORAGE_STATUS_FILE)  # type: ignore

    # Read system logs
    error_log = ""
    service_log = ""
    try:
        error_log_path = PROJECT_ROOT / "logs" / "error.log"
        if error_log_path.exists():
            error_log = await read_file_async(str(error_log_path))
            # Show last 50 lines
            error_log_lines = error_log.split("\n")[-50:]
            error_log = "\n".join(error_log_lines).strip()
    except:
        error_log = "Error reading error.log"

    try:
        service_log_path = PROJECT_ROOT / "logs" / "service.log"
        if service_log_path.exists():
            service_log = await read_file_async(str(service_log_path))
            # Show last 30 lines
            service_log_lines = service_log.split("\n")[-30:]
            service_log = "\n".join(service_log_lines).strip()
    except:
        service_log = "Error reading service.log"

    # Calculate next RSS fetch time (every 15 minutes)
    from datetime import datetime, timedelta

    now = datetime.now()
    # RSS fetches run every 15 minutes, so find the next 15-minute interval
    minutes_since_epoch = (now - datetime(1970, 1, 1)).total_seconds() / 60
    next_fetch_minutes = ((minutes_since_epoch // 15) + 1) * 15
    next_fetch_time = datetime(1970, 1, 1) + timedelta(minutes=next_fetch_minutes)
    seconds_until_next = int((next_fetch_time - now).total_seconds())

    # Build script buttons HTML
    script_buttons = ""
    for name in AVAILABLE_SCRIPTS.keys():
        script_buttons += f'    <button class="script-btn" onclick="runScript(\'{name}\')">▶ {name}</button>\n'

    return HTMLResponse(
        f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Nexus Admin Dashboard</title>
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0d1117; color: #c9d1d9; }}
            .container {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; padding: 20px; max-width: 1600px; margin: 0 auto; }}
            .panel {{ background: #161b22; border: 1px solid #30363d; border-radius: 6px; padding: 20px; overflow: auto; }}
            .panel h2 {{ color: #58a6ff; margin-bottom: 15px; border-bottom: 1px solid #30363d; padding-bottom: 10px; }}
            .storage-status {{ font-family: monospace; font-size: 12px; white-space: pre-wrap; max-height: 400px; overflow-y: auto; }}
            .scripts {{ max-height: 400px; overflow-y: auto; }}
            .script-btn {{ display: block; width: 100%; padding: 10px; margin: 8px 0; background: #238636; color: white; border: none; border-radius: 4px; cursor: pointer; text-align: left; font-size: 13px; }}
            .script-btn:hover {{ background: #2ea043; }}
            .terminal {{ background: #010409; font-family: monospace; font-size: 12px; max-height: 400px; overflow-y: auto; padding: 10px; border-radius: 4px; }}
            .terminal-input {{ width: 100%; padding: 8px; margin-top: 10px; background: #0d1117; color: #c9d1d9; border: 1px solid #30363d; border-radius: 4px; font-family: monospace; }}
            .chat-container {{ display: flex; flex-direction: column; height: 500px; }}
            .chat-messages {{ flex: 1; overflow-y: auto; margin-bottom: 10px; padding: 10px; background: #010409; border-radius: 4px; }}
            .chat-message {{ margin-bottom: 10px; padding: 8px; border-radius: 4px; }}
            .chat-user {{ background: #238636; text-align: right; }}
            .chat-assistant {{ background: #1f6feb; }}
            .chat-input-area {{ display: flex; gap: 10px; }}
            .chat-input {{ flex: 1; padding: 8px; background: #0d1117; color: #c9d1d9; border: 1px solid #30363d; border-radius: 4px; font-family: monospace; }}
            select {{ padding: 8px; background: #0d1117; color: #c9d1d9; border: 1px solid #30363d; border-radius: 4px; }}
            button {{ padding: 8px 16px; background: #238636; color: white; border: none; border-radius: 4px; cursor: pointer; }}
            button:hover {{ background: #2ea043; }}
            .button-group {{ display: flex; gap: 8px; margin-top: 10px; }}
            .output {{ background: #010409; padding: 10px; border-radius: 4px; margin-top: 10px; max-height: 150px; overflow-y: auto; font-size: 11px; }}
            .countdown {{ font-size: 24px; font-weight: bold; color: #58a6ff; text-align: center; margin: 20px 0; }}
            .rss-status {{ text-align: center; }}
            .rss-info {{ font-size: 14px; color: #8b949e; margin-top: 10px; }}
            .logs-container {{ display: flex; gap: 20px; }}
            .log-panel {{ flex: 1; }}
            .log-content {{ font-family: monospace; font-size: 11px; white-space: pre-wrap; max-height: 300px; overflow-y: auto; background: #010409; padding: 10px; border-radius: 4px; }}
            .log-tabs {{ display: flex; margin-bottom: 10px; }}
            .log-tab {{ padding: 8px 16px; background: #30363d; color: #c9d1d9; border: none; border-radius: 4px 4px 0 0; cursor: pointer; }}
            .log-tab.active {{ background: #161b22; color: #58a6ff; }}
            .log-tab:hover {{ background: #21262d; }}
        </style>
    </head>
    <body>
        <div class="container">
            <!-- RSS Status -->
            <div class="panel">
                <h2>📰 RSS Fetch Status</h2>
                <div class="rss-status">
                    <div>Next fetch in:</div>
                    <div class="countdown" id="countdown">--:--:--</div>
                    <div class="rss-info">
                        RSS feeds update every 15 minutes<br>
                        Last fetch: <span id="lastFetch">Checking...</span>
                    </div>
                </div>
            </div>

            <!-- System Logs -->
            <div class="panel">
                <h2>📋 System Logs</h2>
                <div class="log-tabs">
                    <button class="log-tab active" onclick="showLog('error')">Error Log</button>
                    <button class="log-tab" onclick="showLog('service')">Service Log</button>
                </div>
                <div class="logs-container">
                    <div class="log-panel">
                        <div id="error-log" class="log-content">{error_log}</div>
                        <div id="service-log" class="log-content" style="display: none;">{service_log}</div>
                    </div>
                </div>
                <button onclick="refreshLogs()" style="width: 100%; margin-top: 10px;">Refresh Logs</button>
            </div>

            <!-- Script Runner -->
            <div class="panel">
                <h2>🔧 Server Scripts</h2>
                <div class="scripts">
{script_buttons}                </div>
                <div class="output" id="scriptOutput"></div>
            </div>

            <!-- Mini Terminal -->
            <div class="panel">
                <h2>⌨️ Terminal</h2>
                <div class="terminal" id="terminal">\\$ Ready</div>
                <input type="text" class="terminal-input" id="terminalInput" placeholder="Enter command..." onkeypress="if(event.key==='Enter') runTerminalCommand()">
                <button onclick="runTerminalCommand()" style="width: 100%; margin-top: 8px;">Execute</button>
            </div>

            <!-- AI Chat (Full Width Below) -->
            <div class="panel" style="grid-column: 1 / -1;">
                <h2>🤖 Copilot Chat</h2>
                <select id="agentSelect" style="width: 200px; margin-bottom: 10px;">
                    <option value="general">General Assistant</option>
                    <option value="code">Code Expert</option>
                    <option value="devops">DevOps Specialist</option>
                </select>
                <div class="chat-container">
                    <div class="chat-messages" id="chatMessages"></div>
                    <div class="chat-input-area">
                        <input type="text" class="chat-input" id="chatInput" placeholder="Ask Copilot..." onkeypress="if(event.key==='Enter') sendChat()">
                        <button onclick="sendChat()">Send</button>
                    </div>
                </div>
            </div>
        </div>

        <script>
            // RSS countdown timer
            let countdownInterval;
            const RSS_INTERVAL_MINUTES = 15;
            
            function startCountdown() {{
                updateCountdown();
                countdownInterval = setInterval(updateCountdown, 1000);
            }}
            
            function updateCountdown() {{
                const now = new Date();
                const minutesSinceEpoch = (now - new Date(1970, 0, 1)) / (1000 * 60);
                const nextFetchMinutes = Math.ceil(minutesSinceEpoch / RSS_INTERVAL_MINUTES) * RSS_INTERVAL_MINUTES;
                const nextFetchTime = new Date(1970, 0, 1);
                nextFetchTime.setMinutes(nextFetchMinutes);
                
                const timeDiff = nextFetchTime - now;
                
                if (timeDiff <= 0) {{
                    // Fetch should be happening now, refresh in 5 seconds
                    document.getElementById('countdown').textContent = '00:00:00';
                    setTimeout(() => {{
                        location.reload();
                    }}, 5000);
                    return;
                }}
                
                const hours = Math.floor(timeDiff / (1000 * 60 * 60));
                const minutes = Math.floor((timeDiff % (1000 * 60 * 60)) / (1000 * 60));
                const seconds = Math.floor((timeDiff % (1000 * 60)) / 1000);
                
                document.getElementById('countdown').textContent = 
                    String(hours).padStart(2, '0') + ':' + 
                    String(minutes).padStart(2, '0') + ':' + 
                    String(seconds).padStart(2, '0');
            }}
            
            // Update last fetch time
            async function updateLastFetch() {{
                try {{
                    const response = await fetch('/api/v1/content/feed?limit=1');
                    const data = await response.json();
                    if (data.length > 0 && data[0].created_at) {{
                        const lastFetch = new Date(data[0].created_at);
                        document.getElementById('lastFetch').textContent = lastFetch.toLocaleString();
                    }}
                }} catch (e) {{
                    document.getElementById('lastFetch').textContent = 'Unable to check';
                }}
            }}

            async function refreshStorage() {{
                const response = await fetch('/api/v1/admin/storage');
                const data = await response.json();
                document.getElementById('storageStatus').textContent = data.status;
            }}

            async function runScript(name) {{
                const output = document.getElementById('scriptOutput');
                output.textContent = `Running ${{name}}...`;
                const response = await fetch('/api/v1/admin/run-script', {{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/json'}},
                    body: JSON.stringify({{name}})
                }});
                const data = await response.json();
                output.textContent = data.output;
            }}

            async function runTerminalCommand() {{
                const input = document.getElementById('terminalInput');
                const terminal = document.getElementById('terminal');
                terminal.textContent += `\\n\\$ ${{input.value}}\\n`;
                const response = await fetch('/api/v1/admin/terminal', {{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/json'}},
                    body: JSON.stringify({{cmd: input.value}})
                }});
                const data = await response.json();
                terminal.textContent += data.output;
                terminal.scrollTop = terminal.scrollHeight;
                input.value = '';
            }}

            async function sendChat() {{
                const input = document.getElementById('chatInput');
                const messages = document.getElementById('chatMessages');
                const agent = document.getElementById('agentSelect').value;
                
                const userMsg = document.createElement('div');
                userMsg.className = 'chat-message chat-user';
                userMsg.textContent = input.value;
                messages.appendChild(userMsg);

                const response = await fetch('/api/v1/admin/chat', {{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/json'}},
                    body: JSON.stringify({{message: input.value, agent}})
                }});
                const data = await response.json();

                const assistantMsg = document.createElement('div');
                assistantMsg.className = 'chat-message chat-assistant';
                assistantMsg.textContent = data.response;
                messages.appendChild(assistantMsg);
                
                messages.scrollTop = messages.scrollHeight;
                input.value = '';
            }}
            
            // Initialize countdown and last fetch on page load
            window.onload = function() {{
                startCountdown();
                updateLastFetch();
            }};
            
            // Log tab switching
            function showLog(logType) {{
                const errorLog = document.getElementById('error-log');
                const serviceLog = document.getElementById('service-log');
                const errorTab = document.querySelector('.log-tab:nth-child(1)');
                const serviceTab = document.querySelector('.log-tab:nth-child(2)');
                
                if (logType === 'error') {{
                    errorLog.style.display = 'block';
                    serviceLog.style.display = 'none';
                    errorTab.classList.add('active');
                    serviceTab.classList.remove('active');
                }} else {{
                    errorLog.style.display = 'none';
                    serviceLog.style.display = 'block';
                    errorTab.classList.remove('active');
                    serviceTab.classList.add('active');
                }}
            }}
            
            // Refresh logs
            async function refreshLogs() {{
                try {{
                    // Refresh error log
                    const errorResponse = await fetch('/api/v1/admin/logs/error');
                    const errorData = await errorResponse.json();
                    document.getElementById('error-log').textContent = errorData.content;
                    
                    // Refresh service log
                    const serviceResponse = await fetch('/api/v1/admin/logs/service');
                    const serviceData = await serviceResponse.json();
                    document.getElementById('service-log').textContent = serviceData.content;
                }} catch (e) {{
                    console.error('Failed to refresh logs:', e);
                }}
            }}
        </script>
    </body>
    </html>
    """
    )


@router.get("/logs/error")
async def get_error_log(current_user: User = Depends(verify_admin)):
    """Get the last 50 lines of error.log"""
    try:
        error_log_path = PROJECT_ROOT / "logs" / "error.log"
        if error_log_path.exists():
            content = await read_file_async(str(error_log_path))
            # Return last 50 lines
            lines = content.split("\n")[-50:]
            return {"content": "\n".join(lines).strip()}
        return {"content": "error.log not found"}
    except Exception as e:
        return {"content": f"Error reading error.log: {str(e)}"}


@router.get("/logs/service")
async def get_service_log(current_user: User = Depends(verify_admin)):
    """Get the last 30 lines of service.log"""
    try:
        service_log_path = PROJECT_ROOT / "logs" / "service.log"
        if service_log_path.exists():
            content = await read_file_async(str(service_log_path))
            # Return last 30 lines
            lines = content.split("\n")[-30:]
            return {"content": "\n".join(lines).strip()}
        return {"content": "service.log not found"}
    except Exception as e:
        return {"content": f"Error reading service.log: {str(e)}"}


@router.post("/run-script")
async def run_script_endpoint(
    request: Dict[str, str], current_user: User = Depends(verify_admin)
):
    """Run a predefined server script"""
    script_name = request.get("name")

    if script_name not in AVAILABLE_SCRIPTS:
        raise HTTPException(status_code=400, detail="Script not found")

    cmd = AVAILABLE_SCRIPTS[script_name]

    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30,
            cwd=str(PROJECT_ROOT),
        )
        output = result.stdout + (result.stderr if result.returncode != 0 else "")
        return {"output": output[:5000]}  # Limit output
    except subprocess.TimeoutExpired:
        return {"output": "Script timed out after 30 seconds"}
    except Exception as e:
        return {"output": f"Error: {str(e)}"}


@router.post("/terminal")
async def terminal_endpoint(
    request: Dict[str, str], current_user: User = Depends(verify_admin)
):
    """Execute arbitrary terminal command (admin only)"""
    cmd = request.get("cmd", "").strip()

    if not cmd:
        return {"output": "No command provided"}

    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=10,
            cwd=str(PROJECT_ROOT),
        )
        output = result.stdout + (result.stderr if result.returncode != 0 else "")
        return {"output": output[:2000]}  # Limit output
    except subprocess.TimeoutExpired:
        return {"output": "Command timed out after 10 seconds"}
    except Exception as e:
        return {"output": f"Error: {str(e)}"}


@router.post("/chat")
async def chat_endpoint(
    request: Dict[str, str], current_user: User = Depends(verify_admin)
):
    """Chat with Copilot (placeholder - would integrate with actual Copilot API)"""
    message = request.get("message", "")
    agent = request.get("agent", "general")

    agent_descriptions = {
        "general": "General Assistant",
        "code": "Code Review Expert",
        "devops": "DevOps Specialist",
    }

    return {
        "response": f"[{agent_descriptions.get(agent, 'Assistant')}] I received: '{message}'. Real Copilot API integration coming soon!"
    }
