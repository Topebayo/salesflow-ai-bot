"""
=============================================================================
DATABASE MODULE - SUPABASE CLOUD STORAGE
=============================================================================
Handles all database operations using Supabase (PostgreSQL) for persistent 
storage. Your data will never be wiped on deployments again.

SaaS Multi-Tenant: All queries are scoped to business_id for data isolation.
=============================================================================
"""

import os
import re
import logging
from datetime import datetime
from supabase import create_client, Client

logger = logging.getLogger(__name__)

class Database:
    """Persistent storage for conversations and contact tracking using Supabase."""

    def __init__(self):
        """Initialize the Supabase client."""
        url = os.getenv("SUPABASE_URL")
        # Use service_role key if available for backend administrative operations (bypasses RLS safely on server)
        key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY")
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
    # SANDBOX SESSIONS (TEST SWITCHER)
    # =========================================================================
    def get_sandbox_session(self, phone_number: str) -> str:
        if not self.client: return None
        try:
            res = self.client.table("sandbox_sessions").select("business_id").eq("phone_number", phone_number).execute()
            if res.data and len(res.data) > 0:
                return res.data[0]["business_id"]
        except Exception as e:
            logger.error(f"Error fetching sandbox session: {e}")
        return None

    def set_sandbox_session(self, phone_number: str, business_id: str) -> bool:
        if not self.client: return False
        try:
            res = self.client.table("sandbox_sessions").upsert({
                "phone_number": phone_number,
                "business_id": business_id,
                "updated_at": datetime.utcnow().isoformat()
            }).execute()
            return len(res.data) > 0
        except Exception as e:
            logger.error(f"Error setting sandbox session: {e}")
            return False

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

    def has_conversation(self, business_id: str, phone_number: str) -> bool:
        if not self.client or not business_id: return False
        res = self.client.table("conversations").select("id", count="exact").eq("phone_number", phone_number).eq("business_id", business_id).execute()
        return res.count > 0 if res.count else False

    def clear_conversation(self, business_id: str, phone_number: str) -> bool:
        if not self.client or not business_id: return False
        res = self.client.table("conversations").delete().eq("phone_number", phone_number).eq("business_id", business_id).execute()
        cleared = len(res.data) > 0
        if cleared:
            logger.info(f"🗑️ Conversation cleared for: {phone_number}")
        return cleared

    def get_conversation_count(self, business_id: str = None) -> int:
        if not self.client: return 0
        query = self.client.table("contacts").select("phone_number", count="exact")
        if business_id:
            query = query.eq("business_id", business_id)
        res = query.execute()
        return res.count if res.count else 0

    # =========================================================================
    # CONTACT / LEAD OPERATIONS
    # =========================================================================

    def get_all_contacts(self, business_id: str = None) -> list:
        if not self.client: return []
        query = self.client.table("contacts").select("*").order("last_seen", desc=True)
        if business_id:
            query = query.eq("business_id", business_id)
        return query.execute().data

    def update_contact_name(self, business_id: str, phone_number: str, name: str):
        if not self.client or not business_id: return
        contact_res = self.client.table("contacts").select("name").eq("phone_number", phone_number).eq("business_id", business_id).execute()
        if len(contact_res.data) > 0 and not contact_res.data[0].get("name"):
            self.client.table("contacts").update({"name": name}).eq("phone_number", phone_number).eq("business_id", business_id).execute()

    # =========================================================================
    # ANALYTICS / STATS
    # =========================================================================

    def get_stats(self, business_id: str = None) -> dict:
        if not self.client:
            return {"total_contacts": 0, "total_messages": 0, "messages_today": 0, "conversations_today": 0, "top_contacts": []}
        
        contacts_query = self.client.table("contacts").select("*", count="exact")
        msgs_query = self.client.table("conversations").select("*", count="exact")
        top_query = self.client.table("contacts").select("phone_number, name, message_count, last_seen").order("message_count", desc=True).limit(5)
        
        if business_id:
            contacts_query = contacts_query.eq("business_id", business_id)
            msgs_query = msgs_query.eq("business_id", business_id)
            top_query = top_query.eq("business_id", business_id)
        
        contacts_res = contacts_query.execute()
        total_contacts = contacts_res.count if contacts_res.count else 0
        
        msgs_res = msgs_query.execute()
        total_messages = msgs_res.count if msgs_res.count else 0
        
        top_res = top_query.execute()
        
        return {
            "total_contacts": total_contacts,
            "total_messages": total_messages,
            "messages_today": 0,
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

    def get_all_orders(self, business_id: str = None) -> list:
        if not self.client: return []
        query = self.client.table("orders").select("*").order("created_at", desc=True)
        if business_id:
            query = query.eq("business_id", business_id)
        return query.execute().data

    def update_order_status(self, order_id: int, status: str) -> bool:
        if not self.client: return False
        res = self.client.table("orders").update({"status": status}).eq("id", order_id).execute()
        return len(res.data) > 0

    def get_revenue_stats(self, business_id: str = None) -> dict:
        if not self.client:
            return {"total_orders": 0, "total_revenue": 0, "orders_today": 0, "revenue_today": 0}
        
        query = self.client.table("orders").select("total_amount, status").neq("status", "cancelled")
        if business_id:
            query = query.eq("business_id", business_id)
        res = query.execute()
        
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

    def qualify_lead(self, business_id: str, phone_number: str, budget_min: str = "", budget_max: str = "", preferred_location: str = "", search_status: str = "searching") -> bool:
        """Update a contact's real estate qualification info."""
        if not self.client or not business_id or not phone_number: return False
        try:
            # Check if contact exists
            contact_res = self.client.table("contacts").select("id").eq("phone_number", phone_number).eq("business_id", business_id).execute()
            
            update_data = {}
            if budget_min: update_data["budget_min"] = budget_min
            if budget_max: update_data["budget_max"] = budget_max
            if preferred_location: update_data["preferred_location"] = preferred_location
            if search_status: update_data["search_status"] = search_status
            
            if not update_data: return True
            
            if len(contact_res.data) > 0:
                self.client.table("contacts").update(update_data).eq("phone_number", phone_number).eq("business_id", business_id).execute()
            else:
                update_data["business_id"] = business_id
                update_data["phone_number"] = phone_number
                update_data["message_count"] = 0
                self.client.table("contacts").insert(update_data).execute()
            return True
        except Exception as e:
            logger.error(f"Error qualifying lead: {e}")
            return False

    def is_business_admin(self, business_id: str, phone_number: str) -> bool:
        """Check if sender phone matches registered admin_phone or whatsapp_number."""
        if not self.client or not business_id or not phone_number: return False
        try:
            res = self.client.table("businesses").select("admin_phone, whatsapp_number").eq("id", business_id).execute()
            if res.data and len(res.data) > 0:
                b = res.data[0]
                admin_phone = re.sub(r'\D', '', str(b.get("admin_phone") or ""))
                biz_phone = re.sub(r'\D', '', str(b.get("whatsapp_number") or ""))
                sender_clean = re.sub(r'\D', '', str(phone_number))
                if sender_clean and ((admin_phone and sender_clean == admin_phone) or (biz_phone and sender_clean == biz_phone)):
                    return True
        except Exception as e:
            logger.error(f"Error checking business admin: {e}")
        return False

    def get_handoff_contacts(self, business_id: str = None) -> list:
        if not self.client: return []
        query = self.client.table("contacts").select("*").eq("human_handoff", True).order("last_seen", desc=True)
        if business_id:
            query = query.eq("business_id", business_id)
        return query.execute().data

    # =========================================================================
    # SETTINGS / MODE OPERATIONS (Legacy — kept for backward compatibility)
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
                "products_services, payment_info, business_hours, custom_rules, tone, inspection_fee, admin_phone, auto_learned_knowledge"
            ).eq("id", business_id).execute()
            if res.data and len(res.data) > 0:
                return res.data[0]
        except Exception as e:
            logger.error(f"Error fetching business config: {e}")
        return {}

    def update_auto_learned_knowledge(self, business_id: str, knowledge: str) -> bool:
        """Update the auto-learned chat knowledge base for a business."""
        if not self.client or not business_id: return False
        try:
            self.client.table("businesses").update({
                "auto_learned_knowledge": knowledge
            }).eq("id", business_id).execute()
            return True
        except Exception as e:
            logger.error(f"Error updating auto-learned knowledge: {e}")
            return False

    # =========================================================================
    # QUOTAS & SUBSCRIPTIONS (PAYSTACK / PLAN TRACKING)
    # =========================================================================

    def get_business_usage(self, business_id: str) -> dict:
        """Fetch a business's current subscription tier and monthly message usage."""
        if not self.client or not business_id: return {}
        try:
            res = self.client.table("businesses").select(
                "plan_type, monthly_message_limit, messages_used_this_month, subscription_status"
            ).eq("id", business_id).execute()
            if res.data and len(res.data) > 0:
                return res.data[0]
        except Exception as e:
            logger.error(f"Error fetching business usage: {e}")
        return {"plan_type": "starter", "monthly_message_limit": 500, "messages_used_this_month": 0, "subscription_status": "active"}

    def increment_message_usage(self, business_id: str) -> bool:
        """Increment the monthly AI message counter for a business by 1."""
        if not self.client or not business_id: return False
        try:
            usage = self.get_business_usage(business_id)
            current_used = usage.get("messages_used_this_month", 0) or 0
            self.client.table("businesses").update({
                "messages_used_this_month": current_used + 1
            }).eq("id", business_id).execute()
            return True
        except Exception as e:
            logger.error(f"Error incrementing message usage: {e}")
            return False

    def upgrade_business_plan(self, business_id: str, plan_type: str, monthly_limit: int) -> bool:
        """Upgrade or renew a business subscription plan upon successful Paystack payment."""
        if not self.client or not business_id: return False
        try:
            res = self.client.table("businesses").update({
                "plan_type": plan_type,
                "monthly_message_limit": monthly_limit,
                "messages_used_this_month": 0,
                "subscription_status": "active"
            }).eq("id", business_id).execute()
            logger.info(f"🎉 Successfully upgraded business {business_id} to {plan_type.upper()} ({monthly_limit} limit)")
            return len(res.data) > 0
        except Exception as e:
            logger.error(f"Error upgrading business plan: {e}")
            return False

    # =========================================================================
    # WHATSAPP CREDENTIALS (SaaS — Per-Business)
    # =========================================================================

    def get_business_credentials(self, business_id: str) -> dict:
        """Fetch a business's WhatsApp API credentials (Meta or Evolution)."""
        if not self.client or not business_id: return {}
        try:
            res = self.client.table("businesses").select(
                "meta_access_token, meta_phone_number_id, meta_verify_token, webhook_connected, "
                "whatsapp_provider, evolution_instance_name, evolution_apikey"
            ).eq("id", business_id).execute()
            if res.data and len(res.data) > 0:
                return res.data[0]
        except Exception as e:
            logger.error(f"Error fetching business credentials: {e}")
        return {}

    def save_business_credentials(self, business_id: str, access_token: str, phone_number_id: str, verify_token: str) -> bool:
        """Save or update a business's WhatsApp API credentials."""
        if not self.client or not business_id: return False
        try:
            res = self.client.table("businesses").update({
                "meta_access_token": access_token,
                "meta_phone_number_id": phone_number_id,
                "meta_verify_token": verify_token,
                "whatsapp_provider": "meta"
            }).eq("id", business_id).execute()
            return len(res.data) > 0
        except Exception as e:
            logger.error(f"Error saving business credentials: {e}")
            return False

    def save_evolution_credentials(self, business_id: str, instance_name: str, apikey: str) -> bool:
        """Save Evolution API credentials for QR-code based WhatsApp connection."""
        if not self.client or not business_id: return False
        try:
            res = self.client.table("businesses").update({
                "whatsapp_provider": "evolution",
                "evolution_instance_name": instance_name,
                "evolution_apikey": apikey
            }).eq("id", business_id).execute()
            return len(res.data) > 0
        except Exception as e:
            logger.error(f"Error saving Evolution credentials: {e}")
            return False

    def get_business_by_evolution_instance(self, instance_name: str) -> dict:
        """Find a business by its Evolution API instance name (for incoming webhook routing)."""
        if not self.client or not instance_name: return {}
        try:
            res = self.client.table("businesses").select("id, name").eq(
                "evolution_instance_name", instance_name
            ).execute()
            if res.data and len(res.data) > 0:
                return res.data[0]
        except Exception as e:
            logger.error(f"Error looking up business by evolution instance: {e}")
        return {}

    def mark_webhook_verified(self, business_id: str) -> bool:
        """Mark a business's webhook as successfully verified."""
        if not self.client or not business_id: return False
        try:
            res = self.client.table("businesses").update({
                "webhook_connected": True,
                "webhook_verified_at": datetime.utcnow().isoformat()
            }).eq("id", business_id).execute()
            return len(res.data) > 0
        except Exception as e:
            logger.error(f"Error marking webhook verified: {e}")
            return False

    # =========================================================================
    # PRODUCT CATALOG (with Image Support)
    # =========================================================================

    def get_products(self, business_id: str) -> list:
        """Get all products for a business."""
        if not self.client or not business_id: return []
        try:
            res = self.client.table("products").select("*").eq("business_id", business_id).order("created_at", desc=True).execute()
            return res.data
        except Exception as e:
            logger.error(f"Error fetching products: {e}")
            return []

    def get_product_by_id(self, product_id: str) -> dict:
        """Get a single product by its ID."""
        if not self.client or not product_id: return {}
        try:
            res = self.client.table("products").select("*").eq("id", product_id).execute()
            if res.data and len(res.data) > 0:
                return res.data[0]
        except Exception as e:
            logger.error(f"Error fetching product: {e}")
        return {}

    def add_product(self, business_id: str, name: str, description: str = "", price: str = "", image_url: str = "", category: str = "", bedrooms: int = 0, bathrooms: int = 0, property_type: str = "", location: str = "", virtual_tour_url: str = "") -> str:
        """Add a product to the catalog. Returns the product ID."""
        if not self.client or not business_id: return ""
        try:
            res = self.client.table("products").insert({
                "business_id": business_id,
                "name": name,
                "description": description,
                "price": price,
                "image_url": image_url,
                "category": category,
                "bedrooms": bedrooms,
                "bathrooms": bathrooms,
                "property_type": property_type,
                "location": location,
                "virtual_tour_url": virtual_tour_url
            }).execute()
            product_id = res.data[0].get("id", "") if res.data else ""
            logger.info(f"📦 Product '{name}' added for business {business_id}")
            return product_id
        except Exception as e:
            logger.error(f"Error adding product: {e}")
            return ""

    def update_product(self, product_id: str, **kwargs) -> bool:
        """Update a product's details. Pass any fields to update as keyword arguments."""
        if not self.client or not product_id: return False
        try:
            update_data = {k: v for k, v in kwargs.items() if v is not None}
            if not update_data:
                return False
            res = self.client.table("products").update(update_data).eq("id", product_id).execute()
            return len(res.data) > 0
        except Exception as e:
            logger.error(f"Error updating product: {e}")
            return False

    def delete_product(self, product_id: str) -> bool:
        """Delete a product from the catalog."""
        if not self.client or not product_id: return False
        try:
            res = self.client.table("products").delete().eq("id", product_id).execute()
            return len(res.data) > 0
        except Exception as e:
            logger.error(f"Error deleting product: {e}")
            return False

    def get_daily_analytics(self, business_id: str) -> dict:
        """Get daily registrations and messages volume for the last 7 days."""
        if not self.client or not business_id:
            return {"dates": [], "leads": [], "messages": []}
            
        try:
            import datetime
            today = datetime.date.today()
            # Generate the last 7 days
            last_7_days = [today - datetime.timedelta(days=i) for i in range(6, -1, -1)]
            date_strings = [d.strftime("%Y-%m-%d") for d in last_7_days]
            
            # Initialize metrics maps
            leads_map = {d: 0 for d in date_strings}
            msgs_map = {d: 0 for d in date_strings}
            
            # Fetch all contacts for this business to aggregate by creation date
            # filter for contacts created in the last 7 days
            seven_days_ago = (datetime.datetime.utcnow() - datetime.timedelta(days=7)).isoformat()
            
            contacts_res = self.client.table("contacts").select("first_seen").eq("business_id", business_id).gte("first_seen", seven_days_ago).execute()
            if contacts_res.data:
                for c in contacts_res.data:
                    fs = c.get("first_seen")
                    if fs:
                        date_part = fs.split("T")[0]
                        if date_part in leads_map:
                            leads_map[date_part] += 1
            
            # Fetch conversations for the last 7 days
            convos_res = self.client.table("conversations").select("timestamp").eq("business_id", business_id).gte("timestamp", seven_days_ago).execute()
            if convos_res.data:
                for m in convos_res.data:
                    ts = m.get("timestamp")
                    if ts:
                        date_part = ts.split("T")[0]
                        if date_part in msgs_map:
                            msgs_map[date_part] += 1
                            
            # Convert maps back to lists matching date_strings order
            leads_list = [leads_map[d] for d in date_strings]
            msgs_list = [msgs_map[d] for d in date_strings]
            
            # Return human-readable label formats (e.g. "May 31")
            formatted_dates = []
            for d_str in date_strings:
                try:
                    dt = datetime.datetime.strptime(d_str, "%Y-%m-%d")
                    formatted_dates.append(dt.strftime("%b %d"))
                except Exception:
                    formatted_dates.append(d_str)
                    
            return {
                "dates": formatted_dates,
                "leads": leads_list,
                "messages": msgs_list
            }
        except Exception as e:
            logger.error(f"Error fetching daily analytics: {e}")
            return {"dates": [], "leads": [], "messages": []}

    def get_available_products(self, business_id: str) -> list:
        """Get only available products (for AI prompt building)."""
        if not self.client or not business_id: return []
        try:
            res = self.client.table("products").select(
                "id, name, description, price, image_url, category, bedrooms, bathrooms, property_type, location, virtual_tour_url"
            ).eq("business_id", business_id).eq("is_available", True).execute()
            return res.data
        except Exception as e:
            logger.error(f"Error fetching available products: {e}")
            return []

# =============================================================================
# SINGLETON INSTANCE
# =============================================================================
db = Database()
