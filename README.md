# The Unofficial Guide — Project 1

> **How to use this template:**
> Complete each section *after* you've built and tested the corresponding part of your system.
> Do not write placeholder text — if a section isn't done yet, leave it blank and come back.
> Every section below is required for submission. One-liners will not receive full credit.

---

## Domain

<!-- What topic or category of knowledge does your system cover?
     Why is this knowledge valuable, and why is it hard to find through official channels?
     Example: "Student reviews of CS professors at [university] — useful because official
     course descriptions don't reflect teaching style, exam difficulty, or workload." -->

**Topic:** Student experiences in UT Austin's online **Master of Science in Artificial Intelligence (MSAI)** — per-course reviews of real workload (hours/week), difficulty, grading structure, exam/project style, lecture quality, and how courses compare or should be sequenced.

**Why it's valuable and hard to find officially:** The official UT Austin / edX catalog lists course topics, credit hours, and prerequisites — but never what a course is actually *like*: the true hours/week, whether the autograder is brutal, whether you can skip the textbook, or which courses to pair. That lived experience is scattered across community hubs (e.g. [msaihub.com](https://msaihub.com)) and student forums, never in official channels, so a student planning their schedule has no single trustworthy source.

---

## Document Sources

<!-- List every source you collected documents from.
     Be specific: include URLs, subreddit names, forum thread titles, or file names.
     Aim for variety — sources that together cover different subtopics or perspectives. -->

All documents are student reviews collected from [msaihub.com](https://msaihub.com) (the community review hub for UT Austin's online MS programs), one course per file. Because the site is a JavaScript app with no public API, reviews were extracted from the rendered page via a browser-console scraper (see AI Usage below) and saved as plain `.txt`.

| # | Source (course) | Type | URL or file path |
|---|-----------------|------|-----------------|
| 1 | CS 391L — Machine Learning | Student reviews (msaihub.com) | documents/01_machine_learning.txt |
| 2 | CS 394D — Deep Learning | Student reviews (msaihub.com) | documents/02_deep_learning.txt |
| 3 | CS 388 — Natural Language Processing | Student reviews (msaihub.com) | documents/03_nlp.txt |
| 4 | CS 394R — Reinforcement Learning | Student reviews (msaihub.com) | documents/04_reinforcement_learning.txt |
| 5 | CS 395T — Optimization | Student reviews (msaihub.com) | documents/05_optimization.txt |
| 6 | CS 395T — Online Learning and Optimization | Student reviews (msaihub.com) | documents/06_online_learning_optimization.txt |
| 7 | CS 388U — Planning, Search, and Reasoning Under Uncertainty | Student reviews (msaihub.com) | documents/07_planning_search_reasoning.txt |
| 8 | CS 389L — Automated Logical Reasoning | Student reviews (msaihub.com) | documents/08_automated_logical_reasoning.txt |
| 9 | CS 400T — Case Studies in Machine Learning | Student reviews (msaihub.com) | documents/09_case_studies_ml.txt |
| 10 | ICD10 — AI in Healthcare | Student reviews (msaihub.com) | documents/10_ai_in_healthcare.txt |

These 10 courses span foundational ML, deep learning, NLP, reinforcement learning, optimization, search/reasoning, formal logic, applied case studies, and an interdisciplinary healthcare course — different subtopics so retrieval must distinguish genuinely different material. Note #5 and #6 share the course code **CS 395T**, a deliberate disambiguation challenge. Total: **328 reviews** across the 10 files.

---

## Chunking Strategy

<!-- Describe your chunking approach with enough specificity that someone else could reproduce it.
     Include:
     - Chunk size (characters or tokens) and why that size fits your documents
     - Overlap size and why (or why not) you used overlap
     - Any preprocessing you did before chunking (e.g., stripping HTML, removing headers)
     - What your final chunk count was across all documents -->

**Chunk size:** Variable but capped at **256 tokens**. One chunk = one complete student review; any review longer than the cap is sub-split into ≤256-token windows. Average chunk is ~210 tokens.

**Overlap:** **~40 tokens**, applied *only* when a long review is sub-split. There is **no overlap between separate reviews** — bleeding one student's opinion into another's chunk would pollute retrieval (mixing a "loved it" review into a "hated it" one).

**Why these choices fit your documents:** Reviews are self-contained opinions, so splitting on the review boundary (`---`) keeps each opinion intact and avoids cross-review contamination — fixed-size windowing would cut opinions in half and merge unrelated students. The 256-token cap matches the embedding model's real input limit: `all-MiniLM-L6-v2` truncates at 256 tokens, so a larger chunk would be silently cut off when embedded. Each chunk is also **prefixed with its course name (+ review title)** so that even a sub-split fragment keeps its identity — essential for source attribution and for telling the two CS 395T courses apart. Preprocessing strips the scaffold `#` comment lines and normalizes whitespace; the documents had no HTML/nav boilerplate because they were collected from the rendered DOM, not raw HTML.

**Final chunk count:** **760** across the 10 course files (from 328 reviews; 432 of those chunks are sub-split parts of reviews longer than the 256-token window). Within the project's 50–2,000 guidance.

---

## Embedding Model

<!-- Name the embedding model you used and explain your choice.
     Then answer: if you were deploying this system for real users and cost wasn't a constraint,
     what tradeoffs would you weigh in choosing a different model?
     Consider: context length limits, multilingual support, accuracy on domain-specific text,
     latency, and local vs. API-hosted. -->

**Model used:** `all-MiniLM-L6-v2` via `sentence-transformers`, with embeddings stored in **ChromaDB** using **cosine distance** (`hnsw:space: cosine`). It runs locally (no API key, no rate limits), produces 384-dim vectors, and performs well on short English text. Retrieval returns the **top-5** chunks per query; on the evaluation questions, correct-course chunks came back with cosine distances of ~0.32–0.46.

**Production tradeoff reflection:** If cost weren't a constraint and this served real students, I'd weigh:
- **Context length:** MiniLM truncates at ~256 tokens, which forced me to sub-split long reviews. A model like OpenAI `text-embedding-3-large` (8191 tokens) or Voyage AI would embed a full long review in one piece, preserving cross-paragraph context.
- **Domain accuracy:** MiniLM is general-purpose and can under-weight CS/ML jargon and course codes (this showed up as the CS 395T near-twin leaking into retrieval). A larger or domain-adapted model would separate similar courses more reliably.
- **Multilingual:** Not needed here (reviews are English), so a multilingual model would add cost for no benefit.
- **Latency vs. local:** MiniLM is local and instant; an API model adds network latency and an outage/dependency risk in exchange for higher accuracy. For this small corpus the local model is the right call; at scale I'd benchmark the accuracy gain against per-query cost.

---

## Grounded Generation

<!-- Explain how your system enforces grounding — how does it prevent the LLM from answering
     beyond the retrieved documents?
     Describe both your system prompt (what instruction you gave the model) and any structural
     choices (e.g., how you formatted the context, whether you filtered low-relevance chunks).
     Do not just say "I told it to use the documents" — show the actual instruction or explain
     the mechanism. -->

**System prompt grounding instruction:**

**How source attribution is surfaced in the response:**

---

## Evaluation Report

<!-- Run your 5 test questions from planning.md through your system and record the results.
     Be honest — a partially accurate or inaccurate result that you explain well is more
     valuable than a suspiciously perfect result. -->

| # | Question | Expected answer | System response (summarized) | Retrieval quality | Response accuracy |
|---|----------|-----------------|------------------------------|-------------------|-------------------|
| 1 | | | | | |
| 2 | | | | | |
| 3 | | | | | |
| 4 | | | | | |
| 5 | | | | | |

**Retrieval quality:** Relevant / Partially relevant / Off-target  
**Response accuracy:** Accurate / Partially accurate / Inaccurate

---

## Failure Case Analysis

<!-- Identify at least one question where retrieval or generation did not work as expected.
     Write a specific explanation of *why* it failed, tied to a part of the pipeline.

     "The answer was wrong" is not an explanation.

     "The relevant information was split across a chunk boundary, so retrieval returned
     only half the context — the model didn't have enough to answer correctly" is an explanation.

     "The embedding model treated the professor's nickname as out-of-vocabulary and returned
     results from an unrelated review" is an explanation. -->

**Question that failed:**

**What the system returned:**

**Root cause (tied to a specific pipeline stage):**

**What you would change to fix it:**

---

## Spec Reflection

<!-- Reflect on how planning.md shaped your implementation.
     Answer both questions with at least 2–3 sentences each. -->

**One way the spec helped you during implementation:**

**One way your implementation diverged from the spec, and why:**

---

## AI Usage

<!-- Describe at least 2 specific instances where you used an AI tool during this project.
     For each: what did you give the AI as input, what did it produce, and what did you
     change, override, or direct differently?

     "I used Claude to help me code" is not sufficient.
     "I gave Claude my Chunking Strategy section from planning.md and asked it to implement
     chunk_text(). It returned a function using a fixed character split. I overrode the
     chunk size from 500 to 200 because my documents are short reviews, not long guides." -->

**Instance 1 — Document collection (scraper)**

- *What I gave the AI:* the source site (msaihub.com — a JavaScript Angular app with no public API), the structure of a review (overall/difficulty/professor/lecture/textbook ratings, workload hrs/week, body text, date), and my problem: I needed reviews for ~10 courses but copying every field by hand was unworkable.
- *What it produced:* it traced the site to the open-source MSCSHub repo, read the review component's DOM template to learn the exact markup, then wrote a browser-console scraper ([scripts/scrape_msaihub_reviews.js](scripts/scrape_msaihub_reviews.js)) that auto-paginates through a filtered course's reviews and outputs them already formatted with `---` separators.
- *What I changed or overrode:* _[fill in your own words — e.g., on Firefox the `copy()` clipboard write failed on large outputs (pink console text), so I copied from the logged output / re-ran per course; I selected the 10 courses and re-ran the AI in Healthcare scrape after it didn't save the first time.]_

**Instance 2 — Chunking implementation**

- *What I gave the AI:* my Chunking Strategy section from `planning.md` (one chunk per review, split on `---`, attach course metadata) and the requirement that it work with `all-MiniLM-L6-v2`.
- *What it produced:* `load_documents()` and `chunk_text()` in [ingest.py](ingest.py), plus an inspection script that prints chunk counts and 5 sample chunks.
- *What I changed or overrode:* the cap was lowered from the planned ~500 tokens to **256** after confirming `all-MiniLM-L6-v2` truncates at 256 (a 500-token chunk would be silently cut); I also kept the course+title prefix on every sub-split part so long-review fragments stay attributable. _[Adjust to reflect any further changes you made.]_
