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
    # Zero-shot play and calibration

    **Question.** How well does a teacher play with no training, and does a stated 70% come true 70% of the time?

    Written in Batch 6 of `docs/plan.md`.
    """)
    return


if __name__ == "__main__":
    app.run()
