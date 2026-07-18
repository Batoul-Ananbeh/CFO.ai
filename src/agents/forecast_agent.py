# src/agents/forecast_agent.py

from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI
from src.agents.prompts import FORECAST_PROMPT

def run_forecast_agent(state: dict) -> dict:
    """
    وكيل التنبؤ المالي: يستلم تقرير السيولة الحالي من الـ Finance Agent،
    ويقوم بإنشاء توقعات مالية مستقبلية لـ 90 يوماً للأمام.
    """
    # 1. إعداد النموذج (نثبّت الـ Temperature عند 0 لمنع التخمين العشوائي في الأرقام)
    llm = ChatOpenAI(model="gpt-4o", temperature=0)
    
    # 2. استخراج المخرجات التي جهزها الوكيل السابق من الـ State
    finance_report = state.get("finance_report", "لا يوجد تقرير مالي متاح من الوكيل السابق.")
    user_query = state.get("user_query", "")
    
    # 3. استدعاء البرومبت المخصص للتنبؤ من ملف prompts.py
    system_instruction = FORECAST_PROMPT
    
    # 4. صياغة الرسالة الموجهة للـ LLM للربط بين الحاضر والمستقبل
    messages = [
        SystemMessage(content=system_instruction),
        HumanMessage(content=f"""
        سؤال رائد الأعمال: {user_query}
        
        تقرير الوضع المالي الحالي المستلم:
        {finance_report}
        
        بناءً على هذه المعطيات الحالية، قم بتحليل الأنماط بشكل استباقي وتوقع حركة السيولة والنقد القادمة (لفترة 30 يوماً و 90 يوماً).
        ركز على كشف أي فترات حرجة قد يقل فيها الكاش أو يرتفع فيها معدل الحرق بشكل خطر.
        """)
    ]
    
    # 5. تشغيل الوكيل
    response = llm.invoke(messages)
    
    # 6. حفظ التوقعات المستقبلية في الـ State ليمر إلى وكيل المخاطر التالي
    state["forecast_report"] = response.content
    
    print("\n[✔] Forecast Agent: تم الانتهاء من بناء التوقعات المالية والمدرج المالي لـ 90 يوماً بنجاح.")
    return state