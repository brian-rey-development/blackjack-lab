import marimo

__generated_with = "0.26.0"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo

    return (mo,)


@app.cell
def _(mo):
    mo.md(r"""
    # Rules and optimal play

    **Question.** What is the best possible way to play each of the 200 hands, and how do we know it is exact?

    Written in Batch 3 of `docs/plan.md`.
    """)
    return


if __name__ == "__main__":
    app.run()
