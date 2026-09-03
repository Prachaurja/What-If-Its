# Swipe — Product & System Blueprint

Version 1.0 · September 2026 · Author: Prach

## What Swipe is

Swipe is a writing-integrity platform. A user uploads a document; Swipe returns it as a marked-up manuscript showing (1) passages that match known sources — a private repository, an open corpus, and the live web — and (2) sentences that show signs of AI generation or AI paraphrasing, with a calibrated confidence band rather than a bare number.

It is modelled on Turnitin's two engines but built to be honest about uncertainty, cheap to run, and usable by three kinds of customer.

## Who it is for

| Segment | Organisation type | What they check | Why they pay |
|---|---|---|---|
| Universities & schools | `institution` | student submissions, per course | academic integrity, LMS integration, private repository of past submissions |
| Publishers & content teams | `publisher` | articles, marketing copy, ghostwritten pieces | originality before publishing, AI-content policy compliance, web coverage |
| Individual writers & students | `individual` | their own drafts | self-check before submitting, avoid accidental plagiarism |

Serving all three means one product with one organisation model that has three flavours. The differences are: who can see what (roles), which repositories a check compares against, what the report is called, and pricing. The engines are identical.

## Design principles

1. **The document is the interface.** Reports render as the manuscript itself, annotated — not a dashboard of gauges.
2. **Say "unsure" out loud.** Short texts are not scored. Detector disagreement widens the confidence band. Every AI result carries a plain-language caveat.
3. **Every submission makes the product better.** Submissions join the org's private repository; fetched web pages join the shared cache.
4. **One box first.** Everything runs from a single `docker compose up` on one VPS. Scale later by moving the GPU worker and the fingerprint store off-box — nothing else changes.

## What is in this blueprint

| Doc | Contents |
|---|---|
| 01 | System architecture and request flows |
| 02 | Repository file tree |
| 03 | Database schema |
| 04 | API specification |
| 05 | Detection engines: similarity, web fallback, AI ensemble |
| 06 | Frontend: screens, components, wireframes |
| 07 | Deployment on one VPS |
| 08 | Roadmap and milestones |
