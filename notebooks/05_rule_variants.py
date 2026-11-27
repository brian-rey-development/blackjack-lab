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
    # Reasoning or recall

    **Question.** When the rules change so memorised strategy is wrong, does the teacher still help?

    Written in Batch 8 of `docs/plan.md`.
    """)
    return


if __name__ == "__main__":
    app.run()
