from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.api import deps
from app.models.user import User
from app.schemas.prompt_template import PromptTemplate, PromptTemplateCreate, PromptTemplateUpdate
from app.crud import prompt_template as crud_template

router = APIRouter(prefix="/prompt-templates", tags=["prompt_templates"])

@router.get("/", response_model=List[PromptTemplate])
def read_prompt_templates(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """Получение списка шаблонов промптов пользователя"""
    templates = crud_template.get_prompt_templates(db, user_id=current_user.id, skip=skip, limit=limit)
    return templates

@router.post("/", response_model=PromptTemplate, status_code=status.HTTP_201_CREATED)
def create_prompt_template(
    template: PromptTemplateCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """Создание нового шаблона промпта"""
    return crud_template.create_prompt_template(db=db, template=template, user_id=current_user.id)

@router.get("/{template_id}", response_model=PromptTemplate)
def read_prompt_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """Получение конкретного шаблона промпта"""
    db_template = crud_template.get_prompt_template(db, template_id=template_id, user_id=current_user.id)
    if db_template is None:
        raise HTTPException(status_code=404, detail="Prompt template not found")
    return db_template

@router.put("/{template_id}", response_model=PromptTemplate)
def update_prompt_template(
    template_id: int,
    template: PromptTemplateUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """Обновление шаблона промпта"""
    db_template = crud_template.update_prompt_template(
        db=db, 
        template_id=template_id, 
        template_update=template, 
        user_id=current_user.id
    )
    if db_template is None:
        raise HTTPException(status_code=404, detail="Prompt template not found")
    return db_template

@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_prompt_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    """Удаление шаблона промпта (soft delete)"""
    success = crud_template.delete_prompt_template(
        db=db, 
        template_id=template_id, 
        user_id=current_user.id
    )
    if not success:
        raise HTTPException(status_code=404, detail="Prompt template not found")
    return