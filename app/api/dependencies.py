"""依赖注入：Session 交给 Service/Repository。"""
from __future__ import annotations

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.repositories.dataset_repository import DatasetRepository
from app.services.dataset_service import DatasetService
from app.services.evaluation_service import EvaluationService


def get_dataset_service(db: Session = Depends(get_db)) -> DatasetService:
    return DatasetService(DatasetRepository(db))


def get_evaluation_service(db: Session = Depends(get_db)) -> EvaluationService:
    return EvaluationService(db)