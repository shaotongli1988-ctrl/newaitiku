from __future__ import annotations

# Observability note: helper mixins should preserve shared log/trace/metric readiness semantics.
from app.service_modules.internal_analytics import InternalAnalyticsServiceMixin
from app.service_modules.internal_core import InternalCoreServiceMixin
from app.service_modules.internal_question_paper import InternalQuestionPaperServiceMixin
from app.service_modules.internal_student import InternalStudentServiceMixin
from app.service_modules.internal_system_admin import InternalSystemAdminServiceMixin


class InternalHelperServiceMixin(
    InternalCoreServiceMixin,
    InternalSystemAdminServiceMixin,
    InternalQuestionPaperServiceMixin,
    InternalStudentServiceMixin,
    InternalAnalyticsServiceMixin,
):
    """Compatibility aggregate for internal helper mixins."""
