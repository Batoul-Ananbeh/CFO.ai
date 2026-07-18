# src/agents/chief_cfo.py

from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI
from src.agents.prompts import CHIEF_CFO_PROMPT

def run_chief_cfo_agent(state: dict) -> dict:
    """
    المدير المالي التنفيذي (The Boss Agent): يجمع كل تقارير الوكلاء المتخصصين
    ويصيغ النتيجة النهائية بلغة طبيعية، بسيطة، ومباشرة لمساعدة رائد الأعمال على اتخاذ القرار.
    """
    # 1. إعداد النموذج (نرفع الـ Temperature قليلاً هنا إلى 0.3 لإعطاء مرونة وطلاقة لغوية ودودة في الصياغة)
    llm = ChatOpenAI(model="gpt-4o", temperature=0.3)
    
    # 2. استخراج كافة التقارير المتراكمة من الـ State لدمجها
    finance_report = state.get("finance_report", "لا يوجد تقرير مالي متاح.")
    forecast_report = state.get("forecast_report", "لا توجد توقعات مالية متاحة.")
    risk_report = state.get("risk_report", "لا توجد تنبيهات مخاطر متاحة.")
    strategy_report = state.get("strategy_report", "لا توجد توصيات استراتيجية متاحة.")
    user_query = state.get("user_query", "")
    
    # 3. استدعاء البرومبت القيادي والنهائي من ملف prompts.py
    system_instruction = CHIEF_CFO_PROMPT
    
    # 4. بناء سياق القرار النهائي الموجه للمستخدم البشري
    messages = [
        SystemMessage(content=system_instruction),
        HumanMessage(content=f"""
        سؤال رائد الأعمال البشري: {user_query}
        
        إليك خلاصة أعمال كافة أقسام كادرك المالي الافتراضي خلف الكواليس:
        ------------------------------------
        [تقرير المحاسبة والسيولة الحالية]:
        {finance_report}
        
        [تقرير التنبؤ المالي لـ 90 يوماً]:
        {forecast_report}
        
        [تقرير تدقيق المخاطر]:
        {risk_report}
        
        [تقرير المحاكاة والسيناريوهات البديلة]:
        {strategy_report}
        ------------------------------------
        
        بناءً على هذه اللوحة المالية الكاملة، تحدث الآن مع رائد الأعمال مباشرة كـ AI CFO وصديق مقرب له.
        أعطه القرار والحل المناسب لشركته بأسلوب مباشر، ودود، وخالٍ من التعقيد الرياضي، ليعرف خطوته القادمة فوراً.
        """)
    ]
    
    # 5. تشغيل الوكيل القائد
    response = llm.invoke(messages)
    
    # 6. حفظ الرد النهائي الموجه للمستخدم في الـ State
    state["final_decision"] = response.content
    
    print("\n[✔] Chief CFO Agent: تم صياغة القرار الاستشاري النهائي بلغة الأعمال المفهومة.")
    return state