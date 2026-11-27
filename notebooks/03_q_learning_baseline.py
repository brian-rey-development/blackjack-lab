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
    # Q-learning from scratch

    **Question.** How many hands does an agent need to discover optimal play on its own, and why is it so noisy?

    Written in Batch 7 of `docs/plan.md`.
    """)
    return


if __name__ == "__main__":
    app.run()
