from __future__ import annotations

import json
from enum import Enum
from typing import Any, Optional

from app.content_baseline import PUBLIC_SUBJECTS, get_joint_exam_group
from app.shared.codecs import dump_json, load_json_object as shared_load_json_object
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from pydantic.alias_generators import to_camel

try:
    from enum import StrEnum
except ImportError:
    class StrEnum(str, Enum):
        pass

APP_TITLE = "Question Bank Unified Delivery"
SUCCESS_CODE = "OK"
SUCCESS_MESSAGE = "success"

QUESTION_FIELDS = (
    "id",
    "knowledgeId",
    "userId",
    "type",
    "stem",
    "optionsJson",
    "answer",
    "status",
    "extJson",
    "createTime",
    "updateTime",
)

KNOWLEDGE_FIELDS = (
    "id",
    "parentId",
    "name",
    "sort",
    "status",
    "extJson",
    "createTime",
    "updateTime",
)

TASK_FIELDS = (
    "id",
    "userId",
    "type",
    "status",
    "progress",
    "extJson",
    "createTime",
    "updateTime",
)

class KnowledgeStatusEnum(StrEnum):
    ENABLED = "ENABLED"
    DISABLED = "DISABLED"


class TaskTypeEnum(StrEnum):
    AI_MARKING = "AI_MARKING"
    AI_TUTOR = "AI_TUTOR"
    QUESTION_BATCH_PARSE = "QUESTION_BATCH_PARSE"


class TaskStatusEnum(StrEnum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class QuestionTypeEnum(StrEnum):
    single_choice = "single_choice"
    multiple_choice = "multiple_choice"
    judge = "judge"
    subjective = "subjective"


class QuestionDifficultyEnum(StrEnum):
    easy = "easy"
    medium = "medium"
    hard = "hard"


class QuestionStatusEnum(StrEnum):
    DRAFT = "DRAFT"
    QA_IN_PROGRESS = "QA_IN_PROGRESS"
    REVIEW_PENDING = "REVIEW_PENDING"
    PUBLISHED = "PUBLISHED"
    REJECTED = "REJECTED"


class MessageCategoryEnum(StrEnum):
    TEACHER_QA = "TEACHER_QA"
    AI_TUTOR = "AI_TUTOR"
    AI_MARKING = "AI_MARKING"
    SYSTEM_NOTICE = "SYSTEM_NOTICE"
    REVIEW_NOTICE = "REVIEW_NOTICE"
    STUDY_REMINDER = "STUDY_REMINDER"
    WEEKLY_REPORT = "WEEKLY_REPORT"
    POINTS_NOTICE = "POINTS_NOTICE"


KNOWLEDGE_STATUSES = (
    KnowledgeStatusEnum.ENABLED.value,
    KnowledgeStatusEnum.DISABLED.value,
)
TASK_TYPES = (
    TaskTypeEnum.AI_MARKING.value,
    TaskTypeEnum.AI_TUTOR.value,
    TaskTypeEnum.QUESTION_BATCH_PARSE.value,
)
TASK_STATUSES = (
    TaskStatusEnum.QUEUED.value,
    TaskStatusEnum.RUNNING.value,
    TaskStatusEnum.COMPLETED.value,
    TaskStatusEnum.FAILED.value,
    TaskStatusEnum.CANCELLED.value,
)
QUESTION_TYPES = (
    QuestionTypeEnum.single_choice.value,
    QuestionTypeEnum.multiple_choice.value,
    QuestionTypeEnum.judge.value,
    QuestionTypeEnum.subjective.value,
)
QUESTION_DIFFICULTIES = (
    QuestionDifficultyEnum.easy.value,
    QuestionDifficultyEnum.medium.value,
    QuestionDifficultyEnum.hard.value,
)
QUESTION_STATUSES = (
    QuestionStatusEnum.DRAFT.value,
    QuestionStatusEnum.QA_IN_PROGRESS.value,
    QuestionStatusEnum.REVIEW_PENDING.value,
    QuestionStatusEnum.PUBLISHED.value,
    QuestionStatusEnum.REJECTED.value,
)

QUESTION_ERROR_CODES = {
    "NOT_FOUND": "QUESTION_NOT_FOUND",
    "FORBIDDEN": "QUESTION_FORBIDDEN",
    "VALIDATION_FAILED": "QUESTION_VALIDATION_FAILED",
    "INVALID_STATUS": "QUESTION_INVALID_STATUS",
    "DATABASE_ERROR": "QUESTION_DATABASE_ERROR",
}

ROLE_SUPER_ADMIN = "super_admin"
ROLE_TEACHER = "teacher"
ROLE_STUDENT = "student"

LEGACY_ROLE_QUESTION_TEACHER = "question_teacher"
LEGACY_ROLE_ACADEMIC_TEACHER = "academic_teacher"

ROLE_ALIAS_MAP = {
    LEGACY_ROLE_QUESTION_TEACHER: ROLE_TEACHER,
    LEGACY_ROLE_ACADEMIC_TEACHER: ROLE_TEACHER,
}

ALL_ROLES = (
    ROLE_SUPER_ADMIN,
    ROLE_TEACHER,
    ROLE_STUDENT,
)

ACCEPTED_ROLES = (
    *ALL_ROLES,
    LEGACY_ROLE_QUESTION_TEACHER,
    LEGACY_ROLE_ACADEMIC_TEACHER,
)

QUESTION_OPERATE_ROLES = (ROLE_TEACHER,)
PAPER_OPERATE_ROLES = (ROLE_TEACHER,)
ANALYTICS_OPERATE_ROLES = (ROLE_TEACHER,)
STUDENT_OPERATE_ROLES = (ROLE_STUDENT,)

MANAGED_PERMISSION_KEYS = (
    "question:manage",
    "paper:manage",
    "analytics:view",
    "student:manage",
    "settings:manage",
    "message:send",
)

MESSAGE_CATEGORIES = (
    MessageCategoryEnum.TEACHER_QA.value,
    MessageCategoryEnum.AI_TUTOR.value,
    MessageCategoryEnum.AI_MARKING.value,
    MessageCategoryEnum.SYSTEM_NOTICE.value,
    MessageCategoryEnum.REVIEW_NOTICE.value,
    MessageCategoryEnum.STUDY_REMINDER.value,
    MessageCategoryEnum.WEEKLY_REPORT.value,
    MessageCategoryEnum.POINTS_NOTICE.value,
)

REQUEST_MODEL_CONFIG = ConfigDict(
    extra="forbid",
    populate_by_name=False,
    alias_generator=to_camel,
    str_strip_whitespace=True,
)


def _load_json_object(payload: object) -> dict[str, object]:
    return shared_load_json_object(payload)


PUBLIC_SUBJECT_CODES = {str(item.get("subjectCode", "")).strip() for item in PUBLIC_SUBJECTS if isinstance(item, dict)}


def _resolve_subject_type_by_group(
    exam_category_code: str,
    joint_exam_group_code: str,
    subject_code: str,
    subject_type: str,
) -> str:
    normalized_exam_category_code = str(exam_category_code or "").strip()
    normalized_joint_exam_group_code = str(joint_exam_group_code or "").strip()
    normalized_subject_code = str(subject_code or "").strip()
    normalized_subject_type = str(subject_type or "").strip()

    joint_exam_group = get_joint_exam_group(normalized_joint_exam_group_code)
    if not joint_exam_group:
        raise ValueError("jointExamGroupCode 不存在。")
    if str(joint_exam_group.get("examCategoryCode", "")).strip() != normalized_exam_category_code:
        raise ValueError("jointExamGroupCode 与 examCategoryCode 不匹配。")

    if normalized_subject_code in PUBLIC_SUBJECT_CODES:
        return "PUBLIC"

    professional_subjects = joint_exam_group.get("professionalSubjects", [])
    if not isinstance(professional_subjects, list):
        professional_subjects = []
    matched_subjects = [
        item
        for item in professional_subjects
        if isinstance(item, dict) and str(item.get("subjectCode", "")).strip() == normalized_subject_code
    ]
    if not matched_subjects:
        raise ValueError("subjectCode 不属于当前 jointExamGroupCode。")

    if normalized_subject_type:
        if any(str(item.get("subjectType", "")).strip() == normalized_subject_type for item in matched_subjects):
            return normalized_subject_type
        raise ValueError("subjectType 与 subjectCode / jointExamGroupCode 不匹配。")
    return str(matched_subjects[0].get("subjectType", "")).strip()


def _normalize_paper_scope_request(
    exam_category_code: str,
    joint_exam_group_code: str,
    subject_code: str,
) -> tuple[str, str, str]:
    normalized_exam_category_code = str(exam_category_code or "").strip()
    normalized_joint_exam_group_code = str(joint_exam_group_code or "").strip()
    normalized_subject_code = str(subject_code or "").strip()
    has_any_scope = any(
        (
            normalized_exam_category_code,
            normalized_joint_exam_group_code,
            normalized_subject_code,
        )
    )
    if not has_any_scope:
        return "", "", ""

    joint_exam_group = get_joint_exam_group(normalized_joint_exam_group_code) if normalized_joint_exam_group_code else None
    if normalized_joint_exam_group_code and not joint_exam_group:
        raise ValueError("jointExamGroupCode 不存在。")
    if joint_exam_group and not normalized_exam_category_code:
        normalized_exam_category_code = str(joint_exam_group.get("examCategoryCode", "")).strip()
    if not normalized_exam_category_code or not normalized_joint_exam_group_code:
        raise ValueError("examCategoryCode、jointExamGroupCode 需同时提供，subjectCode 可选。")
    if joint_exam_group and str(joint_exam_group.get("examCategoryCode", "")).strip() != normalized_exam_category_code:
        raise ValueError("jointExamGroupCode 与 examCategoryCode 不匹配。")
    if normalized_subject_code:
        _resolve_subject_type_by_group(
            normalized_exam_category_code,
            normalized_joint_exam_group_code,
            normalized_subject_code,
            "",
        )
    return normalized_exam_category_code, normalized_joint_exam_group_code, normalized_subject_code


class QuestionOptionItem(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=False,
        alias_generator=to_camel,
        str_strip_whitespace=True,
    )

    key: str = Field(
        ...,
        min_length=1,
        max_length=8,
        description="选项标识，例如 A/B/C/D。",
    )
    content: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="选项内容，最长 500 字符。",
    )


class QuestionCreateRequest(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=False,
        alias_generator=to_camel,
        str_strip_whitespace=True,
    )

    id: Optional[str] = None
    policy_version: str = Field(
        default="HB_ZSB_2026",
        min_length=1,
        max_length=64,
        description="内容体系策略版本，默认 HB_ZSB_2026。",
    )
    user_id: Optional[str] = Field(
        default=None,
        description="题目归属教师用户 ID，不传时默认当前登录人。",
    )

    title: str = Field(..., min_length=2, max_length=200, description="题目标题，2-200 字符。")
    content: str = Field(
        ...,
        min_length=1,
        max_length=5000,
        description="题干内容，1-5000 字符。",
    )
    type: QuestionTypeEnum = Field(description="题型：单选、多选、判断、主观。")
    subject_code: str = Field(
        ...,
        min_length=1,
        max_length=64,
        description="学科编码，不能为空。",
    )
    exam_category_code: str = Field(
        ...,
        min_length=1,
        max_length=64,
        description="学科门类编码，不能为空。",
    )
    joint_exam_group_code: str = Field(
        ...,
        min_length=1,
        max_length=64,
        description="联考组编码，不能为空。",
    )
    knowledge_points: list[str] = Field(
        ...,
        min_length=1,
        max_length=20,
        description="关联知识点 ID 列表，至少 1 个。",
    )
    options: list[QuestionOptionItem] = Field(
        default_factory=list,
        description="客观题选项列表。",
    )
    answer: str = Field(..., min_length=1, max_length=2000, description="标准答案，1-2000 字符。")
    analysis: str = Field(default="", max_length=5000, description="题目解析，最长 5000 字符。")
    score: int = Field(default=5, ge=1, le=100, description="题目分值，范围 1-100。")
    subject_type: str = Field(
        default="",
        max_length=64,
        description="学科类型（公共课/专业课子类型）。",
    )
    module_code: str = Field(
        default="",
        max_length=64,
        description="模块编码（内容体系扩展字段）。",
    )
    source_type: str = Field(
        default="manual",
        max_length=32,
        description="题目来源类型。",
    )
    difficulty: QuestionDifficultyEnum = Field(default=QuestionDifficultyEnum.medium, description="题目难度。")
    status: QuestionStatusEnum = Field(default=QuestionStatusEnum.DRAFT, description="题目状态。")
    ext_json: dict[str, object] = Field(
        default_factory=dict,
        description="附加扩展字段，将与标准字段合并后写入 extJson。",
    )

    @field_validator("knowledge_points")
    @classmethod
    def validate_knowledge_points(cls, values: list[str]) -> list[str]:
        normalized = [str(item).strip() for item in values if str(item).strip()]
        if not normalized:
            raise ValueError("knowledge_points 至少包含 1 个知识点。")
        return normalized

    @field_validator("options")
    @classmethod
    def validate_options(cls, values: list[QuestionOptionItem], info) -> list[QuestionOptionItem]:
        question_type = info.data.get("type")
        objective_types = {
            QuestionTypeEnum.single_choice,
            QuestionTypeEnum.multiple_choice,
            QuestionTypeEnum.judge,
        }
        if question_type in objective_types and not values:
            raise ValueError("客观题必须包含 options。")
        return values

    @model_validator(mode="after")
    def validate_subject_scope(self) -> "QuestionCreateRequest":
        resolved_subject_type = _resolve_subject_type_by_group(
            self.exam_category_code,
            self.joint_exam_group_code,
            self.subject_code,
            self.subject_type,
        )
        self.subject_type = resolved_subject_type
        return self

    def to_service_payload(self) -> dict[str, object]:
        ext_payload = dict(self.ext_json)
        ext_payload["title"] = self.title
        ext_payload["analysis"] = self.analysis
        ext_payload["subjectCode"] = self.subject_code
        ext_payload["examCategoryCode"] = self.exam_category_code
        ext_payload["jointExamGroupCode"] = self.joint_exam_group_code
        ext_payload["subjectType"] = self.subject_type
        ext_payload["knowledgePointIds"] = self.knowledge_points
        ext_payload["sourceType"] = self.source_type
        ext_payload["difficulty"] = self.difficulty.value
        ext_payload["score"] = self.score
        ext_payload["policyVersionCode"] = self.policy_version
        if self.module_code:
            ext_payload["moduleCode"] = self.module_code

        payload: dict[str, object] = {
            "knowledgeId": self.knowledge_points[0],
            "type": self.type.value,
            "stem": self.content,
            "optionsJson": dump_json([item.model_dump() for item in self.options]),
            "answer": self.answer,
            "status": self.status.value,
            "extJson": dump_json(ext_payload),
        }
        if self.id:
            payload["id"] = self.id
        if self.user_id:
            payload["userId"] = self.user_id
        return payload


class QuestionUpdateRequest(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=False,
        alias_generator=to_camel,
        str_strip_whitespace=True,
    )

    id: Optional[str] = None
    policy_version: str = Field(
        default="HB_ZSB_2026",
        min_length=1,
        max_length=64,
        description="内容体系策略版本，默认 HB_ZSB_2026。",
    )
    user_id: Optional[str] = Field(
        default=None,
        description="题目归属教师用户 ID，不传时继承原值。",
    )
    create_time: Optional[str] = Field(default=None)
    update_time: Optional[str] = Field(default=None)

    title: Optional[str] = Field(default=None, min_length=2, max_length=200, description="题目标题，2-200 字符。")
    content: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=5000,
        description="题干内容，1-5000 字符。",
    )
    type: Optional[QuestionTypeEnum] = Field(default=None, description="题型。")
    subject_code: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=64,
        description="学科编码。",
    )
    exam_category_code: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=64,
        description="学科门类编码。",
    )
    knowledge_points: Optional[list[str]] = Field(
        default=None,
        max_length=20,
        description="关联知识点 ID 列表。",
    )
    options: Optional[list[QuestionOptionItem]] = Field(
        default=None,
        description="客观题选项列表。",
    )
    answer: Optional[str] = Field(default=None, min_length=1, max_length=2000, description="标准答案。")
    analysis: Optional[str] = Field(default=None, max_length=5000, description="题目解析。")
    score: Optional[int] = Field(default=None, ge=1, le=100, description="题目分值，范围 1-100。")
    subject_type: Optional[str] = Field(
        default=None,
        max_length=64,
        description="学科类型（公共课/专业课子类型）。",
    )
    joint_exam_group_code: Optional[str] = Field(
        default=None,
        max_length=64,
        description="联考组编码（专业课场景）。",
    )
    module_code: Optional[str] = Field(
        default=None,
        max_length=64,
        description="模块编码（内容体系扩展字段）。",
    )
    source_type: Optional[str] = Field(
        default=None,
        max_length=32,
        description="题目来源类型。",
    )
    difficulty: Optional[QuestionDifficultyEnum] = Field(default=None, description="题目难度。")
    status: Optional[QuestionStatusEnum] = Field(default=None, description="题目状态。")
    ext_json: Optional[dict[str, object]] = Field(
        default=None,
        description="附加扩展字段，将与原 extJson 合并。",
    )

    @field_validator("knowledge_points")
    @classmethod
    def validate_knowledge_points(cls, values: Optional[list[str]]) -> Optional[list[str]]:
        if values is None:
            return None
        return [str(item).strip() for item in values if str(item).strip()]

    def to_service_payload(self, existing_question: Optional[dict[str, object]] = None) -> dict[str, object]:
        payload: dict[str, object] = {}
        ext_patch: dict[str, object] = dict(self.ext_json or {})

        if self.knowledge_points is not None:
            payload["knowledgeId"] = self.knowledge_points[0] if self.knowledge_points else ""
            ext_patch["knowledgePointIds"] = self.knowledge_points
        if self.type is not None:
            payload["type"] = self.type.value
        if self.content is not None:
            payload["stem"] = self.content
        if self.answer is not None:
            payload["answer"] = self.answer
        if self.status is not None:
            payload["status"] = self.status.value
        if self.options is not None:
            payload["optionsJson"] = dump_json([item.model_dump() for item in self.options])
        if self.user_id:
            payload["userId"] = self.user_id
        if self.title is not None:
            ext_patch["title"] = self.title
        if self.subject_code is not None:
            ext_patch["subjectCode"] = self.subject_code
        if self.exam_category_code is not None:
            ext_patch["examCategoryCode"] = self.exam_category_code
        if self.subject_type is not None:
            ext_patch["subjectType"] = self.subject_type
        if self.joint_exam_group_code is not None:
            ext_patch["jointExamGroupCode"] = self.joint_exam_group_code
        if self.analysis is not None:
            ext_patch["analysis"] = self.analysis
        if self.module_code is not None:
            ext_patch["moduleCode"] = self.module_code
        if self.source_type is not None:
            ext_patch["sourceType"] = self.source_type
        if self.difficulty is not None:
            ext_patch["difficulty"] = self.difficulty.value
        if self.score is not None:
            ext_patch["score"] = self.score
        ext_patch["policyVersionCode"] = self.policy_version

        if ext_patch:
            existing_ext = _load_json_object(existing_question.get("extJson", "{}") if existing_question else "{}")
            existing_ext.update(ext_patch)
            payload["extJson"] = dump_json(existing_ext)
        return payload


class BatchQuestionCreateRequest(BaseModel):
    model_config = REQUEST_MODEL_CONFIG

    items: list[QuestionCreateRequest] = Field(min_length=1, max_length=100)
    source_task_id: Optional[str] = Field(
        default=None,
        description="可选的来源解析任务 ID，用于回写批量入库结果。",
    )


class BaseResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=False, alias_generator=to_camel)

    code: str
    message: str
    data: Any = None


class SubjectKindEnum(StrEnum):
    PUBLIC = "PUBLIC"
    PROFESSIONAL = "PROFESSIONAL"


class ProfessionalTreeSubject(BaseModel):
    model_config = REQUEST_MODEL_CONFIG

    code: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=128)
    subject_type: SubjectKindEnum
    subject_slot: str = Field(min_length=1, max_length=32)
    score: int = Field(ge=0, le=500)


class ProfessionalTreeJointExamGroup(BaseModel):
    model_config = REQUEST_MODEL_CONFIG

    code: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=128)
    major_list_text: str = ""
    children: list[ProfessionalTreeSubject] = Field(default_factory=list)


class ProfessionalTreeExamCategory(BaseModel):
    model_config = REQUEST_MODEL_CONFIG

    code: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=128)
    sort_no: int = Field(ge=1)
    enabled: bool = True
    children: list[ProfessionalTreeJointExamGroup] = Field(default_factory=list)


class ProfessionalTreeResponse(BaseResponse):
    model_config = REQUEST_MODEL_CONFIG

    data: list[ProfessionalTreeExamCategory]


class QuestionTransitionRequest(BaseModel):
    model_config = REQUEST_MODEL_CONFIG

    policy_version: str = Field(
        default="HB_ZSB_2026",
        min_length=1,
        max_length=64,
    )
    reason: str = ""


class QuestionDeleteBatchRequest(BaseModel):
    model_config = REQUEST_MODEL_CONFIG

    policy_version: str = Field(
        default="HB_ZSB_2026",
        min_length=1,
        max_length=64,
    )
    question_ids: list[str] = Field(min_length=1)


class QuestionStatusBatchTransitionRequest(BaseModel):
    model_config = REQUEST_MODEL_CONFIG

    policy_version: str = Field(
        default="HB_ZSB_2026",
        min_length=1,
        max_length=64,
    )
    question_ids: list[str] = Field(min_length=1)
    target_status: str = Field(min_length=1)
    reason: str = ""


class AuthSmsCodeRequest(BaseModel):
    model_config = REQUEST_MODEL_CONFIG

    phone: str = Field(min_length=11, max_length=11)
    purpose: str = Field(min_length=1)


class AuthRegisterRequest(BaseModel):
    model_config = REQUEST_MODEL_CONFIG

    phone: str = Field(min_length=11, max_length=11)
    sms_code: str = Field(min_length=4, max_length=8)
    password: str = Field(min_length=6, max_length=18)
    role: str = Field(min_length=1)
    name: str = Field(min_length=1)
    exam_category_code: str = ""
    joint_exam_group_code: str = ""
    vocational_major: str = ""
    prep_stage: str = ""
    employee_no: str = ""


class AuthLoginPasswordRequest(BaseModel):
    model_config = REQUEST_MODEL_CONFIG

    phone: str = Field(min_length=11, max_length=11)
    password: str = Field(min_length=1, max_length=64)


class AuthLoginSmsRequest(BaseModel):
    model_config = REQUEST_MODEL_CONFIG

    phone: str = Field(min_length=11, max_length=11)
    sms_code: str = Field(min_length=4, max_length=8)


class AuthPasswordResetRequest(BaseModel):
    model_config = REQUEST_MODEL_CONFIG

    phone: str = Field(min_length=11, max_length=11)
    sms_code: str = Field(min_length=4, max_length=8)
    new_password: str = Field(min_length=6, max_length=18)


class KnowledgeWriteRequest(BaseModel):
    model_config = REQUEST_MODEL_CONFIG

    id: Optional[str] = None
    parent_id: Optional[str] = None
    policy_version: str = Field(
        default="HB_ZSB_2026",
    )
    exam_category_code: str = Field(
        default="",
    )
    joint_exam_group_code: str = Field(
        default="",
    )
    subject_code: str = Field(
        default="",
    )
    name: str = Field(min_length=1)
    sort: int = Field(ge=0)
    status: str = Field(min_length=1)
    ext_json: dict[str, object] = {}
    create_time: Optional[str] = None
    update_time: Optional[str] = None

    @field_validator("ext_json", mode="before")
    @classmethod
    def normalize_ext_json(cls, value: object) -> dict[str, object]:
        if isinstance(value, dict):
            return dict(value)
        if value is None:
            return {}
        if isinstance(value, str):
            text = value.strip()
            if not text:
                return {}
            try:
                loaded = json.loads(text)
            except (TypeError, ValueError, json.JSONDecodeError) as exc:
                raise ValueError("extJson 必须是 JSON 对象。") from exc
            if isinstance(loaded, dict):
                return loaded
            raise ValueError("extJson 必须是 JSON 对象。")
        raise ValueError("extJson 必须是 JSON 对象。")


class KnowledgePrerequisiteUpdateRequest(BaseModel):
    model_config = REQUEST_MODEL_CONFIG

    source_id: str = Field(min_length=1)


class KnowledgeLayoutNodeRequest(BaseModel):
    model_config = REQUEST_MODEL_CONFIG

    id: str = Field(min_length=1)
    x: float
    y: float


class KnowledgeLayoutSaveRequest(BaseModel):
    model_config = REQUEST_MODEL_CONFIG

    nodes: list[KnowledgeLayoutNodeRequest] = Field(default_factory=list, min_length=1, max_length=500)


class KnowledgeNode(BaseModel):
    model_config = REQUEST_MODEL_CONFIG

    id: str = Field(min_length=1)
    label: str = Field(min_length=1)
    full_label: str = Field(default="", max_length=256)
    short_label: str = Field(default="", max_length=256)
    parent_id: Optional[str] = None
    level: int = Field(default=0, ge=0, le=10)
    sort: int = Field(default=0, ge=0)
    create_time: str = ""
    module_code: str = Field(default="", max_length=128)
    mastery: float = Field(default=0.0, ge=0.0, le=1.0)
    wrong_count: int = Field(default=0, ge=0)
    size: int = Field(default=8, ge=1, le=200)
    question_count: int = Field(default=0, ge=0)
    x: Optional[float] = None
    y: Optional[float] = None


class KnowledgeLinkTypeEnum(StrEnum):
    parent = "parent"
    prerequisite = "prerequisite"


class KnowledgeLink(BaseModel):
    model_config = REQUEST_MODEL_CONFIG

    source: str = Field(min_length=1)
    target: str = Field(min_length=1)
    type: KnowledgeLinkTypeEnum


class KnowledgeGraphResponse(BaseModel):
    model_config = REQUEST_MODEL_CONFIG

    nodes: list[KnowledgeNode] = Field(default_factory=list)
    links: list[KnowledgeLink] = Field(default_factory=list)


class KnowledgeGraphEnvelopeResponse(BaseResponse):
    model_config = REQUEST_MODEL_CONFIG

    data: KnowledgeGraphResponse = Field(default_factory=KnowledgeGraphResponse)


class StudentSessionSubmitRequest(BaseModel):
    model_config = REQUEST_MODEL_CONFIG

    answered_count: int = Field(ge=0, le=5000)
    elapsed_sec: int = Field(ge=0, le=43200)


class StudentProfileUpdateRequest(BaseModel):
    model_config = REQUEST_MODEL_CONFIG

    exam_category_code: str = Field(min_length=1)
    joint_exam_group_code: str = Field(min_length=1)


class StudentPracticeSubmitRequest(BaseModel):
    model_config = REQUEST_MODEL_CONFIG

    answer: str = Field(min_length=1)
    elapsed_sec: int = Field(ge=0, le=3600)
    assignment_id: str = ""
    source_type: str = ""
    attempt_key: str = Field(
        default="",
    )


class AdaptivePracticeRequest(BaseModel):
    model_config = REQUEST_MODEL_CONFIG

    count: int = Field(default=10, ge=1, le=100, description="推题数量")
    knowledge_id: str = Field(default="", description="指定知识点强化目标（可选）。")


class AdaptivePracticeResult(BaseModel):
    model_config = REQUEST_MODEL_CONFIG

    question_ids: list[str] = Field(default_factory=list, description="生成的临时练习题目 ID 列表。")


class AdaptivePracticeResponse(BaseResponse):
    model_config = REQUEST_MODEL_CONFIG

    data: AdaptivePracticeResult = Field(default_factory=AdaptivePracticeResult)


class StudentPersonalBankToggleRequest(BaseModel):
    model_config = REQUEST_MODEL_CONFIG

    is_collected: bool = True


class StudentAiMarkingSubmitRequest(BaseModel):
    model_config = REQUEST_MODEL_CONFIG

    answer: str = Field(min_length=1)
    answer_image_url: str = ""
    assignment_id: str = ""


class StudentAiTutorAskRequest(BaseModel):
    model_config = REQUEST_MODEL_CONFIG

    prompt: str = Field(min_length=1)
    prompt_image_url: str = ""


class StudentSubscriptionRedeemRequest(BaseModel):
    model_config = REQUEST_MODEL_CONFIG

    code: str = Field(min_length=4, max_length=64)
    request_id: str = Field(default="", max_length=128)


class StudentSubscriptionMockOrderCreateRequest(BaseModel):
    model_config = REQUEST_MODEL_CONFIG

    plan_code: str = Field(default="AI_SCORE_BOOST_30D", min_length=1, max_length=64)
    source_type: str = Field(default="CHECKOUT", max_length=64)
    session_id: str = Field(default="", max_length=128)


class StudentSubscriptionMockOrderConfirmRequest(BaseModel):
    model_config = REQUEST_MODEL_CONFIG

    transaction_no: str = Field(min_length=1, max_length=128)
    request_id: str = Field(default="", max_length=128)
    paid_at: str = Field(default="", max_length=64)


class StudentDiagnosisQuickStartRequest(BaseModel):
    model_config = REQUEST_MODEL_CONFIG

    question_count: int = Field(default=5, ge=3, le=5)
    subject_code: str = Field(default="", max_length=64)
    source_type: str = Field(default="ONBOARDING", max_length=64)


class StudentDiagnosisQuickSubmitAnswerItem(BaseModel):
    model_config = REQUEST_MODEL_CONFIG

    question_id: str = Field(min_length=1, max_length=128)
    answer: str = Field(min_length=1, max_length=200)
    elapsed_sec: int = Field(default=0, ge=0, le=3600)


class StudentDiagnosisQuickSubmitRequest(BaseModel):
    model_config = REQUEST_MODEL_CONFIG

    answers: list[StudentDiagnosisQuickSubmitAnswerItem] = Field(min_length=1, max_length=20)
    source_type: str = Field(default="ONBOARDING", max_length=64)


class LearningMethodPracticeStartRequest(BaseModel):
    model_config = REQUEST_MODEL_CONFIG

    practice_strategy: str = Field(
        default="",
        max_length=64,
    )
    source_type: str = Field(
        default="",
        max_length=64,
    )
    session_id: str = Field(
        default="",
        max_length=64,
    )


class LearningMethodPracticeCompleteRequest(BaseModel):
    model_config = REQUEST_MODEL_CONFIG

    session_id: str = Field(
        min_length=1,
        max_length=64,
    )
    accuracy: float = Field(ge=0.0, le=100.0)
    review_summary: str = Field(
        default="",
        max_length=500,
    )
    duration_sec: int = Field(
        default=0,
        ge=0,
        le=7200,
    )


class LearningMethodAdminSaveRequest(BaseModel):
    model_config = REQUEST_MODEL_CONFIG

    method_code: str = Field(
        min_length=1,
        max_length=64,
    )
    method_name: str = Field(
        min_length=1,
        max_length=128,
    )
    one_line_intro: str = Field(
        default="",
        max_length=200,
    )
    use_when: list[str] = Field(
        default_factory=list,
    )
    steps: list[str] = Field(default_factory=list)
    common_mistakes: list[str] = Field(
        default_factory=list,
    )
    question_bank_actions: list[str] = Field(
        default_factory=list,
    )
    starter_task: str = Field(
        default="",
        max_length=300,
    )
    difficulty_level: str = Field(
        default="L1",
        min_length=1,
        max_length=16,
    )
    estimated_minutes: int = Field(
        default=15,
        ge=1,
        le=180,
    )
    sort: int = Field(default=0, ge=0)
    status: str = Field(default="ACTIVE", min_length=1, max_length=16)
    ext_json: dict[str, object] = Field(
        default_factory=dict,
    )


class LearningMethodAdminUpdateRequest(BaseModel):
    model_config = REQUEST_MODEL_CONFIG

    method_name: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=128,
    )
    one_line_intro: Optional[str] = Field(
        default=None,
        max_length=200,
    )
    use_when: Optional[list[str]] = Field(
        default=None,
    )
    steps: Optional[list[str]] = None
    common_mistakes: Optional[list[str]] = Field(
        default=None,
    )
    question_bank_actions: Optional[list[str]] = Field(
        default=None,
    )
    starter_task: Optional[str] = Field(
        default=None,
        max_length=300,
    )
    difficulty_level: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=16,
    )
    estimated_minutes: Optional[int] = Field(
        default=None,
        ge=1,
        le=180,
    )
    sort: Optional[int] = Field(default=None, ge=0)
    status: Optional[str] = Field(default=None, min_length=1, max_length=16)
    ext_json: Optional[dict[str, object]] = Field(
        default=None,
    )


class LearningMethodAdminSortRequest(BaseModel):
    model_config = REQUEST_MODEL_CONFIG

    method_codes: list[str] = Field(
        min_length=1,
    )


class StudentPaperAnswerRequest(BaseModel):
    model_config = REQUEST_MODEL_CONFIG

    question_id: str = Field(min_length=1)
    answer: str = Field(min_length=1)
    elapsed_sec: int = Field(ge=0, le=3600)
    marked: bool = False


class StudentPaperSubmitRequest(BaseModel):
    model_config = REQUEST_MODEL_CONFIG

    answers: list[StudentPaperAnswerRequest] = Field(min_length=1)
    total_elapsed_sec: int = Field(ge=0, le=14400)


class AdminSyllabusVersionCreateRequest(BaseModel):
    model_config = REQUEST_MODEL_CONFIG

    version_name: str = Field(min_length=1, max_length=80)
    copy_from_version_id: str = ""


class AdminSyllabusWeightItemRequest(BaseModel):
    model_config = REQUEST_MODEL_CONFIG

    knowledge_id: str = Field(min_length=1)
    target_weight: float = Field(ge=0.0, le=1.0)


class AdminSyllabusWeightsSaveRequest(BaseModel):
    model_config = REQUEST_MODEL_CONFIG

    knowledge_weights: list[AdminSyllabusWeightItemRequest] = Field(min_length=1)


class AdminSystemSettingsSaveRequest(BaseModel):
    model_config = REQUEST_MODEL_CONFIG

    platform_name: str = Field(min_length=1)
    default_exam_minutes: int = Field(ge=30, le=240)
    daily_check_in_points: int = Field(ge=0, le=200)
    practice_reward_threshold: int = Field(ge=1, le=200)
    practice_reward_points: int = Field(ge=0, le=200)
    paper_reward_points: int = Field(ge=0, le=200)
    wrong_book_reward_threshold: int = Field(ge=1, le=200)
    wrong_book_reward_points: int = Field(ge=0, le=200)
    ai_daily_limit: int = Field(ge=1, le=200)
    mock_exam_rule_profiles: dict[str, object] = Field(default_factory=dict)


class AdminManagedUserSaveRequest(BaseModel):
    model_config = REQUEST_MODEL_CONFIG

    user_id: str = Field(min_length=1)
    role: str = Field(min_length=1)
    name: str = Field(min_length=1)
    mobile: str = Field(min_length=11, max_length=11)
    enabled: bool = True
    permissions: list[str] = Field(default_factory=list)
    exam_category_code: str = ""
    joint_exam_group_code: str = ""
    vocational_major: str = ""
    prep_stage: str = ""


class AdminStudentsImportRequest(BaseModel):
    model_config = REQUEST_MODEL_CONFIG

    csv_text: str = Field(min_length=1)


class AdminRedeemCodeBatchCreateRequest(BaseModel):
    model_config = REQUEST_MODEL_CONFIG

    batch_name: str = Field(min_length=1, max_length=80)
    total_count: int = Field(ge=1, le=5000)
    plan_code: str = Field(default="AI_SCORE_BOOST_30D", min_length=1, max_length=64)
    channel_code: str = Field(default="MANUAL", max_length=64)
    expires_at: str = Field(default="", max_length=64)
    code_prefix: str = Field(default="RC", min_length=1, max_length=16)


class MessagesReadBatchRequest(BaseModel):
    model_config = REQUEST_MODEL_CONFIG

    message_ids: list[str] = Field(min_length=1)


class MessagesSettingsSaveRequest(BaseModel):
    model_config = REQUEST_MODEL_CONFIG

    allow_ai_tutor: bool = True
    allow_system_notice: bool = True
    allow_review_notice: bool = True
    allow_study_reminder: bool = True
    allow_weekly_report: bool = True
    allow_points_notice: bool = True


class MessagesSendRequest(BaseModel):
    model_config = REQUEST_MODEL_CONFIG

    target_mode: str = "userIds"
    user_ids: list[str] = Field(default_factory=list)
    exam_category_code: str = ""
    joint_exam_group_code: str = ""
    subject_code: str = ""
    send_at: str = ""
    category: str = Field(min_length=1)
    title: str = Field(min_length=1)
    content: str = Field(min_length=1)


class PaperAutoRuleRequest(BaseModel):
    model_config = REQUEST_MODEL_CONFIG

    type: str = Field(min_length=1)
    count: int = Field(ge=1)
    question_score: int = Field(ge=1)


class ManualPaperCreateRequest(BaseModel):
    model_config = REQUEST_MODEL_CONFIG

    paper_id: Optional[str] = None
    policy_version: str = Field(
        default="HB_ZSB_2026",
        min_length=1,
        max_length=64,
    )
    paper_name: str = Field(min_length=1)
    subject_id: str = ""
    exam_category_code: str = ""
    joint_exam_group_code: str = ""
    subject_code: str = ""
    paper_type: str = Field(min_length=1)
    paper_status: str = Field(min_length=1)
    duration_minutes: int = Field(ge=1, le=240)
    total_score: int = Field(ge=1)
    visible_to_students: bool = True
    publish_class_ids: list[str] = Field(
        default_factory=list,
    )
    question_ids: list[str] = Field(min_length=1)
    question_scores: dict[str, int] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_professional_scope(self) -> "ManualPaperCreateRequest":
        self.subject_id = str(self.subject_id or "").strip()
        self.subject_code = str(self.subject_code or "").strip()
        if not self.subject_id and self.subject_code:
            self.subject_id = self.subject_code
        normalized_exam_category_code, normalized_joint_exam_group_code, normalized_subject_code = _normalize_paper_scope_request(
            self.exam_category_code,
            self.joint_exam_group_code,
            self.subject_code,
        )
        self.exam_category_code = normalized_exam_category_code
        self.joint_exam_group_code = normalized_joint_exam_group_code
        self.subject_code = normalized_subject_code
        return self


# Backward compatibility alias for legacy imports/usages.
PaperManualSaveRequest = ManualPaperCreateRequest


class PaperAutoSaveRequest(BaseModel):
    model_config = REQUEST_MODEL_CONFIG

    paper_id: Optional[str] = None
    policy_version: str = Field(
        default="HB_ZSB_2026",
        min_length=1,
        max_length=64,
    )
    paper_name: str = Field(min_length=1)
    paper_type: str = Field(min_length=1)
    paper_status: str = Field(min_length=1)
    duration_minutes: int = Field(ge=1, le=240)
    total_score: int = Field(ge=1)
    visible_to_students: bool = True
    subject_id: str = ""
    exam_category_code: str = ""
    joint_exam_group_code: str = ""
    subject_code: str = ""
    chapter: str = ""
    difficulty: str = ""
    type_rules: list[PaperAutoRuleRequest] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_professional_scope(self) -> "PaperAutoSaveRequest":
        self.subject_id = str(self.subject_id or "").strip()
        self.subject_code = str(self.subject_code or "").strip()
        if not self.subject_id and self.subject_code:
            self.subject_id = self.subject_code
        normalized_exam_category_code, normalized_joint_exam_group_code, normalized_subject_code = _normalize_paper_scope_request(
            self.exam_category_code,
            self.joint_exam_group_code,
            self.subject_code,
        )
        self.exam_category_code = normalized_exam_category_code
        self.joint_exam_group_code = normalized_joint_exam_group_code
        self.subject_code = normalized_subject_code
        return self


class PaperTemplateSaveRequest(BaseModel):
    model_config = REQUEST_MODEL_CONFIG

    template_id: Optional[str] = None
    policy_version: str = Field(
        default="HB_ZSB_2026",
        min_length=1,
        max_length=64,
    )
    template_name: str = Field(min_length=1)
    paper_type: str = Field(min_length=1)
    subject_id: str = ""
    chapter: str = ""
    difficulty: str = ""
    total_score: int = Field(ge=1)
    duration_minutes: int = Field(ge=1, le=240)
    exam_category_code: str = ""
    joint_exam_group_code: str = ""
    subject_code: str = ""
    type_rules: list[PaperAutoRuleRequest] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_professional_scope(self) -> "PaperTemplateSaveRequest":
        self.subject_id = str(self.subject_id or "").strip()
        self.subject_code = str(self.subject_code or "").strip()
        if not self.subject_id and self.subject_code:
            self.subject_id = self.subject_code
        normalized_exam_category_code, normalized_joint_exam_group_code, normalized_subject_code = _normalize_paper_scope_request(
            self.exam_category_code,
            self.joint_exam_group_code,
            self.subject_code,
        )
        self.exam_category_code = normalized_exam_category_code
        self.joint_exam_group_code = normalized_joint_exam_group_code
        self.subject_code = normalized_subject_code
        return self


class PaperAiGenerateRequest(BaseModel):
    model_config = REQUEST_MODEL_CONFIG

    policy_version: str = Field(
        default="HB_ZSB_2026",
        min_length=1,
        max_length=64,
    )
    subject_id: str = ""
    exam_category_code: str = ""
    joint_exam_group_code: str = ""
    subject_code: str = ""
    difficulty: int = Field(
        ge=1,
        le=5,
    )
    class_ids: list[str] = Field(default_factory=list)
    total_count: int = Field(default=20, ge=10, le=50)
    knowledge_scope: list[str] = Field(default_factory=list)

    @field_validator("class_ids", "knowledge_scope")
    @classmethod
    def validate_scope_ids(cls, value: list[str]) -> list[str]:
        normalized: list[str] = []
        seen: set[str] = set()
        for item in value or []:
            normalized_id = str(item or "").strip()
            if not normalized_id or normalized_id in seen:
                continue
            seen.add(normalized_id)
            normalized.append(normalized_id)
        return normalized

    @model_validator(mode="after")
    def validate_professional_scope(self) -> "PaperAiGenerateRequest":
        self.subject_id = str(self.subject_id or "").strip()
        normalized_exam_category_code, normalized_joint_exam_group_code, normalized_subject_code = _normalize_paper_scope_request(
            self.exam_category_code,
            self.joint_exam_group_code,
            self.subject_code,
        )
        self.exam_category_code = normalized_exam_category_code
        self.joint_exam_group_code = normalized_joint_exam_group_code
        self.subject_code = normalized_subject_code
        if not self.subject_id and not self.joint_exam_group_code:
            raise ValueError("subject_id 或 joint_exam_group_code 至少提供一个。")
        return self


class ExamTaskCreateRequest(BaseModel):
    model_config = REQUEST_MODEL_CONFIG

    task_name: str = Field(min_length=1, max_length=100)
    task_type: str = Field(min_length=1, max_length=32)
    subject_id: str = ""
    exam_category_code: str = ""
    joint_exam_group_code: str = ""
    subject_code: str = ""
    source_type: str = Field(default="", max_length=32)
    source_id: str = Field(default="", max_length=128)
    source_label: str = Field(default="", max_length=100)
    description: str = Field(default="", max_length=1000)
    allow_redo: bool = False
    target_question_count: int = Field(default=1, ge=1, le=200)
    due_at: str = Field(default="", max_length=64)
    status: str = Field(default="PUBLISHED", min_length=1, max_length=32)
    class_ids: list[str] = Field(default_factory=list)
    student_ids: list[str] = Field(default_factory=list)

    @field_validator("class_ids", "student_ids")
    @classmethod
    def validate_target_ids(cls, value: list[str]) -> list[str]:
        normalized: list[str] = []
        seen: set[str] = set()
        for item in value or []:
            normalized_id = str(item or "").strip()
            if not normalized_id or normalized_id in seen:
                continue
            seen.add(normalized_id)
            normalized.append(normalized_id)
        return normalized

    @model_validator(mode="after")
    def validate_professional_scope(self) -> "ExamTaskCreateRequest":
        self.subject_id = str(self.subject_id or "").strip()
        self.subject_code = str(self.subject_code or "").strip()
        if not self.subject_id and self.subject_code:
            self.subject_id = self.subject_code
        normalized_exam_category_code, normalized_joint_exam_group_code, normalized_subject_code = _normalize_paper_scope_request(
            self.exam_category_code,
            self.joint_exam_group_code,
            self.subject_code,
        )
        self.exam_category_code = normalized_exam_category_code
        self.joint_exam_group_code = normalized_joint_exam_group_code
        self.subject_code = normalized_subject_code
        return self


class StudentMockExamStartRequest(BaseModel):
    model_config = REQUEST_MODEL_CONFIG

    subject_id: str = ""
    exam_category_code: str = ""
    joint_exam_group_code: str = ""
    subject_code: str = ""

    @model_validator(mode="after")
    def validate_professional_scope(self) -> "StudentMockExamStartRequest":
        self.subject_id = str(self.subject_id or "").strip()
        self.subject_code = str(self.subject_code or "").strip()
        if not self.subject_id and self.subject_code:
            self.subject_id = self.subject_code
        normalized_exam_category_code, normalized_joint_exam_group_code, normalized_subject_code = _normalize_paper_scope_request(
            self.exam_category_code,
            self.joint_exam_group_code,
            self.subject_code,
        )
        self.exam_category_code = normalized_exam_category_code
        self.joint_exam_group_code = normalized_joint_exam_group_code
        self.subject_code = normalized_subject_code
        if not self.subject_id and not self.subject_code:
            raise ValueError("subject_id 或 subject_code 至少提供一个。")
        return self


def normalize_role(role: str) -> str:
    normalized = str(role or "").strip()
    if not normalized:
        return normalized
    return ROLE_ALIAS_MAP.get(normalized, normalized)


def is_teacher_role(role: str) -> bool:
    return normalize_role(role) == ROLE_TEACHER


def success(data: object) -> dict[str, object]:
    return BaseResponse(code=SUCCESS_CODE, message=SUCCESS_MESSAGE, data=data).model_dump()


def pagination(items: list[dict[str, object]], page: int, size: int, total: int) -> dict[str, object]:
    return {
        "items": items,
        "page": page,
        "size": size,
        "total": total,
    }
