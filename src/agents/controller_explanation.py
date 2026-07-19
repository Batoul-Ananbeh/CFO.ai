"""Safe explanation layer for Financial Controller results."""

from __future__ import annotations

from src.schemas.controller import ControllerResult
from src.schemas.enums import ControllerDecisionStatus


def explain_controller_result(
    result: ControllerResult,
) -> str:
    """
    Produce a reliable business explanation from an Engine result.

    This first version is deterministic. An LLM provider can later improve
    the language, but it will not be allowed to change the decision or values.
    """

    difference = result.balance_difference

    if result.decision_status == ControllerDecisionStatus.APPROVED:
        return (
            "تم اعتماد نتيجة المراجعة الأولية لأن إجمالي المدين يساوي "
            "إجمالي الدائن. لا يوجد فرق في ميزان المراجعة، ويمكن إرسال "
            "التقرير إلى المرحلة التالية من سير العمل."
        )

    if (
        result.decision_status
        == ControllerDecisionStatus.REQUIRES_CORRECTION
    ):
        if difference is None:
            return (
                "لا يمكن اعتماد التقرير لأن المراجعة اكتشفت خللًا يحتاج "
                "إلى تصحيح، لكن قيمة الفرق غير متوفرة."
            )

        return (
            "لا يمكن اعتماد ميزان المراجعة لأن إجمالي المدين لا يساوي "
            f"إجمالي الدائن. قيمة الفرق هي {difference.amount} "
            f"{difference.currency}. يجب على General Ledger Agent مراجعة "
            "القيود المحاسبية وحل الفرق قبل إعادة التقرير إلى Controller."
        )

    if (
        result.decision_status
        == ControllerDecisionStatus.REQUIRES_HUMAN_APPROVAL
    ):
        return (
            "اكتملت المراجعة، لكن القرار يتطلب موافقة بشرية مخولة قبل "
            "متابعة الإجراء."
        )

    if result.decision_status == ControllerDecisionStatus.BLOCKED:
        return (
            "تم إيقاف التقرير بسبب وجود مشكلة رقابية أو مالية تمنع "
            "متابعة سير العمل حتى تتم معالجتها."
        )

    if (
        result.decision_status
        == ControllerDecisionStatus.INSUFFICIENT_DATA
    ):
        return (
            "لا توجد بيانات كافية لإتمام المراجعة بشكل موثوق. يجب توفير "
            "البيانات والأدلة المطلوبة دون افتراض قيم غير موجودة."
        )

    return result.summary