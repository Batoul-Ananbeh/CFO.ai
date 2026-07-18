class ScoringEngine:

    # -----------------------------
    # Growth Score
    # -----------------------------

    def growth_score(self, growth_percent):

        score = 50 + growth_percent

        return max(
            0,
            min(100, score)
        )

    # -----------------------------
    # Dependency Score
    # -----------------------------

    def dependency_score(

        self,

        dependency_percent

    ):

        score = 100 - (
            dependency_percent * 10
        )

        return max(
            0,
            min(100, score)
        )

    # -----------------------------
    # Stability Score
    # -----------------------------

    def stability_score(

        self,

        stability

    ):

        return max(
            0,
            min(100, stability)
        )