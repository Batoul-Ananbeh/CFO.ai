"""Safe explanation layer for General Ledger results."""

from __future__ import annotations

from src.schemas.enums import LedgerDecisionStatus
from src.schemas.general_ledger import GeneralLedgerResult


def explain_general_ledger_result(
    result: GeneralLedgerResult,
) -> str:
    """
    Explain a GL result without changing its values or decision.
    """

    if result.journal_entry is None:
        return (
            "لم يتم إنشاء قيد محاسبي لأن البيانات المتوفرة لم تكن كافية "
            "أو لأن العملية تحتاج إلى مراجعة إضافية."
        )

    journal = result.journal_entry

    if (
        result.decision_status
        == LedgerDecisionStatus.READY_FOR_CONTROLLER_REVIEW
    ):
        debit_line = journal.lines[0]
        credit_line = journal.lines[1]

        return (
            "تم تجهيز قيد محاسبي مبدئي ومتوازن. "
            f"تم تسجيل {debit_line.debit.amount} "
            f"{debit_line.debit.currency} في الحساب المدين "
            f"{debit_line.account_name}، وتم تسجيل نفس القيمة في الحساب "
            f"الدائن {credit_line.account_name}. "
            "فرق القيد يساوي صفر، والقيد جاهز لمراجعة "
            "Financial Controller Agent."
        )

    if result.decision_status == LedgerDecisionStatus.REQUIRES_CORRECTION:
        return (
            "لا يمكن إرسال القيد إلى Controller لأن البيانات أو القيد "
            "تحتاج إلى تصحيح."
        )

    if (
        result.decision_status
        == LedgerDecisionStatus.ACCOUNT_MAPPING_REQUIRED
    ):
        return (
            "تعذر تحديد الحساب المحاسبي المناسب للعملية. يجب مراجعة "
            "Chart of Accounts أو إضافة Account Mapping معتمد."
        )

    if result.decision_status == LedgerDecisionStatus.POTENTIAL_DUPLICATE:
        return (
            "تم اكتشاف مؤشرات على أن العملية قد تكون مكررة. يجب التحقق "
            "منها قبل تجهيز القيد."
        )

    if result.decision_status == LedgerDecisionStatus.BLOCKED:
        return (
            "تم إيقاف تجهيز القيد بسبب وجود مشكلة رقابية أو مالية تمنع "
            "متابعة العملية."
        )

    if result.decision_status == LedgerDecisionStatus.INSUFFICIENT_DATA:
        return (
            "لا توجد بيانات كافية لإنشاء القيد دون افتراض معلومات غير "
            "موجودة."
        )

    return result.summary