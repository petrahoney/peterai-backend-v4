"""
PETER AI Autonomous Executor
- Manages tasks via OpenClaw
- Tracks in PostgreSQL
- Integrates with PETER AI backend
"""

import psycopg2
import json
from datetime import datetime
import asyncio
import httpx
import uuid
from typing import Dict, List, Any

DB_CONN = "postgresql://peter_dev:PeterAI2026Secure@127.0.0.1/peter_ai_autonomous"

class AutonomousExecutor:
    """Execute tasks using OpenClaw + PETER AI"""
    
    def __init__(self):
        self.conn = None
        self.ai_base_url = "http://localhost:8001"
        self.ai_key = "sk-peter-demo"
    
    async def plan_task(self, user_request: str, user_id: str) -> Dict:
        """Use Claude to plan task steps"""
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.ai_base_url}/api/chat",
                headers={"x-api-key": self.ai_key},
                json={"message": f"Plan autonomous execution steps for: {user_request}. Return JSON with steps array."},
                timeout=60.0
            )
            
            result = response.json()
            plan = result.get("response", "")
        
        # Store in database
        task_id = str(uuid.uuid4())
        conn = psycopg2.connect(DB_CONN)
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO tasks (id, user_id, original_request, status, created_at)
            VALUES (%s, %s, %s, 'planning', NOW())
        """, (task_id, user_id, user_request))
        conn.commit()
        cur.close()
        conn.close()
        
        return {
            "task_id": task_id,
            "status": "planning",
            "plan": plan
        }
    
    async def execute_task(self, task_id: str) -> Dict:
        """Execute planned task steps"""
        
        # Get task from database
        conn = psycopg2.connect(DB_CONN)
        cur = conn.cursor()
        cur.execute("""
            SELECT original_request, status FROM tasks WHERE id=%s
        """, (task_id,))
        
        row = cur.fetchone()
        if not row:
            cur.close()
            conn.close()
            raise Exception(f"Task {task_id} not found")
        
        original_request, status = row
        
        # Update status
        cur.execute("""
            UPDATE tasks SET status='executing' WHERE id=%s
        """, (task_id,))
        conn.commit()
        
        try:
            # For now: simulate execution
            # TODO: Integrate with actual OpenClaw execution
            result = {
                "action": original_request,
                "status": "completed",
                "result": "Task executed successfully"
            }
            
            # Store result
            cur.execute("""
                UPDATE tasks SET status='completed', completed_at=NOW() WHERE id=%s
            """, (task_id,))
            conn.commit()
            
            return {
                "task_id": task_id,
                "status": "completed",
                "result": result
            }
            
        except Exception as e:
            cur.execute("""
                UPDATE tasks SET status='failed' WHERE id=%s
            """, (task_id,))
            conn.commit()
            raise e
        
        finally:
            cur.close()
            conn.close()
    
    def get_task_status(self, task_id: str) -> Dict:
        """Get task status"""
        
        conn = psycopg2.connect(DB_CONN)
        cur = conn.cursor()
        cur.execute("""
            SELECT id, user_id, original_request, status, created_at, completed_at
            FROM tasks WHERE id=%s
        """, (task_id,))
        
        row = cur.fetchone()
        cur.close()
        conn.close()
        
        if not row:
            raise Exception(f"Task {task_id} not found")
        
        return {
            "id": row[0],
            "user_id": row[1],
            "request": row[2],
            "status": row[3],
            "created_at": str(row[4]),
            "completed_at": str(row[5]) if row[5] else None
        }

# Create singleton
executor = AutonomousExecutor()
