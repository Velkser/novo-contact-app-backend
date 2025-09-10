# app/crud/group.py
from sqlalchemy.orm import Session
from typing import List, Optional
from app.models.group import Group, GroupMember, ScheduledGroupCall
from app.models.contact import Contact
from app.schemas.group import GroupCreate, GroupUpdate, GroupMemberCreate, ScheduledGroupCallCreate, ScheduledGroupCallUpdate
from datetime import datetime

def get_group(db: Session, group_id: int, user_id: int) -> Optional[Group]:
    return db.query(Group).filter(
        Group.id == group_id,
        Group.user_id == user_id,
        Group.is_active == True
    ).first()

def get_groups(db: Session, user_id: int, skip: int = 0, limit: int = 100) -> List[Group]:
    return db.query(Group).filter(
        Group.user_id == user_id,
        Group.is_active == True
    ).offset(skip).limit(limit).all()

def create_group(db: Session, group: GroupCreate, user_id: int) -> Group:
    db_group = Group(
        user_id=user_id,
        name=group.name,
        description=group.description
    )
    db.add(db_group)
    db.commit()
    db.refresh(db_group)
    
    # Добавляем участников если указаны
    if group.contact_ids:
        for contact_id in group.contact_ids:
            # Проверяем, что контакт принадлежит пользователю
            contact = db.query(Contact).filter(
                Contact.id == contact_id,
                Contact.user_id == user_id
            ).first()
            
            if contact:
                member = GroupMember(
                    group_id=db_group.id,
                    contact_id=contact_id
                )
                db.add(member)
        
        db.commit()
        db.refresh(db_group)
    
    return db_group

def update_group(db: Session, group_id: int, group_update: GroupUpdate, user_id: int) -> Optional[Group]:
    db_group = get_group(db, group_id, user_id)
    if db_group:
        update_data = group_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_group, field, value)
        db_group.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(db_group)
    return db_group

def delete_group(db: Session, group_id: int, user_id: int) -> bool:
    db_group = get_group(db, group_id, user_id)
    if db_group:
        db_group.is_active = False
        db.commit()
        return True
    return False

# Group Members CRUD
def add_group_member(db: Session, member: GroupMemberCreate, user_id: int) -> Optional[GroupMember]:
    # Проверяем, что группа принадлежит пользователю
    group = get_group(db, member.group_id, user_id)
    if not group:
        return None
    
    # Проверяем, что контакт принадлежит пользователю
    contact = db.query(Contact).filter(
        Contact.id == member.contact_id,
        Contact.user_id == user_id
    ).first()
    
    if not contact:
        return None
    
    # Проверяем, что участник еще не добавлен
    existing_member = db.query(GroupMember).filter(
        GroupMember.group_id == member.group_id,
        GroupMember.contact_id == member.contact_id
    ).first()
    
    if existing_member:
        return existing_member
    
    db_member = GroupMember(
        group_id=member.group_id,
        contact_id=member.contact_id
    )
    db.add(db_member)
    db.commit()
    db.refresh(db_member)
    return db_member

def remove_group_member(db: Session, group_id: int, contact_id: int, user_id: int) -> bool:
    # Проверяем, что группа принадлежит пользователю
    group = get_group(db, group_id, user_id)
    if not group:
        return False
    
    db_member = db.query(GroupMember).filter(
        GroupMember.group_id == group_id,
        GroupMember.contact_id == contact_id
    ).first()
    
    if db_member:
        db.delete(db_member)
        db.commit()
        return True
    return False

def get_group_members(db: Session, group_id: int, user_id: int) -> List[GroupMember]:
    group = get_group(db, group_id, user_id)
    if not group:
        return []
    
    return db.query(GroupMember).filter(
        GroupMember.group_id == group_id
    ).all()

def get_group_contacts(db: Session, group_id: int, user_id: int) -> List[Contact]:
    group = get_group(db, group_id, user_id)
    if not group:
        return []
    
    # Получаем все контакты группы
    member_contacts = db.query(Contact).join(GroupMember).filter(
        GroupMember.group_id == group_id,
        Contact.user_id == user_id,
        Contact.is_active == True
    ).all()
    
    return member_contacts

# Scheduled Group Calls CRUD
def get_scheduled_group_call(db: Session, call_id: int, user_id: int) -> Optional[ScheduledGroupCall]:
    return db.query(ScheduledGroupCall).filter(
        ScheduledGroupCall.id == call_id,
        ScheduledGroupCall.user_id == user_id
    ).first()

def get_scheduled_group_calls(db: Session, user_id: int, skip: int = 0, limit: int = 100) -> List[ScheduledGroupCall]:
    return db.query(ScheduledGroupCall).filter(
        ScheduledGroupCall.user_id == user_id
    ).offset(skip).limit(limit).all()

def create_scheduled_group_call(db: Session, call: ScheduledGroupCallCreate, user_id: int) -> ScheduledGroupCall:
    db_call = ScheduledGroupCall(
        user_id=user_id,
        group_id=call.group_id,
        start_time_window=call.start_time_window,
        end_time_window=call.end_time_window,
        script=call.script,
        notes=call.notes,
        retry_until_success=call.retry_until_success or False,
        retry_interval=call.retry_interval or 60
    )
    db.add(db_call)
    db.commit()
    db.refresh(db_call)
    return db_call

def update_scheduled_group_call(
    db: Session, 
    call_id: int, 
    call_update: ScheduledGroupCallUpdate, 
    user_id: int
) -> Optional[ScheduledGroupCall]:
    db_call = get_scheduled_group_call(db, call_id, user_id)
    if db_call:
        update_data = call_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_call, field, value)
        db_call.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(db_call)
    return db_call

def delete_scheduled_group_call(db: Session, call_id: int, user_id: int) -> bool:
    db_call = get_scheduled_group_call(db, call_id, user_id)
    if db_call:
        db.delete(db_call)
        db.commit()
        return True
    return False

def get_group_scheduled_calls(db: Session, group_id: int, user_id: int) -> List[ScheduledGroupCall]:
    group = get_group(db, group_id, user_id)
    if not group:
        return []
    
    # возвращаем все запланированные звонки без поля scheduled_time
    return db.query(ScheduledGroupCall).filter(
        ScheduledGroupCall.group_id == group_id,
        ScheduledGroupCall.user_id == user_id
    ).all()
