FINAL YEAR PROJECT PROPOSAL
CareerMatch
A Telegram Mini App for Personalized Job Recommendations Powered by ReliefWeb
Field Detail
Student Seng Kimsun
Project Title CareerMatch
Proposed Technology Stack Next.js, Django, PostgreSQL
Delivery Platform Telegram Mini App (web-based, browser-compatible)
Deployment Mode Local demonstration (no public hosting required)
1. Introduction
Job seekers, particularly young graduates and first-time job seekers, face a fragmented job search experience:
relevant openings are scattered across multiple channels (job boards, Telegram channels, NGO/humanitarian
postings, company pages), and there is no single, low-friction way to receive job listings matched to a person's
actual preferences. CareerMatch addresses this by combining a lightweight, chat-native interface (a Telegram
Mini App) with a structured recommendation backend that filters and ranks job listings against a user's stated
preferences for job type, sector, and location.
This proposal describes a scaled-down, locally demonstrable version of CareerMatch suitable for a final year
project: a single real-world data source, a conventional three-tier web architecture (Next.js frontend, Django
REST API, PostgreSQL database), and a transparent, explainable recommendation algorithm.
2. Problem Statement
• Job listings relevant to a given job seeker are dispersed across many sources with no unified, structured
access point.
• Most job platforms require the user to manually search and filter, rather than proactively surfacing
relevant opportunities.
• There is no lightweight, no-install way for users to receive and browse recommendations from within a
tool they already use daily (Telegram).
• Existing job-matching systems are often opaque; users cannot see why a job was recommended to
them.
3. Objectives
• To design and implement a structured data pipeline that ingests real job listings from a live external
source into a relational database.
• To build a REST API (Django) that exposes endpoints for user preference management and job
recommendation retrieval.
• To implement a transparent recommendation/matching algorithm that scores jobs against user
preferences, with an optional AI-assisted ranking and explanation layer.
• To build a Telegram Mini App frontend (Next.js) that allows a user to set preferences, view ranked
recommendations, view job details, and bookmark jobs.
• To evaluate the system's matching quality and usability through a local demonstration and manual test
cases.
4. Scope of the Project
Given the academic scope and timeline, the project is deliberately bounded as follows:
• Single data source: job listings will be ingested from ReliefWeb (reliefweb.int), a public humanitarian
job-and-vacancy aggregator, via its public REST API. The project uses ReliefWeb's global jobs feed (not
restricted to a single country) to ensure a sufficiently large and varied dataset for demonstrating the
recommendation logic.
• A small set of manually curated "seed" listings may be added to ensure coverage across all job
categories used in the app's onboarding flow (e.g. hospitality, construction), since ReliefWeb's postings skew
toward development/NGO-sector roles. This will be explicitly disclosed as sample data in the final report.
• The system will run and be demonstrated locally (localhost) rather than being deployed to a public
server; a tunneling tool (e.g. ngrok) may be used only to expose the app temporarily during a live Telegram
demonstration.
• The AI-assisted ranking component, if implemented, will use a free-tier LLM API (e.g. Groq) rather
than a paid service, or will be replaced by a fully rule-based scoring function if time is limited — both are
treated as valid, defensible implementations of the recommendation objective.
• Continuous, always-on ingestion from many sources is explicitly out of scope; the project instead
demonstrates a working, repeatable ingestion pipeline against one real source, run on demand or on a schedule
during the evaluation period.
5. Data Source: ReliefWeb
ReliefWeb is a public service provided by the UN Office for the Coordination of Humanitarian Affairs (OCHA)
that aggregates job vacancies worldwide. It exposes a public, authentication-free REST API that returns
structured JSON data including job title, organisation, location, job type, closing date, and a link to the full
posting — all fields that map directly onto CareerMatch's job schema.
The project uses the following registered endpoint pattern for ingestion:
https://api.reliefweb.int/v2/jobs?appname=KhmerGigs-TelegramMiniApp-
X7K29&preset=latest&profile=full&limit=20
The ingestion command calls this endpoint with an app-specific appname (required by ReliefWeb's usage
policy), preset=latest to retrieve the most recently published vacancies, and profile=full to receive complete job
records rather than summaries. The dataset is deliberately not filtered by country, giving a larger and more
varied pool of real listings to demonstrate the matching logic across all onboarding categories (job type, sector,
location). A country filter (filter[field]=country&filter[value]=<Country>) can be added later as a simple,
optional parameter if a narrower or more geographically focused dataset is preferred for a future iteration.
Using ReliefWeb as the sole real-world source provides:
• Genuinely live, regularly updated data (not static/mock data), satisfying the requirement for real-world
evaluation.
• A clean, documented, structured API response, avoiding the fragility of HTML scraping.
• No authentication or paid tier requirement, keeping the project free to run and demonstrate.
6. Proposed System Architecture
Layer Technology Responsibility
Frontend Next.js (React, TypeScript, Tailwind
CSS)
Telegram Mini App UI: onboarding, job feed, job
details, saved jobs, profile
Backend API Django + Django REST Framework User preference storage, job ingestion command,
recommendation/scoring logic, REST endpoints
Database PostgreSQL Persistent storage for users, jobs, and saved-job
interactions
Data Ingestion Django management command
(Python)
Fetches and normalizes listings from the ReliefWeb
API into the Jobs table
AI Layer (optional) Groq API (free tier) or rule-based
Python function
Ranks candidate jobs and generates a short, human-
readable match explanation
Data flow: the Telegram user opens the Mini App → Next.js retrieves the Telegram user identity via the
Telegram WebApp SDK → the frontend calls the Django REST API to save/load preferences and fetch
recommendations → Django queries PostgreSQL for candidate jobs, applies scoring (and optional AI re-
ranking), and returns a ranked list → the frontend renders job cards, job details, and supports saving jobs, all
persisted back to PostgreSQL.
7. Recommendation Approach
Jobs are scored against a user's selected job type, sector/field, and location. Missing or unknown fields in a
given listing are treated as neutral (contributing zero score) rather than disqualifying the listing, since real-world
job data is frequently incomplete. A baseline rule-based scoring function will be implemented first; if time
permits, a free-tier LLM (Groq) will be used to re-rank the top candidate jobs and generate a one-sentence, user-
friendly explanation for each recommendation (e.g. "Good match for Tech & IT roles in Phnom Penh"). In both
cases, the underlying job data itself is never generated or altered by the AI layer — only the ranking and
explanation are AI-assisted, ensuring recommendations remain grounded in real listings.
8. Methodology
• Requirements analysis and schema design for Users, Jobs, and SavedJobs tables.
• Implementation of the Django data models, REST API endpoints, and the ReliefWeb ingestion
command.
• Implementation of the Next.js frontend and Telegram WebApp integration.
• Implementation and iterative tuning of the scoring/ranking logic.
• Local integration testing: onboarding flow, preference persistence, recommendation retrieval, job
details, save/unsave.
• Preparation of a local demonstration (with optional temporary HTTPS tunnel for live Telegram
testing).
9. Tentative Timeline
Week(s) Milestone
1–2 Requirements finalization, schema design, Django project setup
3–4 ReliefWeb ingestion command + Jobs/Users models and migrations
5–6 REST API endpoints (preferences, recommendations, job details, saved jobs)
7–8 Next.js frontend integration with the new backend
9 Scoring/ranking logic implementation and tuning
10 Optional: Groq-based re-ranking and explanation generation
11 Integration testing and bug fixing
12 Final demonstration preparation and report writing
10. Expected Outcome
A working, locally runnable Telegram Mini App that ingests real job data from ReliefWeb, stores it in
PostgreSQL via a Django backend, and presents users with personalized, explainable job recommendations
based on their stated preferences — demonstrating a complete, real-world-grounded recommendation pipeline
within an academically appropriate scope.
11. Limitations and Future Work
• Single data source: future work could extend ingestion to additional job boards and Telegram channels
for broader coverage.
• Local-only demonstration: a production deployment would require hosting, scheduled ingestion, and
monitoring, which are out of scope here.
• Rule-based/lightweight AI ranking: a production system could employ more sophisticated ML-based
ranking trained on real user interaction data over time.
12. References
ReliefWeb. (n.d.). ReliefWeb Jobs API. Retrieved from https://reliefweb.int/jobs
Telegram. (n.d.). Telegram Mini Apps Documentation. Retrieved from https://core.telegram.org/bots/webapps