from fastapi import FastAPI

from src.agents.chief_cfo import ChiefCFO

app = FastAPI(

    title="CFO.ai API",

    version="1.0.0"

)

chief = ChiefCFO(

    "Data/online_retail_II.csv"

)


@app.get("/")

def home():

    return {

        "message": "Welcome to CFO.ai"

    }


@app.get("/analyze")

def analyze():

    return chief.run()


@app.get("/finance")
def finance():

    return chief.finance.analyze()


@app.get("/forecast")
def forecast():

    finance = chief.finance.analyze()

    return chief.forecast.analyze(

        finance["monthly"]

    )

@app.get("/risk")
def risk():

    finance = chief.finance.analyze()

    growth = chief.finance.engine.growth_rate()

    growth_score = chief.scoring.growth_score(growth)

    return chief.risk.analyze(

        growth_score,

        finance["stability"],

        finance["dependency"]

    )

@app.get("/fii")
def fii():

    return chief.run()["FII"]

@app.get("/decision")
def decision():

    return chief.run()["Decision"]