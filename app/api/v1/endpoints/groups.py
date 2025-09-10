# app/api/v1/endpoints/groups.py
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.api import deps
from app.models.user import User
from app.models.contact import Contact
from app.models.group import Group, GroupMember
from app.schemas.group import (
    Group, GroupCreate, GroupUpdate, GroupResponse,
    GroupMember, GroupMemberCreate,
    ScheduledGroupCall, ScheduledGroupCallCreate, ScheduledGroupCallUpdate
)
from app.crud.group import (
    get_group, get_groups, create_group, update_group, delete_group,
    add_group_member, remove_group_member, get_group_members,
    get_scheduled_group_call, get_scheduled_group_calls, create_scheduled_group_call,
    update_scheduled_group_call, delete_scheduled_group_call
)
import logging

logger = logging.getLogger(__name__)

# 🔥 Исправлено: разделили маршруты для групп и запланированных звонков
router = APIRouter(prefix="/groups", tags=["groups"])
scheduled_calls_router = APIRouter(prefix="/scheduled-group-calls", tags=["scheduled_group_calls"])  # ← Новый роутер

# Groups endpoints
@router.get("/", response_model=List[GroupResponse])
def read_groups(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """Получение списка групп пользователя с участниками"""
    try:
        logger.info(f"Fetching groups for user {current_user.id}")
        groups = get_groups(db, user_id=current_user.id, skip=skip, limit=limit)
        
        # Добавляем информацию об участниках и контактах для каждой группы
        groups_with_details = []
        for group in groups:
            members = get_group_members(db, group_id=group.id, user_id=current_user.id)
            
            # Получаем контакты участников
            contacts = []
            for member in members:
                contact = db.query(Contact).filter(
                    Contact.id == member.contact_id,
                    Contact.user_id == current_user.id,
                    Contact.is_active == True
                ).first()
                if contact:
                    contacts.append(contact)
            
            # Создаем GroupResponse с деталями
            group_response = GroupResponse(
                id=group.id,
                user_id=group.user_id,
                name=group.name,
                description=group.description,
                is_active=group.is_active,
                created_at=group.created_at,
                updated_at=group.updated_at,
                members=members,
                contacts=contacts,
                member_count=len(members),
                scheduled_calls_count=0  # Пока не реализовано
            )
            groups_with_details.append(group_response)
        
        logger.info(f"Found {len(groups_with_details)} groups")
        return groups_with_details
    except Exception as e:
        logger.error(f"Error fetching groups: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/", response_model=GroupResponse, status_code=status.HTTP_201_CREATED)
def create_group_endpoint(
    group: GroupCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """Создание новой группы с участниками"""
    try:
        logger.info(f"Creating group for user {current_user.id}: {group.name}")
        new_group = create_group(db=db, group=group, user_id=current_user.id)
        
        # Если указаны участники, добавляем их
        if group.contact_ids:
            for contact_id in group.contact_ids:
                try:
                    add_group_member(db, new_group.id, contact_id)
                except Exception as e:
                    logger.warning(f"Failed to add member {contact_id} to group {new_group.id}: {e}")
        
        # Получаем участников группы
        members = get_group_members(db, group_id=group.id, user_id=current_user.id)
        
        # Получаем контакты участников
        contacts = []
        for member in members:
            contact = db.query(Contact).filter(
                Contact.id == member.contact_id,
                Contact.user_id == current_user.id,
                Contact.is_active == True
            ).first()
            if contact:
                contacts.append(contact)
        
        # Создаем GroupResponse с деталями
        group_response = GroupResponse(
            id=new_group.id,
            user_id=new_group.user_id,
            name=new_group.name,
            description=new_group.description,
            is_active=new_group.is_active,
            created_at=new_group.created_at,
            updated_at=new_group.updated_at,
            members=members,
            contacts=contacts,
            member_count=len(members),
            scheduled_calls_count=0
        )
        
        logger.info(f"Group created successfully: {new_group.id}")
        return group_response
    except Exception as e:
        logger.error(f"Error creating group: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{group_id}", response_model=GroupResponse)
def read_group(
    group_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """Получение конкретной группы с участниками"""
    try:
        logger.info(f"Fetching group {group_id} for user {current_user.id}")
        db_group = get_group(db, group_id=group_id, user_id=current_user.id)
        if db_group is None:
            logger.warning(f"Group {group_id} not found for user {current_user.id}")
            raise HTTPException(status_code=404, detail="Group not found")
        
        # Получаем участников группы
        members = get_group_members(db, group_id=db_group.id, user_id=current_user.id)
        
        # Получаем контакты участников
        contacts = []
        for member in members:
            contact = db.query(Contact).filter(
                Contact.id == member.contact_id,
                Contact.user_id == current_user.id,
                Contact.is_active == True
            ).first()
            if contact:
                contacts.append(contact)
        
        # Создаем GroupResponse с деталями
        group_response = GroupResponse(
            id=db_group.id,
            user_id=db_group.user_id,
            name=db_group.name,
            description=db_group.description,
            is_active=db_group.is_active,
            created_at=db_group.created_at,
            updated_at=db_group.updated_at,
            members=members,
            contacts=contacts,
            member_count=len(members),
            scheduled_calls_count=0
        )
        
        logger.info(f"Group found: {db_group.name}")
        return group_response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching group {group_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{group_id}", response_model=GroupResponse)
def update_group_endpoint(
    group_id: int,
    group_update: GroupUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """Обновление группы с участниками"""
    try:
        logger.info(f"Updating group {group_id} for user {current_user.id}")
        db_group = update_group(
            db=db, 
            group_id=group_id, 
            group_update=group_update, 
            user_id=current_user.id
        )
        if db_group is None:
            logger.warning(f"Group {group_id} not found for user {current_user.id}")
            raise HTTPException(status_code=404, detail="Group not found")
        
        # Получаем участников группы
        members = get_group_members(db, group_id=db_group.id, user_id=current_user.id)
        
        # Получаем контакты участников
        contacts = []
        for member in members:
            contact = db.query(Contact).filter(
                Contact.id == member.contact_id,
                Contact.user_id == current_user.id,
                Contact.is_active == True
            ).first()
            if contact:
                contacts.append(contact)
        
        # Создаем GroupResponse с деталями
        group_response = GroupResponse(
            id=db_group.id,
            user_id=db_group.user_id,
            name=db_group.name,
            description=db_group.description,
            is_active=db_group.is_active,
            created_at=db_group.created_at,
            updated_at=db_group.updated_at,
            members=members,
            contacts=contacts,
            member_count=len(members),
            scheduled_calls_count=0
        )
        
        logger.info(f"Group updated successfully: {db_group.name}")
        return group_response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating group {group_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_group_endpoint(
    group_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """Удаление группы (soft delete)"""
    try:
        logger.info(f"Deleting group {group_id} for user {current_user.id}")
        success = delete_group(
            db=db, 
            group_id=group_id, 
            user_id=current_user.id
        )
        if not success:
            logger.warning(f"Group {group_id} not found for user {current_user.id}")
            raise HTTPException(status_code=404, detail="Group not found")
        logger.info(f"Group deleted successfully: {group_id}")
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting group {group_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Group Members endpoints
@router.post("/{group_id}/members", response_model=GroupMember, status_code=status.HTTP_201_CREATED)
def add_group_member_endpoint(
    group_id: int,
    member_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """Добавление участника в группу"""
    try:
        logger.info(f"Adding member {member_data.get('contact_id')} to group {group_id} for user {current_user.id}")
        
        # Проверяем, что группа принадлежит пользователю
        group = get_group(db, group_id=group_id, user_id=current_user.id)
        if not group:
            logger.warning(f"Group {group_id} not found for user {current_user.id}")
            raise HTTPException(status_code=404, detail="Group not found")
        
        # Проверяем, что контакт принадлежит пользователю
        contact = db.query(Contact).filter(
            Contact.id == member_data.get('contact_id'),
            Contact.user_id == current_user.id,
            Contact.is_active == True
        ).first()
        
        if not contact:
            logger.warning(f"Contact {member_data.get('contact_id')} not found for user {current_user.id}")
            raise HTTPException(status_code=404, detail="Contact not found")
        
        new_member = add_group_member(
            db=db, 
            group_id=group_id, 
            contact_id=member_data.get('contact_id')
        )
        
        if not new_member:
            logger.error(f"Failed to add member {member_data.get('contact_id')} to group {group_id}")
            raise HTTPException(status_code=500, detail="Failed to add group member")
        
        logger.info(f"Member added successfully: {new_member.id}")
        return new_member
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding group member: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{group_id}/members/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_group_member_endpoint(
    group_id: int,
    contact_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """Удаление участника из группы"""
    try:
        logger.info(f"Removing member {contact_id} from group {group_id} for user {current_user.id}")
        
        # Проверяем, что группа принадлежит пользователю
        group = get_group(db, group_id=group_id, user_id=current_user.id)
        if not group:
            logger.warning(f"Group {group_id} not found for user {current_user.id}")
            raise HTTPException(status_code=404, detail="Group not found")
        
        success = remove_group_member(
            db=db, 
            group_id=group_id, 
            contact_id=contact_id
        )
        
        if not success:
            logger.warning(f"Group member {contact_id} not found in group {group_id}")
            raise HTTPException(status_code=404, detail="Group member not found")
        
        logger.info(f"Member removed successfully: {contact_id}")
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing group member: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{group_id}/members", response_model=List[GroupMember])
def get_group_members_endpoint(
    group_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """Получение всех участников группы"""
    try:
        logger.info(f"Fetching members for group {group_id} for user {current_user.id}")
        
        # Проверяем, что группа принадлежит пользователю
        group = get_group(db, group_id=group_id, user_id=current_user.id)
        if not group:
            logger.warning(f"Group {group_id} not found for user {current_user.id}")
            raise HTTPException(status_code=404, detail="Group not found")
        
        members = get_group_members(db, group_id=group_id, user_id=current_user.id)
        logger.info(f"Found {len(members)} members")
        return members
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching group members: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 🔥 Scheduled Group Calls endpoints (новый роутер)
@scheduled_calls_router.get("/", response_model=List[ScheduledGroupCall])
def read_scheduled_group_calls(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """Получение списка запланированных звонков для групп"""
    try:
        logger.info(f"Fetching scheduled group calls for user {current_user.id}")
        calls = get_scheduled_group_calls(db, user_id=current_user.id, skip=skip, limit=limit)
        logger.info(f"Found {len(calls)} scheduled group calls")
        return calls
    except Exception as e:
        logger.error(f"Error fetching scheduled group calls: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@scheduled_calls_router.post("/", response_model=ScheduledGroupCall, status_code=status.HTTP_201_CREATED)
def create_scheduled_group_call_endpoint(
    call: ScheduledGroupCallCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """Создание запланированного звонка для группы"""
    try:
        logger.info(f"Creating scheduled group call for user {current_user.id}, group {call.group_id}")
        
        # Проверяем, что группа принадлежит пользователю
        group = get_group(db, group_id=call.group_id, user_id=current_user.id)
        if not group:
            logger.warning(f"Group {call.group_id} not found for user {current_user.id}")
            raise HTTPException(status_code=404, detail="Group not found")
        
        new_call = create_scheduled_group_call(db=db, call=call, user_id=current_user.id)
        logger.info(f"Scheduled group call created successfully: {new_call.id}")
        return new_call
    except Exception as e:
        logger.error(f"Error creating scheduled group call: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@scheduled_calls_router.get("/{call_id}", response_model=ScheduledGroupCall)
def read_scheduled_group_call(
    call_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """Получение конкретного запланированного звонка для группы"""
    try:
        logger.info(f"Fetching scheduled group call {call_id} for user {current_user.id}")
        db_call = get_scheduled_group_call(db, call_id=call_id, user_id=current_user.id)
        if db_call is None:
            logger.warning(f"Scheduled group call {call_id} not found for user {current_user.id}")
            raise HTTPException(status_code=404, detail="Scheduled group call not found")
        logger.info(f"Scheduled group call found: {db_call.id}")
        return db_call
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching scheduled group call {call_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@scheduled_calls_router.put("/{call_id}", response_model=ScheduledGroupCall)
def update_scheduled_group_call_endpoint(
    call_id: int,
    call_update: ScheduledGroupCallUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """Обновление запланированного звонка для группы"""
    try:
        logger.info(f"Updating scheduled group call {call_id} for user {current_user.id}")
        db_call = update_scheduled_group_call(
            db=db, 
            call_id=call_id, 
            call_update=call_update, 
            user_id=current_user.id
        )
        if db_call is None:
            logger.warning(f"Scheduled group call {call_id} not found for user {current_user.id}")
            raise HTTPException(status_code=404, detail="Scheduled group call not found")
        logger.info(f"Scheduled group call updated successfully: {db_call.id}")
        return db_call
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating scheduled group call {call_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@scheduled_calls_router.delete("/{call_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_scheduled_group_call_endpoint(
    call_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """Удаление запланированного звонка для группы"""
    try:
        logger.info(f"Deleting scheduled group call {call_id} for user {current_user.id}")
        success = delete_scheduled_group_call(
            db=db, 
            call_id=call_id, 
            user_id=current_user.id
        )
        if not success:
            logger.warning(f"Scheduled group call {call_id} not found for user {current_user.id}")
            raise HTTPException(status_code=404, detail="Scheduled group call not found")
        logger.info(f"Scheduled group call deleted successfully: {call_id}")
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting scheduled group call {call_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))