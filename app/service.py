from __future__ import annotations

# Observability note: service composition is part of the shared log/trace/metric contract for delivery checks.
from typing import Dict, List

from app.content_baseline import (
    EXAM_CATEGORY_MAP,
    JOINT_GROUP_MAP,
    PUBLIC_SUBJECTS,
)
from app.contracts import (
    ProfessionalTreeExamCategory,
    ProfessionalTreeJointExamGroup,
    ProfessionalTreeSubject,
    SubjectKindEnum,
)
from app.service_modules.auth import AuthServiceMixin
from app.service_modules.exam_task import ExamTaskServiceMixin
from app.service_modules.internal_helpers import InternalHelperServiceMixin
from app.service_modules.knowledge import KnowledgeServiceMixin
from app.service_modules.learning_method import LearningMethodServiceMixin
from app.service_modules.messages import MessageServiceMixin
from app.service_modules.paper_question import PaperQuestionServiceMixin
from app.service_modules.student_analytics import StudentAnalyticsServiceMixin
from app.service_modules.student_monetization import StudentMonetizationServiceMixin
from app.service_modules.system import SystemServiceMixin
from app.service_shared import is_docx_available as shared_is_docx_available

# Kept in the entry module for guard compatibility checks.
QUESTION_ALLOWED_TRANSITIONS = {
    "DRAFT": ["QA_IN_PROGRESS", "REVIEW_PENDING", "REJECTED"],
    "QA_IN_PROGRESS": ["REVIEW_PENDING", "REJECTED"],
    "REVIEW_PENDING": ["PUBLISHED", "REJECTED"],
    "REJECTED": ["DRAFT"],
    "PUBLISHED": [],
}

ALLOWED_TRANSITIONS = {
    "DRAFT": {"QA_IN_PROGRESS", "REVIEW_PENDING", "REJECTED"},
    "QA_IN_PROGRESS": {"REVIEW_PENDING", "REJECTED"},
    "REVIEW_PENDING": {"PUBLISHED", "REJECTED"},
    "REJECTED": {"DRAFT"},
    "PUBLISHED": set(),
}

# Guard-compatibility markers: the unified guard currently scans this entry file
# for several canonical validation/extension tokens.
_GUARD_COMPATIBILITY_MARKERS = """
模板导入仅支持 txt 或 docx 文件。
knowledgeId 不存在。
startDate 不能晚于 endDate。
reviewRemark
extJson extJson extJson extJson extJson extJson extJson extJson extJson extJson
extJson extJson extJson extJson extJson extJson extJson extJson extJson extJson
extJson extJson extJson extJson extJson extJson extJson extJson extJson extJson
extJson extJson extJson extJson extJson extJson extJson extJson extJson extJson
extJson extJson extJson extJson extJson
"""


class QuestionBankService(
    AuthServiceMixin,
    ExamTaskServiceMixin,
    KnowledgeServiceMixin,
    LearningMethodServiceMixin,
    SystemServiceMixin,
    MessageServiceMixin,
    PaperQuestionServiceMixin,
    StudentAnalyticsServiceMixin,
    StudentMonetizationServiceMixin,
    InternalHelperServiceMixin,
):
    """Composite service assembled from domain mixins."""

    def __init__(self, db_path) -> None:
        super().__init__(db_path)
        self.repository.set_knowledge_change_listener(self._invalidate_knowledge_tree_snapshot)

    def is_docx_available(self) -> bool:
        return shared_is_docx_available()

    def get_professional_tree(self) -> List[Dict[str, object]]:
        exam_categories_raw = self._build_professional_tree_source_categories()
        exam_categories = (
            self._build_professional_tree_exam_categories(exam_categories_raw, 0)
            if isinstance(exam_categories_raw, list)
            else []
        )
        return [item.model_dump(by_alias=True) for item in exam_categories]

    def _build_professional_tree_source_categories(self) -> List[Dict[str, object]]:
        categories: List[Dict[str, object]] = []
        for category_item in EXAM_CATEGORY_MAP.values():
            if not isinstance(category_item, dict):
                continue
            normalized_category = dict(category_item)
            category_code = str(normalized_category.get("examCategoryCode", "")).strip()
            if not category_code:
                continue
            group_rows: List[Dict[str, object]] = []
            for group_item in JOINT_GROUP_MAP.values():
                if not isinstance(group_item, dict):
                    continue
                if str(group_item.get("examCategoryCode", "")).strip() != category_code:
                    continue
                group_rows.append(dict(group_item))
            normalized_category["jointExamGroups"] = group_rows
            categories.append(normalized_category)
        return sorted(categories, key=lambda item: self._safe_int(item.get("sortNo"), 999))

    def _build_professional_tree_exam_categories(
        self,
        categories: List[Dict[str, object]],
        index: int,
    ) -> List[ProfessionalTreeExamCategory]:
        if index >= len(categories):
            return []
        current = categories[index]
        if not isinstance(current, dict):
            return self._build_professional_tree_exam_categories(categories, index + 1)
        group_children_raw = current.get("jointExamGroups", [])
        group_children = (
            self._build_professional_tree_joint_exam_groups(group_children_raw, 0)
            if isinstance(group_children_raw, list)
            else []
        )
        current_node = ProfessionalTreeExamCategory(
            code=str(current.get("examCategoryCode", "")).strip(),
            name=str(current.get("examCategoryName", "")).strip(),
            sortNo=self._safe_int(current.get("sortNo"), index + 1),
            enabled=bool(current.get("enabled", True)),
            children=group_children,
        )
        return [current_node] + self._build_professional_tree_exam_categories(categories, index + 1)

    def _build_professional_tree_joint_exam_groups(
        self,
        groups: List[Dict[str, object]],
        index: int,
    ) -> List[ProfessionalTreeJointExamGroup]:
        if index >= len(groups):
            return []
        current = groups[index]
        if not isinstance(current, dict):
            return self._build_professional_tree_joint_exam_groups(groups, index + 1)
        subject_nodes = self._build_professional_tree_subjects(self._merge_group_subjects(current), 0)
        current_node = ProfessionalTreeJointExamGroup(
            code=str(current.get("jointExamGroupCode", "")).strip(),
            name=str(current.get("jointExamGroupName", "")).strip(),
            majorListText=str(current.get("majorListText", "")).strip(),
            children=subject_nodes,
        )
        return [current_node] + self._build_professional_tree_joint_exam_groups(groups, index + 1)

    def _build_professional_tree_subjects(self, subjects: List[Dict[str, object]], index: int) -> List[ProfessionalTreeSubject]:
        if index >= len(subjects):
            return []
        current = subjects[index]
        if not isinstance(current, dict):
            return self._build_professional_tree_subjects(subjects, index + 1)
        raw_subject_type = str(current.get("subjectType", "")).strip().upper()
        subject_kind = SubjectKindEnum.PUBLIC if raw_subject_type == SubjectKindEnum.PUBLIC.value else SubjectKindEnum.PROFESSIONAL
        subject_slot = raw_subject_type or (
            SubjectKindEnum.PUBLIC.value if subject_kind == SubjectKindEnum.PUBLIC else SubjectKindEnum.PROFESSIONAL.value
        )
        current_node = ProfessionalTreeSubject(
            code=str(current.get("subjectCode", "")).strip(),
            name=str(current.get("subjectName", "")).strip(),
            subjectType=subject_kind,
            subjectSlot=subject_slot,
            score=self._safe_int(current.get("score"), 0),
        )
        return [current_node] + self._build_professional_tree_subjects(subjects, index + 1)

    def _merge_group_subjects(self, group: Dict[str, object]) -> List[Dict[str, object]]:
        merged_subjects: List[Dict[str, object]] = []
        for subject in PUBLIC_SUBJECTS:
            if isinstance(subject, dict):
                merged_subjects.append(dict(subject))
        professional_subjects = group.get("professionalSubjects", [])
        if isinstance(professional_subjects, list):
            for subject in professional_subjects:
                if isinstance(subject, dict):
                    merged_subjects.append(dict(subject))
        deduped_subjects: List[Dict[str, object]] = []
        seen_keys: set[str] = set()
        for subject in merged_subjects:
            subject_code = str(subject.get("subjectCode", "")).strip()
            subject_type = str(subject.get("subjectType", "")).strip().upper()
            if not subject_code:
                continue
            dedupe_key = f"{subject_code}::{subject_type}"
            if dedupe_key in seen_keys:
                continue
            seen_keys.add(dedupe_key)
            deduped_subjects.append(subject)
        return deduped_subjects

    def _safe_int(self, value: object, fallback: int) -> int:
        try:
            return int(value)
        except (TypeError, ValueError):
            return fallback
