"""
Seed script for development / demo purposes.
Run with: python -m app.seed
Idempotent: safe to re-run, it wipes and recreates all tables.
"""
from datetime import datetime, timedelta

from app.database import Base, engine, SessionLocal
from app.models import (
    User, UserRole, Complaint, ComplaintHistory, ComplaintStatus,
    ComplaintPriority, HistoryEventType, Notice,
)
from app.auth import hash_password


def run():
    print("Resetting database...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        admin = User(
            name="Priya Nair", email="admin@societyhub.dev",
            hashed_password=hash_password("AdminPass123!"),
            role=UserRole.ADMIN, flat_number=None,
        )
        residents = [
            User(name="Arjun Mehta", email="arjun.mehta@societyhub.dev",
                 hashed_password=hash_password("ResidentPass123!"),
                 role=UserRole.RESIDENT, flat_number="A-204"),
            User(name="Kavya Iyer", email="kavya.iyer@societyhub.dev",
                 hashed_password=hash_password("ResidentPass123!"),
                 role=UserRole.RESIDENT, flat_number="B-101"),
            User(name="Rahul Sharma", email="rahul.sharma@societyhub.dev",
                 hashed_password=hash_password("ResidentPass123!"),
                 role=UserRole.RESIDENT, flat_number="C-305"),
        ]
        db.add(admin)
        db.add_all(residents)
        db.flush()

        def make_complaint(resident, category, description, status_, priority, days_ago, note=None):
            created = datetime.utcnow() - timedelta(days=days_ago)
            c = Complaint(
                reference_code=Complaint.generate_reference_code(),
                resident_id=resident.id, category=category, description=description,
                status=status_, priority=priority, created_at=created, updated_at=created,
            )
            db.add(c)
            db.flush()
            db.add(ComplaintHistory(
                complaint_id=c.id, event_type=HistoryEventType.CREATED,
                new_status=ComplaintStatus.OPEN, new_priority=ComplaintPriority.MEDIUM,
                actor_id=resident.id, actor_name=resident.name,
                note="Complaint submitted by resident.", created_at=created,
            ))
            if status_ != ComplaintStatus.OPEN:
                db.add(ComplaintHistory(
                    complaint_id=c.id, event_type=HistoryEventType.STATUS_CHANGE,
                    previous_status=ComplaintStatus.OPEN, new_status=status_,
                    actor_id=admin.id, actor_name=admin.name,
                    note=note or "Status updated by maintenance team.",
                    created_at=created + timedelta(hours=4),
                ))
            if status_ == ComplaintStatus.RESOLVED:
                c.resolved_at = created + timedelta(hours=8)
            if priority != ComplaintPriority.MEDIUM:
                db.add(ComplaintHistory(
                    complaint_id=c.id, event_type=HistoryEventType.PRIORITY_CHANGE,
                    previous_priority=ComplaintPriority.MEDIUM, new_priority=priority,
                    actor_id=admin.id, actor_name=admin.name,
                    note="Priority reassessed.", created_at=created + timedelta(hours=1),
                ))
            return c

        make_complaint(residents[0], "Plumbing", "Kitchen sink has been leaking steadily for two days and water is pooling under the cabinet.",
                        ComplaintStatus.OPEN, ComplaintPriority.HIGH, days_ago=5)
        make_complaint(residents[1], "Electrical", "Common corridor light on the 1st floor flickers and switches off intermittently.",
                        ComplaintStatus.IN_PROGRESS, ComplaintPriority.MEDIUM, days_ago=2,
                        note="Electrician scheduled for inspection.")
        make_complaint(residents[2], "Elevator", "Elevator in C wing makes a loud grinding noise on the way up.",
                        ComplaintStatus.OPEN, ComplaintPriority.HIGH, days_ago=4)
        make_complaint(residents[0], "Housekeeping", "Garbage from the ground floor bin was not collected for three days.",
                        ComplaintStatus.RESOLVED, ComplaintPriority.LOW, days_ago=6,
                        note="Collection schedule corrected with housekeeping vendor.")
        make_complaint(residents[1], "Security", "Main gate boom barrier is not closing automatically after vehicles pass.",
                        ComplaintStatus.IN_PROGRESS, ComplaintPriority.HIGH, days_ago=1,
                        note="Vendor informed, awaiting technician visit.")
        make_complaint(residents[2], "Plumbing", "Low water pressure on the 3rd floor during morning hours.",
                        ComplaintStatus.RESOLVED, ComplaintPriority.MEDIUM, days_ago=8,
                        note="Booster pump serviced and pressure restored.")

        notices_data = [
            ("Water supply maintenance on Sunday", "Water supply will be shut off from 9 AM to 1 PM on Sunday for tank cleaning.", True),
            ("Diwali celebration in the clubhouse", "Join us for the annual Diwali get-together in the clubhouse this Saturday at 7 PM.", False),
            ("Parking re-allocation notice", "Two-wheeler parking will be re-allocated to the basement level starting next month.", True),
            ("Society AGM scheduled", "The Annual General Meeting will be held in the community hall next Friday at 6:30 PM.", False),
        ]
        for title, content, important in notices_data:
            db.add(Notice(title=title, content=content, is_important=important,
                           author_id=admin.id, author_name=admin.name))

        db.commit()
        print("Seed complete.")
        print("Admin login:    admin@societyhub.dev / AdminPass123!")
        print("Resident login: arjun.mehta@societyhub.dev / ResidentPass123!")
    finally:
        db.close()


if __name__ == "__main__":
    run()
