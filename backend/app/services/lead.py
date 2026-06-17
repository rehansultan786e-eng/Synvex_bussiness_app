from app.database.connection import get_db
from app.models.lead import LeadCreate, LeadUpdate
from app.services.audit_log import log_action
from datetime import datetime
from bson import ObjectId


def lead_helper(lead) -> dict:
    return {
        "id": str(lead["_id"]),
        "lead_id": lead["lead_id"],
        "sales_rep_id": lead["sales_rep_id"],
        "sales_rep_name": lead["sales_rep_name"],
        "client_name": lead["client_name"],
        "platform": lead["platform"],
        "contact_email": lead.get("contact_email"),
        "contact_phone": lead.get("contact_phone"),
        "service_required": lead["service_required"],
        "estimated_value": lead["estimated_value"],
        "currency": lead["currency"],
        "status": lead["status"],
        "first_contact_date": str(lead["first_contact_date"]),
        "notes": lead.get("notes"),
        "created_at": lead["created_at"],
        "updated_at": lead.get("updated_at")
    }


async def generate_lead_id():
    db = get_db()
    count = await db.leads.count_documents({})
    return f"LEAD-{count + 1:05d}"


async def create_lead(
    lead_data: LeadCreate, 
    sales_rep_id: str, 
    sales_rep_name: str,
    actor_id: str = "system",
    actor_name: str = "System Automated",
    actor_role: str = "system"
):
    db = get_db()
    lead_id = await generate_lead_id()

    lead = {
        "lead_id": lead_id,
        "sales_rep_id": sales_rep_id,
        "sales_rep_name": sales_rep_name,
        "client_name": lead_data.client_name,
        "platform": lead_data.platform,
        "contact_email": lead_data.contact_email,
        "contact_phone": lead_data.contact_phone,
        "service_required": lead_data.service_required,
        "estimated_value": lead_data.estimated_value,
        "currency": lead_data.currency,
        "status": "New",
        "first_contact_date": str(lead_data.first_contact_date),
        "notes": lead_data.notes,
        "is_deleted": False,
        "created_at": datetime.utcnow()
    }
    result = await db.leads.insert_one(lead)
    new_lead = await db.leads.find_one({"_id": result.inserted_id})
    
    audit_payload = lead_helper(new_lead)
    
    # Trigger Audit Log
    await log_action(
        user_id=actor_id,
        user_name=actor_name,
        user_role=actor_role,
        action="CREATE",
        entity="lead",
        entity_id=lead_id,
        old_value=None,
        new_value=audit_payload,
        description=f"Logged new sales pipeline opportunity {lead_id} for client '{lead_data.client_name}' via {lead_data.platform}."
    )
    
    return audit_payload


async def get_all_leads(status: str = None, sales_rep_id: str = None, platform: str = None):
    db = get_db()
    query = {"is_deleted": False}
    if status:
        query["status"] = status
    if sales_rep_id:
        query["sales_rep_id"] = sales_rep_id
    if platform:
        query["platform"] = platform

    leads = await db.leads.find(query).sort("created_at", -1).to_list(1000)
    return [lead_helper(l) for l in leads]


async def get_lead_by_id(lead_id: str):
    db = get_db()
    lead = await db.leads.find_one({"lead_id": lead_id, "is_deleted": False})
    if lead:
        return lead_helper(lead)
    return None


async def update_lead(
    lead_id: str, 
    lead_data: LeadUpdate, 
    updated_by_role: str,
    actor_id: str = "system",
    actor_name: str = "System Automated"
):
    """
    When status changes to "Won", a commission record is created automatically.
    Only super_admin (CEO) can confirm a "Won" status per SRS 3.2.1.
    """
    db = get_db()
    lead = await db.leads.find_one({"lead_id": lead_id, "is_deleted": False})
    if not lead:
        return None, "Lead not found"

    old_payload = lead_helper(lead)
    update_data = {k: v for k, v in lead_data.model_dump().items() if v is not None}

    new_status = update_data.get("status")
    if new_status == "Won" and lead["status"] != "Won":
        if updated_by_role != "super_admin":
            return None, "Only the CEO can confirm a deal as Won"

    update_data["updated_at"] = datetime.utcnow()
    await db.leads.update_one({"lead_id": lead_id}, {"$set": update_data})

    updated_lead = await get_lead_by_id(lead_id)
    became_won = (new_status == "Won" and lead["status"] != "Won")
    
    # Trigger Audit Log
    await log_action(
        user_id=actor_id,
        user_name=actor_name,
        user_role=updated_by_role,
        action="UPDATE",
        entity="lead",
        entity_id=lead_id,
        old_value=old_payload,
        new_value=updated_lead,
        description=f"Updated parameters for pipeline opportunity {lead_id}. Status transitioned from '{lead['status']}' to '{new_status or lead['status']}'."
    )

    return updated_lead, ("WON_TRANSITION" if became_won else None)


async def delete_lead(
    lead_id: str,
    actor_id: str = "system",
    actor_name: str = "System Automated",
    actor_role: str = "system"
):
    db = get_db()
    lead = await db.leads.find_one({"lead_id": lead_id, "is_deleted": False})
    if not lead:
        return False
        
    old_payload = lead_helper(lead)
    
    await db.leads.update_one(
        {"lead_id": lead_id},
        {"$set": {"is_deleted": True, "updated_at": datetime.utcnow()}}
    )
    
    # Trigger Audit Log
    await log_action(
        user_id=actor_id,
        user_name=actor_name,
        user_role=actor_role,
        action="DELETE",
        entity="lead",
        entity_id=lead_id,
        old_value=old_payload,
        new_value={"is_deleted": True},
        description=f"Soft deleted pipeline deal structure for lead file index: {lead_id}."
    )
    
    return True