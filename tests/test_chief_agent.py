from src.agents.chief_cfo import ChiefCFO

chief = ChiefCFO(

    "Data/online_retail_II.csv"

)

result = chief.run()

print("=" * 60)

print("CHIEF CFO AGENT")

print("=" * 60)

for k, v in result.items():

    print()

    print(k)

    print(v)