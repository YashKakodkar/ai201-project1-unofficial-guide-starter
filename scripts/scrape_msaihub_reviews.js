/*
 * msaihub.com review scraper — run in the BROWSER CONSOLE (DevTools).
 * ---------------------------------------------------------------------------
 * Why a console script? msaihub is an Angular app whose Firestore backend is
 * locked (allow read: if false) + App Check, so there is no public API to curl.
 * But the reviews ARE rendered in your browser, so we read them from the DOM.
 *
 * USAGE
 *   1. Go to msaihub.com -> Reviews.
 *   2. In "Filter by Class Name", select ONE course (e.g. CS 391L Machine Learning).
 *   3. Open DevTools console (Cmd+Option+J on Chrome/Mac) and paste this whole file.
 *   4. It auto-clicks "Next" through every page, extracts all reviews, and copies
 *      the formatted text to your clipboard.
 *   5. Paste into the matching documents/NN_course.txt file. Repeat per course.
 *
 * Output format per review (matches our chunking convention; reviews split on ---):
 *   Title: ...
 *   Term: CS 391L - Fall 2023
 *   Posted: 1/2/2024 ...
 *   Rating: 5
 *   Difficulty: 4
 *   Textbook: 2
 *   Lectures: 4
 *   Professor: 5
 *   Piazza: 3
 *   Workload: 15 hours per week
 *
 *   Review:
 *   <body text>
 */
(async function scrapeMSAIHub() {
  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

  const findBtn = (label) =>
    [...document.querySelectorAll('button')].find(
      (b) => b.textContent.trim().toLowerCase() === label.toLowerCase()
    );

  function scrapePage() {
    const blocks = [];
    document.querySelectorAll('.review-container mat-card').forEach((card) => {
      // Only real review cards have a .rating-grid (skips the filter card).
      if (!card.querySelector('.rating-grid')) return;

      const title = card.querySelector('mat-card-title')?.innerText.trim() || '';
      const subs = card.querySelectorAll('mat-card-subtitle');
      const term = subs[0]?.innerText.trim() || '';
      const date = subs[1]?.innerText.trim() || '';

      // Label spans only (skip the spans that hold the star-rating visual).
      const raw = [...card.querySelectorAll('.rating-grid > span')]
        .filter((s) => !s.querySelector('app-star-rating'))
        .map((s) => s.innerText.trim())
        .filter(Boolean);

      // "Workload:" and its value render as two spans -> merge them.
      const fields = [];
      for (let i = 0; i < raw.length; i++) {
        if (raw[i] === 'Workload:' && raw[i + 1]) {
          fields.push('Workload: ' + raw[i + 1]);
          i++;
        } else {
          fields.push(raw[i]);
        }
      }

      const body = card.querySelector('mat-card-content p')?.innerText.trim() || '';

      blocks.push(
        `Title: ${title}\nTerm: ${term}\nPosted: ${date}\n${fields.join('\n')}\n\nReview:\n${body}`
      );
    });
    return blocks;
  }

  const seen = new Set();
  const all = [];
  let guard = 0;

  while (guard++ < 300) {
    for (const b of scrapePage()) {
      const key = b.slice(0, 250); // dedupe on the leading slice
      if (!seen.has(key)) {
        seen.add(key);
        all.push(b);
      }
    }
    const next = findBtn('Next');
    if (!next || next.disabled) break;
    next.click();
    await sleep(1000); // wait for the next page to fetch + render; raise if your connection is slow
  }

  const text = all.join('\n\n---\n\n');
  try {
    copy(text); // DevTools console helper -> clipboard
    console.log(`✅ Scraped ${all.length} reviews — copied to clipboard. Paste into the course file.`);
  } catch (e) {
    console.log(`Scraped ${all.length} reviews. copy() unavailable; the full text is logged below:`);
  }
  console.log(text);
  return `Done: ${all.length} reviews.`;
})();
