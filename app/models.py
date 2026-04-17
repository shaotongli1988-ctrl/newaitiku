from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional, TypeVar

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, field_validator, model_validator

from app.content_baseline import POLICY_VERSION_CODE, PUBLIC_SUBJECTS, get_joint_exam_group
from app.contracts import (
    ALL_ROLES,
    KNOWLEDGE_STATUSES,
    MANAGED_PERMISSION_KEYS,
    MANAGED_TEACHER_POST_TAGS,
    MESSAGE_CATEGORIES,
    QUESTION_DIFFICULTIES,
    QUESTION_STATUSES,
    QUESTION_TYPES,
)
from app.exceptions import validation_failed


class QuestionWriteModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: Optional[str] = None
    knowledgeId: str = Field(min_length=1)
    userId: str = Field(min_length=1)
    type: str = Field(min_length=1)
    stem: str = Field(min_length=1)
    optionsJson: str = Field(min_length=2)
    answer: str = Field(min_length=1)
    status: str = Field(min_length=1)
    extJson: str = Field(min_length=2)
    createTime: Optional[str] = None
    updateTime: Optional[str] = None

    @field_validator("knowledgeId", "userId", "stem", "answer")
    @classmethod
    def trim_required(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("字段不能为空。")
        return value

    @field_validator("type")
    @classmethod
    def validate_type(cls, value: str) -> str:
        value = value.strip()
        if value not in QUESTION_TYPES:
            raise ValueError(f"type 仅支持 {', '.join(QUESTION_TYPES)}。")
        return value

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str) -> str:
        value = value.strip()
        if value not in QUESTION_STATUSES:
            raise ValueError(f"status 仅支持 {', '.join(QUESTION_STATUSES)}。")
        return value

    @field_validator("optionsJson")
    @classmethod
    def validate_options(cls, value: str, info) -> str:
        value = value.strip()
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError as exc:
            raise ValueError("optionsJson 必须是合法 JSON。") from exc
        question_type = info.data.get("type")
        if question_type in {"single_choice", "multiple_choice", "judge"}:
            if not isinstance(parsed, list) or not parsed:
                raise ValueError("客观题的 optionsJson 必须是非空数组。")
        if question_type == "subjective" and not isinstance(parsed, list):
            raise ValueError("主观题的 optionsJson 也必须保持 JSON 数组格式。")
        return value

    @field_validator("extJson")
    @classmethod
    def validate_ext_json(cls, value: str) -> str:
        value = value.strip()
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError as exc:
            raise ValueError("extJson 必须是合法 JSON。") from exc
        if not isinstance(parsed, dict):
            raise ValueError("extJson 必须是 JSON 对象。")
        difficulty = str(parsed.get("difficulty", "")).strip()
        if difficulty and difficulty not in QUESTION_DIFFICULTIES:
            raise ValueError(f"extJson.difficulty 仅支持 {', '.join(QUESTION_DIFFICULTIES)}。")
        knowledge_tags = parsed.get("knowledgeTags")
        if knowledge_tags is not None:
            if not isinstance(knowledge_tags, list) or not (1 <= len(knowledge_tags) <= 3):
                raise ValueError("extJson.knowledgeTags 必须是 1-3 个知识点组成的数组。")
        analysis = str(parsed.get("analysis", "")).strip()
        if "analysis" in parsed and not analysis:
            raise ValueError("extJson.analysis 不能为空。")
        return value


class StatusTransitionModel(BaseModel):
    target_status: str


class StatusTransitionPayloadModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    policyVersion: str = Field(
        default=POLICY_VERSION_CODE,
        validation_alias=AliasChoices("policyVersion", "policy_version", "policyVersionCode"),
    )
    reason: str = ""

    @field_validator("policyVersion")
    @classmethod
    def validate_policy_version(cls, value: str) -> str:
        normalized = str(value or "").strip()
        if not normalized:
            raise ValueError("policyVersion 不能为空。")
        return normalized


class KnowledgeWriteModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: Optional[str] = None
    parentId: Optional[str] = None
    policyVersionCode: str = Field(
        default=POLICY_VERSION_CODE,
        validation_alias=AliasChoices("policyVersionCode", "policyVersion", "policy_version"),
    )
    examCategoryCode: str = Field(
        default="",
        validation_alias=AliasChoices("examCategoryCode", "exam_category_code"),
    )
    jointExamGroupCode: str = Field(
        default="",
        validation_alias=AliasChoices("jointExamGroupCode", "joint_exam_group_code"),
    )
    subjectCode: str = Field(
        default="",
        validation_alias=AliasChoices("subjectCode", "subject_code"),
    )
    name: str = Field(min_length=1)
    sort: int = Field(ge=0)
    status: str = Field(min_length=1)
    extJson: dict[str, object] = Field(default_factory=dict)
    createTime: Optional[str] = None
    updateTime: Optional[str] = None

    @field_validator("name")
    @classmethod
    def trim_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("name 不能为空。")
        return value

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str) -> str:
        value = value.strip()
        if value not in KNOWLEDGE_STATUSES:
            raise ValueError(f"status 仅支持 {', '.join(KNOWLEDGE_STATUSES)}。")
        return value

    @field_validator("policyVersionCode", "examCategoryCode", "jointExamGroupCode", "subjectCode")
    @classmethod
    def trim_scope_fields(cls, value: str) -> str:
        return str(value or "").strip()

    @field_validator("extJson")
    @classmethod
    def validate_ext_json_object(cls, value: object) -> dict[str, object]:
        if not isinstance(value, dict):
            raise ValueError("extJson 必须是 JSON 对象。")
        return dict(value)


class ImportResultModel(BaseModel):
    imported: int
    failed: int
    errors: list[str]


class PaperAutoRuleModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: str
    count: int = Field(ge=1)
    questionScore: int = Field(ge=1)

    @field_validator("type")
    @classmethod
    def validate_rule_type(cls, value: str) -> str:
        value = value.strip()
        if value not in QUESTION_TYPES:
            raise ValueError(f"type 仅支持 {', '.join(QUESTION_TYPES)}。")
        return value


def _normalize_paper_scope_model(
    exam_category_code: str,
    joint_exam_group_code: str,
    subject_code: str,
) -> tuple[str, str, str]:
    normalized_exam_category_code = str(exam_category_code or "").strip()
    normalized_joint_exam_group_code = str(joint_exam_group_code or "").strip()
    normalized_subject_code = str(subject_code or "").strip()
    has_any_scope = any((normalized_exam_category_code, normalized_joint_exam_group_code, normalized_subject_code))
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

    if not normalized_subject_code:
        return normalized_exam_category_code, normalized_joint_exam_group_code, ""

    public_subject_codes = {
        str(item.get("subjectCode", "")).strip()
        for item in PUBLIC_SUBJECTS
        if isinstance(item, dict)
    }
    if normalized_subject_code in public_subject_codes:
        return normalized_exam_category_code, normalized_joint_exam_group_code, normalized_subject_code

    professional_subjects = joint_exam_group.get("professionalSubjects", []) if joint_exam_group else []
    if not isinstance(professional_subjects, list):
        professional_subjects = []
    matched = any(
        str(item.get("subjectCode", "")).strip() == normalized_subject_code
        for item in professional_subjects
        if isinstance(item, dict)
    )
    if not matched:
        raise ValueError("subjectCode 不属于当前 jointExamGroupCode。")
    return normalized_exam_category_code, normalized_joint_exam_group_code, normalized_subject_code


class PaperManualModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    paperId: Optional[str] = None
    paperName: str = Field(min_length=1)
    policyVersion: str = Field(
        default="HB_ZSB_2026",
        validation_alias=AliasChoices("policyVersion", "policy_version", "policyVersionCode"),
    )
    subjectId: str = Field(
        default="",
        validation_alias=AliasChoices("subjectId", "subject_id"),
    )
    examCategoryCode: str = Field(
        default="",
        validation_alias=AliasChoices("examCategoryCode", "exam_category_code"),
    )
    jointExamGroupCode: str = Field(
        default="",
        validation_alias=AliasChoices("jointExamGroupCode", "joint_exam_group_code"),
    )
    subjectCode: str = Field(
        default="",
        validation_alias=AliasChoices("subjectCode", "subject_code"),
    )
    paperType: str = Field(min_length=1)
    paperStatus: str = Field(min_length=1)
    durationMinutes: int = Field(ge=1, le=240)
    totalScore: int = Field(ge=1)
    visibleToStudents: bool = True
    publishClassIds: List[str] = Field(
        default_factory=list,
        validation_alias=AliasChoices(
            "publishClassIds",
            "publish_class_ids",
            "targetClassIds",
            "target_class_ids",
        ),
    )
    questionIds: List[str] = Field(min_length=1)
    questionScores: Dict[str, int] = Field(default_factory=dict)

    @field_validator("subjectId")
    @classmethod
    def validate_subject_id(cls, value: str) -> str:
        return str(value or "").strip()

    @field_validator("publishClassIds")
    @classmethod
    def validate_publish_class_ids(cls, value: List[str]) -> List[str]:
        normalized: List[str] = []
        seen = set()
        for item in value or []:
            class_id = str(item).strip()
            if not class_id or class_id in seen:
                continue
            seen.add(class_id)
            normalized.append(class_id)
        return normalized

    @field_validator("questionScores")
    @classmethod
    def validate_question_scores(cls, value: Dict[str, int]) -> Dict[str, int]:
        normalized: Dict[str, int] = {}
        for question_id, score in (value or {}).items():
            normalized_question_id = str(question_id).strip()
            if not normalized_question_id:
                raise ValueError("questionScores 的键不能为空。")
            normalized_score = int(score)
            if normalized_score < 1:
                raise ValueError("questionScores 的分值必须 >= 1。")
            normalized[normalized_question_id] = normalized_score
        return normalized

    @model_validator(mode="after")
    def validate_professional_scope(self) -> "PaperManualModel":
        self.subjectId = str(self.subjectId or "").strip()
        self.subjectCode = str(self.subjectCode or "").strip()
        if not self.subjectId and self.subjectCode:
            self.subjectId = self.subjectCode
        (
            self.examCategoryCode,
            self.jointExamGroupCode,
            self.subjectCode,
        ) = _normalize_paper_scope_model(
            self.examCategoryCode,
            self.jointExamGroupCode,
            self.subjectCode,
        )
        return self


class PaperAutoModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    paperId: Optional[str] = None
    policyVersion: str = Field(
        default=POLICY_VERSION_CODE,
        validation_alias=AliasChoices("policyVersion", "policy_version", "policyVersionCode"),
    )
    paperName: str = Field(min_length=1)
    paperType: str = Field(min_length=1)
    paperStatus: str = Field(min_length=1)
    durationMinutes: int = Field(ge=1, le=240)
    totalScore: int = Field(ge=1)
    visibleToStudents: bool = True
    subjectId: str = Field(
        default="",
        validation_alias=AliasChoices("subjectId", "subject_id"),
    )
    examCategoryCode: str = Field(
        default="",
        validation_alias=AliasChoices("examCategoryCode", "exam_category_code"),
    )
    jointExamGroupCode: str = Field(
        default="",
        validation_alias=AliasChoices("jointExamGroupCode", "joint_exam_group_code"),
    )
    subjectCode: str = Field(
        default="",
        validation_alias=AliasChoices("subjectCode", "subject_code"),
    )
    chapter: str = ""
    difficulty: str = ""
    typeRules: List[PaperAutoRuleModel] = Field(min_length=1)

    @field_validator("policyVersion")
    @classmethod
    def validate_policy_version(cls, value: str) -> str:
        normalized = str(value or "").strip()
        if not normalized:
            raise ValueError("policyVersion 不能为空。")
        return normalized

    @model_validator(mode="after")
    def validate_professional_scope(self) -> "PaperAutoModel":
        self.subjectId = str(self.subjectId or "").strip()
        self.subjectCode = str(self.subjectCode or "").strip()
        if not self.subjectId and self.subjectCode:
            self.subjectId = self.subjectCode
        (
            self.examCategoryCode,
            self.jointExamGroupCode,
            self.subjectCode,
        ) = _normalize_paper_scope_model(
            self.examCategoryCode,
            self.jointExamGroupCode,
            self.subjectCode,
        )
        return self


class PracticeSubmitModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    answer: str = Field(min_length=1)
    elapsedSec: int = Field(ge=0, le=3600)
    assignmentId: str = ""


class PaperAnswerModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    questionId: str = Field(min_length=1)
    answer: str = Field(min_length=1)
    elapsedSec: int = Field(ge=0, le=3600)
    marked: bool = False


class PaperSubmitModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    answers: List[PaperAnswerModel] = Field(min_length=1)
    totalElapsedSec: int = Field(ge=0, le=14400)


class StudentProfileModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    examCategoryCode: str = Field(min_length=1)
    jointExamGroupCode: str = Field(min_length=1)


class StudentSubmitModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    answeredCount: int = Field(ge=0, le=5000)
    elapsedSec: int = Field(ge=0, le=43200)


class AiMarkingSubmitModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    answer: str = Field(min_length=1)
    answerImageUrl: str = ""
    assignmentId: str = ""


class AiTutorAskModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    prompt: str = Field(min_length=1)
    promptImageUrl: str = ""


class SystemSettingsModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    platformName: str = Field(min_length=1)
    defaultExamMinutes: int = Field(ge=30, le=240)
    dailyCheckInPoints: int = Field(ge=0, le=200)
    practiceRewardThreshold: int = Field(ge=1, le=200)
    practiceRewardPoints: int = Field(ge=0, le=200)
    paperRewardPoints: int = Field(ge=0, le=200)
    wrongBookRewardThreshold: int = Field(ge=1, le=200)
    wrongBookRewardPoints: int = Field(ge=0, le=200)
    aiDailyLimit: int = Field(ge=1, le=200)
    mockExamRuleProfiles: Dict[str, object] = Field(default_factory=dict)


class SyllabusVersionCreateModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    versionName: str = Field(min_length=1, max_length=80)
    copyFromVersionId: str = ""

    @field_validator("versionName", "copyFromVersionId")
    @classmethod
    def trim_text_fields(cls, value: str) -> str:
        return value.strip()


class SyllabusWeightItemModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    knowledgeId: str = Field(min_length=1)
    targetWeight: float = Field(ge=0.0, le=1.0)

    @field_validator("knowledgeId")
    @classmethod
    def trim_knowledge_id(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("knowledgeId 不能为空。")
        return value


class SyllabusWeightsSaveModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    knowledgeWeights: List[SyllabusWeightItemModel] = Field(min_length=1)


class ManagedUserModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    userId: Optional[str] = Field(default=None)
    role: str = Field(min_length=1)
    name: str = Field(min_length=1)
    mobile: str = Field(min_length=11, max_length=11)
    enabled: bool = True
    permissions: List[str] = Field(default_factory=list)
    examCategoryCode: str = ""
    jointExamGroupCode: str = ""
    vocationalMajor: str = ""
    prepStage: str = ""
    postTags: List[str] = Field(default_factory=list)
    managedStudentIds: List[str] = Field(default_factory=list)
    managedJointExamGroupCodes: List[str] = Field(default_factory=list)

    @field_validator(
        "name",
        "mobile",
        "examCategoryCode",
        "jointExamGroupCode",
        "vocationalMajor",
        "prepStage",
    )
    @classmethod
    def trim_text_fields(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        return value.strip()
    
    @field_validator("userId")
    @classmethod
    def trim_user_id(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        trimmed = value.strip()
        # 对于 userId 字段，如果修剪后为空字符串，则返回 None
        if trimmed == "":
            return None
        return trimmed

    @field_validator("role")
    @classmethod
    def validate_role(cls, value: str) -> str:
        value = value.strip()
        if value not in ALL_ROLES:
            raise ValueError("role 不合法。")
        return value

    @field_validator("mobile")
    @classmethod
    def validate_mobile(cls, value: str) -> str:
        if not re.fullmatch(r"1\d{10}", value):
            raise ValueError("mobile 必须是合法中国大陆手机号。")
        return value

    @field_validator("permissions")
    @classmethod
    def validate_permissions(cls, value: List[str]) -> List[str]:
        normalized = []
        for item in value:
            item = item.strip()
            if item not in MANAGED_PERMISSION_KEYS:
                raise ValueError("permissions 存在非法值。")
            normalized.append(item)
        return normalized

    @field_validator("postTags")
    @classmethod
    def validate_post_tags(cls, value: List[str]) -> List[str]:
        normalized = []
        for item in value:
            tag = str(item or "").strip()
            if not tag:
                continue
            if tag not in MANAGED_TEACHER_POST_TAGS:
                raise ValueError("postTags 存在非法值。")
            if tag not in normalized:
                normalized.append(tag)
        return normalized

    @field_validator("managedStudentIds", "managedJointExamGroupCodes")
    @classmethod
    def normalize_scope_ids(cls, value: List[str]) -> List[str]:
        normalized = []
        for item in value:
            key = str(item or "").strip()
            if not key or key in normalized:
                continue
            normalized.append(key)
        return normalized


class MessageSettingsModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    allowAiTutor: bool = True
    allowSystemNotice: bool = True
    allowReviewNotice: bool = True
    allowStudyReminder: bool = True
    allowWeeklyReport: bool = True
    allowPointsNotice: bool = True


class SendMessageModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    targetMode: str = "userIds"
    userIds: List[str] = Field(default_factory=list)
    examCategoryCode: str = ""
    jointExamGroupCode: str = ""
    subjectCode: str = ""
    sendAt: str = ""
    category: str = Field(min_length=1)
    title: str = Field(min_length=1)
    content: str = Field(min_length=1)

    @field_validator("targetMode")
    @classmethod
    def validate_target_mode(cls, value: str) -> str:
        normalized = value.strip() or "userIds"
        if normalized not in {"userIds", "cohort"}:
            raise ValueError("targetMode 仅支持 userIds 或 cohort。")
        return normalized

    @field_validator("category")
    @classmethod
    def validate_category(cls, value: str) -> str:
        value = value.strip()
        if value not in MESSAGE_CATEGORIES:
            raise ValueError("category 不合法。")
        return value

    @field_validator("userIds")
    @classmethod
    def validate_user_ids(cls, value: List[str], info) -> List[str]:
        normalized = [str(item).strip() for item in value if str(item).strip()]
        target_mode = str(info.data.get("targetMode", "userIds"))
        if target_mode == "userIds" and not normalized:
            raise ValueError("userIds 不能为空。")
        if target_mode == "cohort":
            exam_category_code = str(info.data.get("examCategoryCode", "")).strip()
            joint_exam_group_code = str(info.data.get("jointExamGroupCode", "")).strip()
            subject_code = str(info.data.get("subjectCode", "")).strip()
            if not exam_category_code and not joint_exam_group_code and not subject_code:
                raise ValueError("分群发送至少需要提供 examCategoryCode、jointExamGroupCode、subjectCode 中的一项。")
        return normalized


class BatchQuestionStatusModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    policyVersion: str = Field(
        default=POLICY_VERSION_CODE,
        validation_alias=AliasChoices("policyVersion", "policy_version", "policyVersionCode"),
    )
    questionIds: List[str] = Field(min_length=1)
    targetStatus: str = Field(min_length=1)
    reason: str = ""

    @field_validator("policyVersion")
    @classmethod
    def validate_policy_version(cls, value: str) -> str:
        normalized = str(value or "").strip()
        if not normalized:
            raise ValueError("policyVersion 不能为空。")
        return normalized

    @field_validator("questionIds")
    @classmethod
    def validate_question_ids(cls, value: List[str]) -> List[str]:
        normalized = [str(item).strip() for item in value if str(item).strip()]
        if not normalized:
            raise ValueError("questionIds 不能为空。")
        return normalized

    @field_validator("targetStatus")
    @classmethod
    def validate_target_status(cls, value: str) -> str:
        value = value.strip()
        if value not in QUESTION_STATUSES:
            raise ValueError(f"targetStatus 仅支持 {', '.join(QUESTION_STATUSES)}。")
        return value


class BatchQuestionDeleteModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    policyVersion: str = Field(
        default=POLICY_VERSION_CODE,
        validation_alias=AliasChoices("policyVersion", "policy_version", "policyVersionCode"),
    )
    questionIds: List[str] = Field(min_length=1)

    @field_validator("policyVersion")
    @classmethod
    def validate_policy_version(cls, value: str) -> str:
        normalized = str(value or "").strip()
        if not normalized:
            raise ValueError("policyVersion 不能为空。")
        return normalized

    @field_validator("questionIds")
    @classmethod
    def validate_question_ids(cls, value: List[str]) -> List[str]:
        normalized = [str(item).strip() for item in value if str(item).strip()]
        if not normalized:
            raise ValueError("questionIds 不能为空。")
        return normalized


class PaperTemplateModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    templateId: Optional[str] = None
    policyVersion: str = Field(
        default="HB_ZSB_2026",
        validation_alias=AliasChoices("policyVersion", "policy_version", "policyVersionCode"),
    )
    templateName: str = Field(min_length=1)
    paperType: str = Field(min_length=1)
    subjectId: str = Field(
        default="",
        validation_alias=AliasChoices("subjectId", "subject_id"),
    )
    chapter: str = ""
    difficulty: str = ""
    totalScore: int = Field(ge=1)
    durationMinutes: int = Field(ge=1, le=240)
    examCategoryCode: str = ""
    jointExamGroupCode: str = ""
    subjectCode: str = Field(
        default="",
        validation_alias=AliasChoices("subjectCode", "subject_code"),
    )
    typeRules: List[PaperAutoRuleModel] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_professional_scope(self) -> "PaperTemplateModel":
        self.subjectId = str(self.subjectId or "").strip()
        self.subjectCode = str(self.subjectCode or "").strip()
        if not self.subjectId and self.subjectCode:
            self.subjectId = self.subjectCode
        (
            self.examCategoryCode,
            self.jointExamGroupCode,
            self.subjectCode,
        ) = _normalize_paper_scope_model(
            self.examCategoryCode,
            self.jointExamGroupCode,
            self.subjectCode,
        )
        return self


class SmsCodeRequestModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    phone: str = Field(min_length=11, max_length=11)
    purpose: str = Field(min_length=1)

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str) -> str:
        value = value.strip()
        if not re.fullmatch(r"1\d{10}", value):
            raise ValueError("phone 必须是合法中国大陆手机号。")
        return value

    @field_validator("purpose")
    @classmethod
    def validate_purpose(cls, value: str) -> str:
        value = value.strip()
        allowed = {"register", "login", "reset_password"}
        if value not in allowed:
            raise ValueError("purpose 仅支持 register、login、reset_password。")
        return value


class AuthRegisterModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    phone: str = Field(min_length=11, max_length=11)
    smsCode: str = Field(min_length=4, max_length=8)
    password: str = Field(min_length=6, max_length=18)
    role: str = Field(min_length=1)
    name: str = Field(min_length=1)
    examCategoryCode: str = ""
    jointExamGroupCode: str = ""
    vocationalMajor: str = ""
    prepStage: str = ""
    employeeNo: str = ""

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str) -> str:
        value = value.strip()
        if not re.fullmatch(r"1\d{10}", value):
            raise ValueError("phone 必须是合法中国大陆手机号。")
        return value

    @field_validator("role")
    @classmethod
    def validate_role(cls, value: str) -> str:
        value = value.strip()
        if value not in ALL_ROLES:
            raise ValueError("role 不合法。")
        return value

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        value = value.strip()
        if not re.fullmatch(r"(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d]{6,18}", value):
            raise ValueError("password 需为 6-18 位字母+数字组合。")
        return value

    @field_validator("smsCode", "name", "examCategoryCode", "jointExamGroupCode", "vocationalMajor", "prepStage", "employeeNo")
    @classmethod
    def trim_text(cls, value: str) -> str:
        return value.strip()


class AuthLoginPasswordModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    phone: str = Field(min_length=11, max_length=11)
    password: str = Field(min_length=1, max_length=64)

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str) -> str:
        value = value.strip()
        if not re.fullmatch(r"1\d{10}", value):
            raise ValueError("phone 必须是合法中国大陆手机号。")
        return value

    @field_validator("password")
    @classmethod
    def trim_password(cls, value: str) -> str:
        return value.strip()


class AuthLoginSmsModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    phone: str = Field(min_length=11, max_length=11)
    smsCode: str = Field(min_length=4, max_length=8)

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str) -> str:
        value = value.strip()
        if not re.fullmatch(r"1\d{10}", value):
            raise ValueError("phone 必须是合法中国大陆手机号。")
        return value

    @field_validator("smsCode")
    @classmethod
    def trim_code(cls, value: str) -> str:
        return value.strip()


class AuthPasswordResetModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    phone: str = Field(min_length=11, max_length=11)
    smsCode: str = Field(min_length=4, max_length=8)
    newPassword: str = Field(min_length=6, max_length=18)

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str) -> str:
        value = value.strip()
        if not re.fullmatch(r"1\d{10}", value):
            raise ValueError("phone 必须是合法中国大陆手机号。")
        return value

    @field_validator("smsCode")
    @classmethod
    def trim_code(cls, value: str) -> str:
        return value.strip()

    @field_validator("newPassword")
    @classmethod
    def validate_password(cls, value: str) -> str:
        value = value.strip()
        if not re.fullmatch(r"(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d]{6,18}", value):
            raise ValueError("newPassword 需为 6-18 位字母+数字组合。")
        return value


ModelType = TypeVar("ModelType", bound=BaseModel)


def _parse_model(model_type: type[ModelType], payload: dict[str, Any]) -> ModelType:
    try:
        return model_type.model_validate(payload)
    except Exception as exc:
        raise validation_failed(str(exc)) from exc


def parse_question_model(payload: dict[str, Any]) -> QuestionWriteModel:
    return _parse_model(QuestionWriteModel, payload)


def parse_knowledge_model(payload: dict[str, Any]) -> KnowledgeWriteModel:
    return _parse_model(KnowledgeWriteModel, payload)


def parse_paper_manual_model(payload: dict[str, Any]) -> PaperManualModel:
    return _parse_model(PaperManualModel, payload)


def parse_paper_auto_model(payload: dict[str, Any]) -> PaperAutoModel:
    return _parse_model(PaperAutoModel, payload)


def parse_practice_submit_model(payload: dict[str, Any]) -> PracticeSubmitModel:
    return _parse_model(PracticeSubmitModel, payload)


def parse_paper_submit_model(payload: dict[str, Any]) -> PaperSubmitModel:
    return _parse_model(PaperSubmitModel, payload)


def parse_student_profile_model(payload: dict[str, Any]) -> StudentProfileModel:
    return _parse_model(StudentProfileModel, payload)


def parse_student_submit_model(payload: dict[str, Any]) -> StudentSubmitModel:
    return _parse_model(StudentSubmitModel, payload)


def parse_ai_marking_submit_model(payload: dict[str, Any]) -> AiMarkingSubmitModel:
    return _parse_model(AiMarkingSubmitModel, payload)


def parse_ai_tutor_ask_model(payload: dict[str, Any]) -> AiTutorAskModel:
    return _parse_model(AiTutorAskModel, payload)


def parse_system_settings_model(payload: dict[str, Any]) -> SystemSettingsModel:
    return _parse_model(SystemSettingsModel, payload)


def parse_syllabus_version_create_model(payload: dict[str, Any]) -> SyllabusVersionCreateModel:
    return _parse_model(SyllabusVersionCreateModel, payload)


def parse_syllabus_weights_save_model(payload: dict[str, Any]) -> SyllabusWeightsSaveModel:
    return _parse_model(SyllabusWeightsSaveModel, payload)


def parse_managed_user_model(payload: dict[str, Any]) -> ManagedUserModel:
    return _parse_model(ManagedUserModel, payload)


def parse_message_settings_model(payload: dict[str, Any]) -> MessageSettingsModel:
    return _parse_model(MessageSettingsModel, payload)


def parse_send_message_model(payload: dict[str, Any]) -> SendMessageModel:
    return _parse_model(SendMessageModel, payload)


def parse_status_transition_payload_model(payload: dict[str, Any]) -> StatusTransitionPayloadModel:
    return _parse_model(StatusTransitionPayloadModel, payload)


def parse_batch_question_status_model(payload: dict[str, Any]) -> BatchQuestionStatusModel:
    return _parse_model(BatchQuestionStatusModel, payload)


def parse_batch_question_delete_model(payload: dict[str, Any]) -> BatchQuestionDeleteModel:
    return _parse_model(BatchQuestionDeleteModel, payload)


def parse_paper_template_model(payload: dict[str, Any]) -> PaperTemplateModel:
    return _parse_model(PaperTemplateModel, payload)


def parse_sms_code_request_model(payload: dict[str, Any]) -> SmsCodeRequestModel:
    return _parse_model(SmsCodeRequestModel, payload)


def parse_auth_register_model(payload: dict[str, Any]) -> AuthRegisterModel:
    return _parse_model(AuthRegisterModel, payload)


def parse_auth_login_password_model(payload: dict[str, Any]) -> AuthLoginPasswordModel:
    return _parse_model(AuthLoginPasswordModel, payload)


def parse_auth_login_sms_model(payload: dict[str, Any]) -> AuthLoginSmsModel:
    return _parse_model(AuthLoginSmsModel, payload)


def parse_auth_password_reset_model(payload: dict[str, Any]) -> AuthPasswordResetModel:
    return _parse_model(AuthPasswordResetModel, payload)
