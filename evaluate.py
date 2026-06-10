"""Evaluation harness — runs the 5 planning.md test questions end-to-end.

For each question it prints the expected answer, which chunks were retrieved
(course + cosine distance), the system's grounded answer, and the cited sources.
Used to fill the Evaluation Report and Failure Case Analysis in README.md.

    .venv/bin/python evaluate.py
"""
from query import ask

EVAL = [
    {
        "q": "How many hours per week do students report spending on CS 391L Machine Learning?",
        "expected": "Cluster at 10-15 hrs/week (15 most common; range ~5-30).",
    },
    {
        "q": "According to reviews, which is more difficult: CS 394D Deep Learning or CS 388 Natural Language Processing, and why?",
        "expected": "Roughly comparable; NLP marginally higher by avg rating (~4.7 vs ~4.4/7). Both project-heavy.",
    },
    {
        "q": "What do students recommend doing to prepare before taking CS 394R Reinforcement Learning?",
        "expected": "Take DL/NLP first (PyTorch); strong Python + Probability; little linear algebra.",
    },
    {
        "q": "How do CS 395T Optimization and CS 395T Online Learning and Optimization differ in workload and content?",
        "expected": "Workload ~equal (~10-11 hrs). Optimization = convex-opt foundations; OLO builds on it, two halves.",
    },
    {
        "q": "How is grading structured in CS 389L Automated Logical Reasoning - exams, projects, or both?",
        "expected": "Quizzes ~50%, programming assignments ~30%, homework ~20%; no traditional exams.",
    },
]


def main() -> None:
    for i, item in enumerate(EVAL, 1):
        r = ask(item["q"])
        retrieved = [(c["course"].split(" — ")[0], round(c["distance"], 3)) for c in r["chunks"]]
        print("=" * 72)
        print(f"Q{i}: {item['q']}")
        print(f"EXPECTED  : {item['expected']}")
        print(f"RETRIEVED : {retrieved}")
        print(f"ANSWER    : {r['answer']}")
        print(f"SOURCES   : {r['sources']}")
        print()


if __name__ == "__main__":
    main()
