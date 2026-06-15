from app.database.connection import get_db
from app.models.lead import MeetingCreate
from datetime import datetime


def meeting_helper(meeting) -> dict:
    return {
        "id": str(meeting["_id"]),
        "meeting_id": meeting["meeting_id"],
        "lead_id": meeting["lead_id"],
        "meeting_date": str(meeting["meeting_date"]),
        "meeting_time": meeting["meeting_time"],
        "attendees": meeting["attendees"],
        "platform": meeting["platform"],
        "outcome_notes": meeting.get("outcome_notes"),
        "requires_ceo": meeting["requires_ceo"],
        "created_by": meeting["created_by"],
        "created_at": meeting["created_at"]
    }


async def generate_meeting_id():
    db = get_db()
    count = await db.meetings.count_documents({})
    return f"MTG-{count + 1:05d}"


async def create_meeting(meeting_data: MeetingCreate, created_by: str):
    db = get_db()

    lead = await db.leads.find_one({"lead_id": meeting_data.lead_id, "is_deleted": False})
    if not lead:
        return None, "Lead not found"

    meeting_id = await generate_meeting_id()

    meeting = {
        "meeting_id": meeting_id,
        "lead_id": meeting_data.lead_id,
        "meeting_date": str(meeting_data.meeting_date),
        "meeting_time": meeting_data.meeting_time,
        "attendees": meeting_data.attendees,
        "platform": meeting_data.platform,
        "outcome_notes": meeting_data.outcome_notes,
        "requires_ceo": meeting_data.requires_ceo,
        "created_by": created_by,
        "created_at": datetime.utcnow()
    }
    result = await db.meetings.insert_one(meeting)
    new_meeting = await db.meetings.find_one({"_id": result.inserted_id})

    # NOTE: CEO notification for "requires_ceo" meetings will be wired up
    # in Phase 6 (Notification System overhaul) via create_notification()

    return meeting_helper(new_meeting), None


async def get_meetings_by_lead(lead_id: str):
    db = get_db()
    meetings = await db.meetings.find({"lead_id": lead_id}).sort("created_at", -1).to_list(1000)
    return [meeting_helper(m) for m in meetings]


async def get_all_meetings(requires_ceo: bool = None):
    db = get_db()
    query = {}
    if requires_ceo is not None:
        query["requires_ceo"] = requires_ceo
    meetings = await db.meetings.find(query).sort("meeting_date", -1).to_list(1000)
    return [meeting_helper(m) for m in meetings]