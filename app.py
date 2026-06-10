"""Milestone 5 — Gradio query interface for The Unofficial Guide.

Run it:

    .venv/bin/python app.py

then open http://localhost:7860
"""
import gradio as gr

from query import ask


def handle_query(question: str):
    question = (question or "").strip()
    if not question:
        return "Please enter a question.", ""
    result = ask(question)
    sources = "\n".join(f"• {s}" for s in result["sources"])
    if not sources:
        sources = "(no sources — the reviews don't cover this)"
    return result["answer"], sources


EXAMPLES = [
    "How many hours per week do students spend on CS 391L Machine Learning?",
    "What should I do to prepare before taking Reinforcement Learning?",
    "How is grading structured in Automated Logical Reasoning?",
    "How do CS 395T Optimization and Online Learning and Optimization differ?",
]

with gr.Blocks(title="The Unofficial Guide — UT Austin MSAI") as demo:
    gr.Markdown(
        "# The Unofficial Guide — UT Austin MSAI\n"
        "Ask about course workload, difficulty, grading, lectures, and prep. "
        "Answers are generated **only** from real student reviews, with sources shown."
    )
    inp = gr.Textbox(label="Your question", placeholder="e.g. How heavy is the Deep Learning workload?")
    btn = gr.Button("Ask", variant="primary")
    answer = gr.Textbox(label="Answer", lines=8)
    sources = gr.Textbox(label="Retrieved from (sources)", lines=4)
    gr.Examples(EXAMPLES, inputs=inp)

    btn.click(handle_query, inputs=inp, outputs=[answer, sources])
    inp.submit(handle_query, inputs=inp, outputs=[answer, sources])


if __name__ == "__main__":
    demo.launch()
