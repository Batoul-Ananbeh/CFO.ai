# src/agents/strategy_agent.py

from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI
from src.agents.prompts import RECOMMENDATION_PROMPT

def run_strategy_agent(state: dict) -> dict:
    """
    وكيل الاستراتيجية والقرارات: يطبق محاكاة "ماذا لو" بناءً على رغبة المستخدم
    ويصيغ الحلول البديلة والخطط التشغيلية المحكمة.
    """
    # 1. إعداد النموذج (نحافظ على حرارة 0 لتقديم توصيات عقلانية ومبنية على الأرقام)
    llm = ChatOpenAI(model="gpt-4o", temperature=0)
    
    # 2. استخراج التقارير التراكمية من الـ State
    finance_report = state.get("finance_report", "لا يوجد تقرير مالي متاح.")
    forecast_report = state.get("forecast_report", "لا توجد توقعات مالية متاحة.")
    risk_report = state.get("risk_report", "لا توجد تنبيهات مخاطر متاحة.")
    user_query = state.get("user_query", "")
    
    # 3. استدعاء البرومبت الاستراتيجي الذي صممته أنت في ملف prompts.py
    system_instruction = RECOMMENDATION_PROMPT
    
    # 4. بناء السياق الكامل لاتخاذ القرار الخارق الذي يتفوق على البشر
    messages = [
        SystemMessage(content=system_instruction),
        HumanMessage(content=f"""
        طلب أو سؤال رائد الأعمال الحركي: {user_query}
        
        [المعطيات المالية للحاضر]:
        {finance_report}
        
        [التوقعات المستقبلية لـ 90 يوماً]:
        {forecast_report}
        
        [التدقيق الأمني وتحليل المخاطر المستلم]:
        {risk_report}
        
        بناءً على هذا السياق الكامل، قم بعمل محاكاة افتراضية لقرار المستخدم. احسب الأثر بدقة، 
        وقدم توصياتك مرتبة حسب الأفضلية والأمان المالي. إذا كان القرار خطراً، اقترح السيناريو البديل فوراً.
        """)
    ]
    
    # 5. تشغيل الوكيل
    response = llm.invoke(messages)
    
    # 6. حفظ التوصية الاستراتيجية المعقدة في الـ State لتمريرها للمدير المالي النهائي
    state["strategy_report"] = response.content
    
    print("\n[✔] Strategy Agent: تم الانتهاء من محاكاة السيناريوهات وصياغة البدائل الاستثمارية بنجاح.")
    return state