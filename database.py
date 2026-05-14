"""
=============================================================================
DATABASE MODULE - SUPABASE CLOUD STORAGE
=============================================================================
Handles all database operations using Supabase (PostgreSQL) for persistent 
storage. Your data will never be wiped on deployments again.
=============================================================================
"""

import os
import logging
from datetime import datetime
from supabase import create_client, Client

logger = logging.getLogger(__name__)

class Database:
    """Persistent storage for conversations and contact tracking using Supabase."""

    def __init__(self):
        """Initialize the Supabase client."""
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")
        if not url or not key:
            logger.warning("Supabase URL or Key missing. Database operations will fail.")
            self.client = None
        else:
            self.client: Client = create_client(url, key)
            logger.info("✅ Connected to Supabase Cloud Database!")

    # =========================================================================
    # BUSINESS LOOKUP
    # =========================================================================
    def get_business_id_by_phone(self, whatsapp_number: str) -> str:
        if not self.client: return None
        try:
            # Clean number just in case
            clean_number = whatsapp_number.replace("+", "")
            
            # Try to find exactly matching business
            res = self.client.table("businesses").select("id").eq("whatsapp_number", clean_number).execute()
            if res.data and len(res.data) > 0:
                return res.data[0]["id"]
            
            # Sandbox fallback: If not found, just grab the first business created
            # This allows testing the first account with the Twilio sandbox
            res = self.client.table("businesses").select("id").order("created_at", desc=False).limit(1).execute()
            if res.data and len(res.data) > 0:
                return res.data[0]["id"]
        except Exception as e:
            logger.error(f"Error looking up business ID: {e}")
        return None

    # =========================================================================
    # CONVERSATION OPERATIONS
    # =========================================================================

    def save_message(self, business_id: str, phone_number: str, role: str, content: str):
        if not self.client or not business_id: return

        # 1. Ensure contact exists or update their stats
        contact_res = self.client.table("contacts").select("*").eq("phone_number", phone_number).eq("business_id", business_id).execute()
        
        if len(contact_res.data) > 0:
            # Update existing
            current_count = contact_res.data[0].get("message_count", 0)
            self.client.table("contacts").update({
                "message_count": current_count + 1,
                "last_seen": datetime.utcnow().isoformat()
            }).eq("phone_number", phone_number).eq("business_id", business_id).execute()
        else:
            # Insert new
            self.client.table("contacts").insert({
                "business_id": business_id,
                "phone_number": phone_number,
                "message_count": 1
            }).execute()

        # 2. Save the message
        self.client.table("conversations").insert({
            "business_id": business_id,
            "phone_number": phone_number,
            "role": role,
            "content": content
        }).execute()

    def get_conversation_history(self, business_id: str, phone_number: str, limit: int = 50) -> list:
        if not self.client or not business_id: return []
        
        # We order by timestamp descending to get the newest, then reverse it for Gemini
        res = self.client.table("conversations").select("role, content").eq("phone_number", phone_number).eq("business_id", business_id).order("timestamp", desc=True).limit(limit).execute()
        
        # Reverse to chronological order
        history = [
            {"role": row["role"], "parts": [row["content"]]}
            for row in reversed(res.data)
        ]
        return history

    def has_conversation(self, phone_number: str) -> bool:
        if not self.client: return False
        res = self.client.table("conversations").select("id", count="exact").eq("phone_number", phone_number).execute()
        return res.count > 0 if res.count else False

    def clear_conversation(self, phone_number: str) -> bool:
        if not self.client: return False
        res = self.client.table("conversations").delete().eq("phone_number", phone_number).execute()
        cleared = len(res.data) > 0
        if cleared:
            logger.info(f"🗑️ Conversation cleared for: {phone_number}")
        return cleared

    def get_conversation_count(self) -> int:
        if not self.client: return 0
        res = self.client.table("contacts").select("phone_number", count="exact").execute()
        return res.count if res.count else 0

    # =========================================================================
    # CONTACT / LEAD OPERATIONS
    # =========================================================================

    def get_all_contacts(self) -> list:
        if not self.client: return []
        res = self.client.table("contacts").select("*").order("last_seen", desc=True).execute()
        return res.data

    def update_contact_name(self, business_id: str, phone_number: str, name: str):
        if not self.client or not business_id: return
        contact_res = self.client.table("contacts").select("name").eq("phone_number", phone_number).eq("business_id", business_id).execute()
        if len(contact_res.data) > 0 and not contact_res.data[0].get("name"):
            self.client.table("contacts").update({"name": name}).eq("phone_number", phone_number).eq("business_id", business_id).execute()

    # =========================================================================
    # ANALYTICS / STATS
    # =========================================================================

    def get_stats(self) -> dict:
        if not self.client:
            return {"total_contacts": 0, "total_messages": 0, "messages_today": 0, "conversations_today": 0, "top_contacts": []}
            
        contacts_res = self.client.table("contacts").select("*", count="exact").execute()
        total_contacts = contacts_res.count if contacts_res.count else 0
        
        msgs_res = self.client.table("conversations").select("*", count="exact").execute()
        total_messages = msgs_res.count if msgs_res.count else 0
        
        # For simplicity in REST without complex time queries, we'll return zeroes for "today" metrics for now, 
        # or calculate in memory if there are few contacts.
        # Top 5 contacts
        top_res = self.client.table("contacts").select("phone_number, name, message_count, last_seen").order("message_count", desc=True).limit(5).execute()
        
        return {
            "total_contacts": total_contacts,
            "total_messages": total_messages,
            "messages_today": 0,  # Simplified for Supabase migration
            "conversations_today": 0,
            "top_contacts": top_res.data
        }

    # =========================================================================
    # ORDER OPERATIONS
    # =========================================================================

    def save_order(self, business_id: str, phone_number: str, customer_name: str, items: str, total_amount: int, delivery_address: str = None) -> int:
        if not self.client or not business_id: return 0
        res = self.client.table("orders").insert({
            "business_id": business_id,
            "phone_number": phone_number,
            "customer_name": customer_name,
            "items": items,
            "total_amount": total_amount,
            "delivery_address": delivery_address
        }).execute()
        
        order_id = res.data[0].get("id", 0) if res.data else 0
        logger.info(f"📦 Order #{order_id} saved for {phone_number}: {items} = {total_amount}")
        return order_id

    def get_all_orders(self) -> list:
        if not self.client: return []
        res = self.client.table("orders").select("*").order("created_at", desc=True).execute()
        return res.data

    def update_order_status(self, order_id: int, status: str) -> bool:
        if not self.client: return False
        res = self.client.table("orders").update({"status": status}).eq("id", order_id).execute()
        return len(res.data) > 0

    def get_revenue_stats(self) -> dict:
        if not self.client:
            return {"total_orders": 0, "total_revenue": 0, "orders_today": 0, "revenue_today": 0}
            
        res = self.client.table("orders").select("total_amount, status").neq("status", "cancelled").execute()
        
        total_orders = len(res.data)
        total_revenue = sum(order.get("total_amount", 0) for order in res.data)
        
        return {
            "total_orders": total_orders,
            "total_revenue": total_revenue,
            "orders_today": 0,
            "revenue_today": 0
        }

    # =========================================================================
    # HUMAN HANDOFF OPERATIONS
    # =========================================================================

    def set_human_handoff(self, business_id: str, phone_number: str, active: bool = True):
        if not self.client or not business_id: return
        
        # Ensure contact exists before updating
        contact_res = self.client.table("contacts").select("*").eq("phone_number", phone_number).eq("business_id", business_id).execute()
        if len(contact_res.data) == 0:
            self.client.table("contacts").insert({"phone_number": phone_number, "business_id": business_id}).execute()
            
        self.client.table("contacts").update({"human_handoff": active}).eq("phone_number", phone_number).eq("business_id", business_id).execute()
        logger.info(f"🙋 Human handoff {'activated' if active else 'deactivated'} for {phone_number}")

    def is_human_handoff(self, business_id: str, phone_number: str) -> bool:
        if not self.client or not business_id: return False
        res = self.client.table("contacts").select("human_handoff").eq("phone_number", phone_number).eq("business_id", business_id).execute()
        if len(res.data) > 0:
            return bool(res.data[0].get("human_handoff", False))
        return False

    def get_handoff_contacts(self) -> list:
        if not self.client: return []
        res = self.client.table("contacts").select("*").eq("human_handoff", True).order("last_seen", desc=True).execute()
        return res.data

    # =========================================================================
    # SETTINGS / MODE OPERATIONS
    # =========================================================================

    def get_settings(self) -> dict:
        if not self.client: return {"bot_mode": "retail", "business_name": "SalesFlow AI"}
        res = self.client.table("settings").select("*").eq("id", 1).execute()
        if len(res.data) > 0:
            return res.data[0]
        return {"bot_mode": "retail", "business_name": "SalesFlow AI"}

    def update_settings(self, bot_mode: str, business_name: str) -> bool:
        if not self.client: return False
        res = self.client.table("settings").update({
            "bot_mode": bot_mode,
            "business_name": business_name
        }).eq("id", 1).execute()
        return len(res.data) > 0

    # =========================================================================
    # BUSINESS CONFIG (CUSTOM PROMPT EDITOR)
    # =========================================================================

    def get_business_config(self, business_id: str) -> dict:
        """Fetch the business's custom prompt configuration."""
        if not self.client or not business_id: return {}
        try:
            res = self.client.table("businesses").select(
                "name, bot_mode, agent_name, greeting, business_description, "
                "products_services, payment_info, business_hours, custom_rules, tone"
            ).eq("id", business_id).execute()
            if res.data and len(res.data) > 0:
                return res.data[0]
        except Exception as e:
            logger.error(f"Error fetching business config: {e}")
        return {}

# =============================================================================
# SINGLETON INSTANCE
# =============================================================================
db = Database()
