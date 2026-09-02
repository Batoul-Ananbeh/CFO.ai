from src.agents.chief_cfo import ChiefCFO

chief = ChiefCFO(

    "Data/online_retail_II.csv"

)

report = chief.run()

print(report["AI_Report"])