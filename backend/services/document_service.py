# services/document_service.py

from sqlalchemy.orm import Session
from database.models import Document, AgentResult
from typing import List, Optional, Dict, Any


def create_document(
    db: Session,
    user_id: int,
    file_id: str,
    filename: str,
    original_name: str,
    size_mb: float
) -> Document:
    doc = Document(
        user_id=user_id,
        file_id=file_id,
        filename=filename,
        original_name=original_name,
        size_mb=size_mb,
        is_embedded=False
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


def get_user_documents(db: Session, user_id: int) -> List[Document]:
    return db.query(Document)\
             .filter(Document.user_id == user_id)\
             .order_by(Document.uploaded_at.desc())\
             .all()


def get_document_by_file_id(
    db: Session,
    file_id: str,
    user_id: int
) -> Optional[Document]:
    return db.query(Document)\
             .filter(
                 Document.file_id == file_id,
                 Document.user_id == user_id
             ).first()


def mark_document_embedded(
    db: Session,
    file_id: str,
    user_id: int,
    total_chunks: int
) -> Optional[Document]:
    doc = get_document_by_file_id(db, file_id, user_id)
    if doc:
        doc.is_embedded = True
        doc.total_chunks = total_chunks
        db.commit()
        db.refresh(doc)
    return doc


def save_agent_result(
    db: Session,
    user_id: int,
    agent_type: str,
    input_data: Dict[str, Any],
    result_data: Dict[str, Any],
    urgency_level: str = None
) -> AgentResult:
    result = AgentResult(
        user_id=user_id,
        agent_type=agent_type,
        input_data=input_data,
        result_data=result_data,
        urgency_level=urgency_level
    )
    db.add(result)
    db.commit()
    db.refresh(result)
    return result


def get_user_agent_results(
    db: Session,
    user_id: int,
    agent_type: str = None,
    limit: int = 10
) -> List[AgentResult]:
    query = db.query(AgentResult)\
              .filter(AgentResult.user_id == user_id)

    if agent_type:
        query = query.filter(AgentResult.agent_type == agent_type)

    return query.order_by(AgentResult.created_at.desc())\
                .limit(limit)\
                .all()