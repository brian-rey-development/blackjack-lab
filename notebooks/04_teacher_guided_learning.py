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
    # Learning with a teacher

    **Question.** Does a fading prior from a decision model cut the hands needed, and does a bad teacher do harm?

    Written in Batch 8 of `docs/plan.md`.
    """)
    return


if __name__ == "__main__":
    app.run()
