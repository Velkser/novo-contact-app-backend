from sqlalchemy.orm import Session
from typing import List, Optional
from app.models.prompt_template import PromptTemplate
from app.schemas.prompt_template import PromptTemplateCreate, PromptTemplateUpdate

def get_prompt_template(db: Session, template_id: int, user_id: int) -> Optional[PromptTemplate]:
    return db.query(PromptTemplate).filter(
        PromptTemplate.id == template_id,
        PromptTemplate.user_id == user_id,
        PromptTemplate.is_active == True
    ).first()

def get_prompt_templates(db: Session, user_id: int, skip: int = 0, limit: int = 100) -> List[PromptTemplate]:
    return db.query(PromptTemplate).filter(
        PromptTemplate.user_id == user_id,
        PromptTemplate.is_active == True
    ).offset(skip).limit(limit).all()

def create_prompt_template(
    db: Session, 
    template: PromptTemplateCreate, 
    user_id: int
) -> PromptTemplate:
    db_template = PromptTemplate(
        user_id=user_id,
        name=template.name,
        content=template.content
    )
    db.add(db_template)
    db.commit()
    db.refresh(db_template)
    return db_template

def update_prompt_template(
    db: Session, 
    template_id: int, 
    template_update: PromptTemplateUpdate, 
    user_id: int
) -> Optional[PromptTemplate]:
    db_template = get_prompt_template(db, template_id, user_id)
    if db_template:
        update_data = template_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_template, field, value)
        
        db.commit()
        db.refresh(db_template)
    return db_template

def delete_prompt_template(db: Session, template_id: int, user_id: int) -> bool:
    db_template = get_prompt_template(db, template_id, user_id)
    if db_template:
        db_template.is_active = False
        db.commit()
        return True
    return False