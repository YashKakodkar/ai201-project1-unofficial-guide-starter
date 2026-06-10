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

**System prompt grounding instruction:** The system prompt (in [query.py](query.py)) tells the model it is "The Unofficial Guide" and enforces these rules: *"Use ONLY the context. Do not use outside knowledge and do not invent facts. If the context does not contain enough information to answer, reply with exactly: 'I don't have enough information on that.' When reviews disagree, surface the range of opinion instead of picking one."* Structural choices that reinforce grounding: (1) the **only** content in the user message is the retrieved excerpts + the question — the model is given nothing else to draw on; (2) each excerpt is labeled with its course and source file so the model references courses by name; (3) temperature is set low (0.2) to keep the model close to the source text. Verified: out-of-domain questions (e.g. "What's the weather in Austin?") return the refusal sentence rather than a fabricated answer.

**How source attribution is surfaced in the response:** Attribution is added **programmatically, not left to the LLM.** After generation, `ask()` collects the unique `(course, source_file)` pairs from the chunks that were actually retrieved and returns them as a `sources` list, which the Gradio UI shows in a "Retrieved from" box. This guarantees the citation reflects the real retrieved evidence regardless of what the model writes. Sources are suppressed when the answer is the "I don't have enough information" response, so a refusal is never falsely attributed to a document.

---

## Evaluation Report

<!-- Run your 5 test questions from planning.md through your system and record the results.
     Be honest — a partially accurate or inaccurate result that you explain well is more
     valuable than a suspiciously perfect result. -->

All five were run through the full system via [evaluate.py](evaluate.py). Retrieval cosine distances are shown where relevant.

| # | Question | Expected answer | System response (summarized) | Retrieval quality | Response accuracy |
|---|----------|-----------------|------------------------------|-------------------|-------------------|
| 1 | Hours/week for CS 391L Machine Learning? | Cluster at 10–15 hrs/wk (15 most common; range ~5–30) | Listed scattered figures from 5 reviews (20 early, 15, 8 late, 5 end, week-by-week 18.5/6.25/9.5) incl. 15, but did not state the typical 10–15 | Relevant (5/5 CS 391L, dist 0.35–0.43) | Partially accurate |
| 2 | More difficult: Deep Learning or NLP, and why? | Roughly comparable; NLP marginally higher by avg rating (~4.7 vs ~4.4/7) | Stated NLP is **definitively** more difficult, citing a "hardest course I've taken" review; overstated the near-tie | Partially relevant (mixed DL/NLP, dist 0.47–0.50 — weakest of all) | Partially accurate |
| 3 | How to prepare before Reinforcement Learning? | Take DL/NLP first (PyTorch); strong Python + Probability | Strong on Probability (conditional expectation, Blitzstein chapters) but **missed** the "take DL/NLP first for PyTorch" advice | Relevant (5/5 CS 394R, dist 0.35–0.37) | Partially accurate |
| 4 | How do CS 395T Optimization vs Online Learning and Optimization differ? | ~Equal workload; Optimization = convex-opt foundations; OLO builds on it, two halves | Correctly distinguished the two same-coded courses: OLO is "two courses in one" (optimization + online learning halves) with per-half workload figures; cited both source files | Relevant (5/5 CS 395T, correctly split across both, dist 0.37–0.41) | Accurate |
| 5 | Grading in Automated Logical Reasoning? | Quizzes ~50%, programming assignments ~30%, homework ~20%; no traditional exams | Correctly said quizzes + programming assignments (no traditional exams) and captured the harsh grading, but **missed** the exact 50/30/20 weights | Relevant (5/5 CS 389L, dist 0.32–0.37 — best) | Partially accurate |

**Overall retrieval quality:** Relevant on 4/5 (Q2 partially relevant). The course-prefix on each chunk kept retrieval on the correct course in every case, including the CS 395T disambiguation (Q4).
**Overall response accuracy:** 1 Accurate, 4 Partially accurate. The partial cases share one cause — they ask for a corpus-wide aggregate (a mode, an average, a weight breakdown) that no single 5-chunk sample can represent (see Failure Case Analysis).

---

## Failure Case Analysis

<!-- Identify at least one question where retrieval or generation did not work as expected.
     Write a specific explanation of *why* it failed, tied to a part of the pipeline.

     "The answer was wrong" is not an explanation.

     "The relevant information was split across a chunk boundary, so retrieval returned
     only half the context — the model didn't have enough to answer correctly" is an explanation.

     "The embedding model treated the professor's nickname as out-of-vocabulary and returned
     results from an unrelated review" is an explanation. -->

**Question that failed:** Q2 — "Which is more difficult: CS 394D Deep Learning or CS 388 Natural Language Processing, and why?"

**What the system returned:** A confident verdict that **NLP is more difficult than Deep Learning**, backed by a review calling NLP "the hardest course I've taken" and reviews calling DL "manageable / easier now that it's split." The corpus-wide reality is that the two are **nearly tied** — average difficulty ratings are 4.4 (DL) vs 4.7 (NLP) out of 7. So the system overstated a marginal difference as a clear gap. (Notably, an earlier run with slightly different query wording flipped the verdict to "DL is harder" — the answer is unstable.)

**Root cause (tied to a specific pipeline stage): retrieval, not generation.** Difficulty is a *corpus-wide statistic* spread across ~70 DL and ~33 NLP reviews. Top-k retrieval returns only 5 chunks, selected by semantic similarity to the query — a small, non-representative sample that skews toward the most strongly-worded reviews (which is why distances here were the highest of all questions, ~0.47–0.50: no chunk was a clean match for a comparison query). The LLM then faithfully reported that biased sample. The generation step is correctly grounded in what it was given; the failure is that **semantic retrieval *samples* the corpus, it does not *aggregate* it** — so a couple of vivid reviews outweigh the silent majority.

**What you would change to fix it:** (1) For comparison/superlative questions, retrieve a balanced set — e.g. top-k *per course* via metadata filtering — so both sides are represented rather than whichever course has the most quotable reviews. (2) Store the structured ratings (difficulty, workload) as queryable numeric metadata and **compute the average directly** instead of asking the LLM to infer it from prose — aggregation questions need an aggregation step, not just nearest-neighbor text search. (3) Raise k for comparison intents so the sample better approximates the full distribution.

---

## Spec Reflection

<!-- Reflect on how planning.md shaped your implementation.
     Answer both questions with at least 2–3 sentences each. -->

**One way the spec helped you during implementation:** Committing to the chunking strategy in `planning.md` *before* coding — one chunk per review, split on the `---` boundary, with the course attached as metadata — directly shaped `chunk_text()` and prevented a whole class of bugs. Because the decision was made up front, retrieval returned whole, self-contained opinions (not half-sentences), and every chunk carried its course, which is exactly what made source attribution and the CS 395T disambiguation work in practice. Writing the 5 evaluation questions before any code also gave a concrete target to test retrieval against at each milestone, so I caught the aggregation weakness during evaluation instead of after submitting.

**One way your implementation diverged from the spec, and why:** The spec set the chunk-size cap at ~500 tokens. During Milestone 3 I lowered it to **256** after confirming that `all-MiniLM-L6-v2` truncates its input at 256 tokens — a 500-token chunk would have been silently cut off at embedding time, losing the tail of long reviews without any error. I also added a course + review-title **prefix to every sub-split part** (not in the original plan) so that fragments of a long review stay attributable to the right course. I updated `planning.md`'s Chunking Strategy to record the 256 cap and the reasoning, rather than leaving the spec and code disagreeing.

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
- *What I changed or overrode:* I picked the 10 courses myself to spread across the catalog (foundational ML, deep learning, NLP, RL, optimization, logic, applied healthcare) instead of just grabbing the most-reviewed ones, so retrieval would have to tell genuinely different topics apart. When I ran the scraper in Firefox, the `copy()` clipboard call silently failed on the larger courses (the console output came back pink and nothing landed on the clipboard), so for those I copied the reviews out of the logged console output instead; the small AI in Healthcare course copied cleanly. I also missed saving the AI in Healthcare file on the first pass and had to re-paste and save it.

**Instance 2 — Chunking implementation**

- *What I gave the AI:* my Chunking Strategy section from `planning.md` (one chunk per review, split on `---`, attach course metadata) and the requirement that it work with `all-MiniLM-L6-v2`.
- *What it produced:* `load_documents()` and `chunk_text()` in [ingest.py](ingest.py), plus an inspection script that prints chunk counts and 5 sample chunks.
- *What I changed or overrode:* I directed it to use **one chunk per review** (splitting on the `---` boundary) rather than fixed-size character chunks, because each review is a self-contained opinion and fixed-size splitting would cut opinions in half. I had the cap lowered from the planned ~500 tokens to **256** after we confirmed `all-MiniLM-L6-v2` truncates at 256 (a 500-token chunk would be silently cut off at embedding time), and I kept a course + review-title prefix on every sub-split part so fragments of long reviews stay attributable to the right course.
