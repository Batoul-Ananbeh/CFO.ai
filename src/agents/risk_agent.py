# src/agents/risk_agent.py

from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI

# سنقوم بصياغة نظام البرومبت الخاص بالمخاطر مباشرة هنا أو يمكنك نقله لملف prompts.py لاحقاً
RISK_PROMPT = """
أنت خبير إدارة المخاطر المالية والتدقيق الرقمي (Risk & Auditor Agent).
مهمتك الأساسية هي فحص البيانات الحالية والتوقعات المستقبلية الممررة إليك لاكتشاف نقاط الضعف وصدمات السيولة قبل حدوثها.
يجب عليك:
1. تحديد أي تضخم غير طبيعي في المصاريف (Overspending).
2. تقييم مدى أمان المدرج المالي (Runway) وتحديد اللحظة التي قد يتقاطع فيها الكاش مع الصفر.
3. إصدار تنبيهات مخاطر (Risk Alerts) واضحة ومحددة بالأيام أو الأسابيع إذا كشفت عن عجز مستقبلي متوقع.
"""

def run_risk_agent(state: dict) -> dict:
    """
    وكيل إدارة المخاطر: يفحص التوقعات والتقارير المالية السابقة ويطلق تنبيهات العجز والسيولة.
    """
    # 1. إعداد النموذج بحرارة 0 لضمان الصرامة والدقة في تحديد المخاطر
    llm = ChatOpenAI(model="gpt-4o", temperature=0)
    
    # 2. استخراج التقارير السابقة من الـ State
    finance_report = state.get("finance_report", "لا يوجد تقرير مالي متاح.")
    forecast_report = state.get("forecast_report", "لا توجد توقعات مالية متاحة.")
    user_query = state.get("user_query", "")
    
    # 3. صياغة الرسالة الموجهة للـ LLM
    messages = [
        SystemMessage(content=RISK_PROMPT),
        HumanMessage(content=f"""
        سؤال رائد الأعمال: {user_query}
        
        [تقرير الحاضر]:
        {finance_report}
        
        [تقرير التوقعات المستقبلية لـ 90 يوماً]:
        {forecast_report}
        
        بناءً على هذه المعطيات، قم بإجراء تدقيق شامل للمخاطر المادية والتشغيلية التي قد تواجهها الشركة. 
        إذا كان هناك عجز مالي وشيك أو احتمالية لنفاذ السيولة بناءً على القرارات الحالية، حدد ذلك بدقة وأطلق صافرة الإنذار (Risk Alert).
        """)
    ]
    
    # 4. تشغيل الوكيل
    response = llm.invoke(messages)
    
    # 5. حفظ تقرير المخاطر في الـ State ليمر إلى وكيل الاستراتيجية والقرارات التالي
    state["risk_report"] = response.content
    
    print("\n[✔] Risk Agent: تم فحص المخاطر وإصدار تنبيهات الامتثال والسيولة الاستباقية بنجاح.")
    return state