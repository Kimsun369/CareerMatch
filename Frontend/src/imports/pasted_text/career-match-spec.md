# CRITICAL — REAL API DATA ONLY — DO NOT USE MOCK DATA

This is NOT a static Figma prototype.

Build CareerMatch as a **real, API-driven Next.js application**.

The application must be designed and coded so that job listings, recommendations, user preferences, saved jobs, and job details come from the **Django REST API**.

## ABSOLUTELY DO NOT DECLARE JOB DATA IN THE FRONTEND

Do NOT create any hardcoded or mock job dataset such as:

```typescript
const jobs = [
  {
    id: 1,
    title: "Software Engineer",
    organization: "Example Company",
    location: "Phnom Penh",
    match_score: 92
  }
];
```

Do NOT create:

```typescript
const mockJobs = [...]
```

Do NOT create:

```typescript
const recommendedJobs = [...]
```

Do NOT create fake JSON files containing jobs.

Do NOT create placeholder job objects that are rendered as if they came from the backend.

Do NOT hardcode:

* Job titles
* Organizations
* Job descriptions
* Locations
* Job types
* Sectors
* Skills
* Closing dates
* Match scores
* Match reasons
* Source URLs
* Saved-job states
* Job counts

The frontend must receive these values from API responses.

If you need to demonstrate the UI while the API is unavailable, use **loading, empty, or error states**. Do not create fake jobs.

---

# REAL DATA ARCHITECTURE

The required architecture is:

**ReliefWeb API**

↓

**Django ingestion process**

↓

**Django normalization / validation**

↓

**PostgreSQL**

↓

**Django recommendation engine**

↓

**Django REST API**

↓

**Next.js frontend**

The Next.js frontend must NOT directly fetch ReliefWeb as the primary application data source.

The Next.js frontend communicates with Django.

Django communicates with ReliefWeb.

The browser must never be responsible for scraping websites.

---

# NEXT.JS FRONTEND REQUIREMENT

Build this specifically as:

**Next.js + React + TypeScript + Tailwind CSS**

Use a proper component-based architecture.

Use the Next.js App Router where appropriate.

The frontend must have a centralized API service.

For example:

```typescript
const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL;
```

The API base URL must come from an environment variable.

Do NOT scatter URLs throughout components.

Do NOT hardcode:

```typescript
fetch("http://localhost:8000/api/jobs/")
```

inside UI components.

Instead, create a centralized API layer.

For example:

```typescript
api.getJobs()
api.getRecommendations()
api.getJob(id)
api.getSavedJobs()
api.saveJob(id)
api.unsaveJob(id)
api.getProfile()
api.updatePreferences(data)
```

The exact implementation can vary, but the principle is mandatory:

**UI components must consume API services, not contain hardcoded application data.**

---

# REQUIRED API-DRIVEN DATA FLOW

The Home page must work conceptually like this:

```text
User opens Home
        ↓
Next.js requests Django API
        ↓
Django retrieves the user's preferences
        ↓
Django queries available jobs
        ↓
Django calculates recommendation scores
        ↓
Django returns ranked jobs
        ↓
Next.js renders the API response
```

The frontend must NOT calculate recommendation scores.

The frontend must NOT create recommendation results.

The frontend must NOT randomly assign match percentages.

The backend is responsible for recommendation logic.

---

# RECOMMENDATION API

The frontend should be prepared to consume an endpoint similar to:

```text
GET /api/jobs/recommendations/
```

The response should contain real jobs from the backend.

A conceptual response could look like:

```json
{
  "results": [
    {
      "id": 123,
      "title": "...",
      "organization": "...",
      "location": "...",
      "job_type": "...",
      "sector": "...",
      "description": "...",
      "skills": [],
      "closing_date": "...",
      "source": "ReliefWeb",
      "source_url": "...",
      "match_score": 87,
      "match_reason": "..."
    }
  ]
}
```

The values above are ONLY an example of the API schema.

DO NOT put these example values into the application.

The actual values must come from Django.

---

# IMPORTANT DISTINCTION: API SCHEMA VS API DATA

You may define TypeScript interfaces.

For example:

```typescript
interface Job {
  id: string | number;
  title: string;
  organization: string;
  location: string | null;
  job_type: string | null;
  sector: string | null;
  description: string;
  skills: string[];
  closing_date: string | null;
  source: string;
  source_url: string;
  match_score?: number;
  match_reason?: string;
  is_saved?: boolean;
}
```

This is allowed.

The interface defines the **shape of data**.

However, do NOT create an actual static object containing fake job information.

Correct:

```typescript
interface Job {
  id: string | number;
  title: string;
  ...
}
```

Incorrect:

```typescript
const jobs: Job[] = [
  {
    id: 1,
    title: "Software Engineer",
    ...
  }
];
```

The application must obtain the actual objects through the Django API.

---

# REAL-TIME / FRESH DATA BEHAVIOR

CareerMatch uses real job listings ingested from ReliefWeb.

The frontend should always request the current data available from the Django backend.

Do not design the application around a permanently embedded dataset.

When the user opens the recommendation page, fetch the current recommendation response from the backend according to the application's caching strategy.

When the user searches or filters jobs, request the appropriate current data from Django.

When the user opens a job, retrieve its current details from Django.

When the user saves or unsaves a job, update the backend.

When the user changes preferences, persist them through Django and request updated recommendations.

The frontend should never assume that yesterday's job list is still current.

---

# NO FAKE FALLBACK

This is especially important.

If the Django API is unavailable:

DO NOT:

* Replace the jobs with fake jobs
* Show example jobs
* Show hardcoded recommendations
* Show fake match scores
* Pretend the API succeeded

Instead show:

**Unable to load jobs**

with:

**Try again**

The application must honestly communicate the API state.

If there are no jobs:

Show a genuine empty state.

If the API is loading:

Show skeleton loaders.

If the API fails:

Show an error state.

If the API succeeds:

Render the returned data.

There should be exactly one source of truth:

**The backend API.**

---

# ONBOARDING MUST ALSO BE DYNAMIC

Onboarding consists of exactly three main questions.

Do NOT ask for the user's name.

Do NOT add a name field.

Do NOT add unnecessary personal information.

### Question 1

**What are you looking for?**

Options:

* Full-time job
* Part-time / Flexible
* Internship
* Freelance / Gig

No emojis.

Use professional icons.

### Question 2

**What field are you interested in?**

Options:

* Hotel & Tourism
* Tech & IT
* Marketing & Sales
* Health & NGO
* Finance & Banking
* Education & Teaching
* Construction & Engineering
* Logistics & Supply Chain
* Any / Show me everything

No emojis.

### Question 3

**Where would you like to work?**

Options:

* Cambodia
* Abroad

If Abroad is selected:

Reveal a searchable country selector.

Do not show the country selector before Abroad is selected.

The country list should be sourced from a proper dataset or backend-supported list rather than being limited to a few manually written countries.

The three-question structure remains:

**Job Type → Field → Location**

Abroad → Country is a conditional part of Location, not a fourth question.

---

# ONBOARDING DATA FLOW

When onboarding is completed:

```text
User selections
      ↓
Next.js
      ↓
Django REST API
      ↓
PostgreSQL
      ↓
Saved user preferences
      ↓
Recommendation endpoint
      ↓
Real ranked jobs
```

Do not merely store the selections in React state.

Do not merely store them in localStorage.

The final preferences must be persisted through Django.

---

# SEARCH MUST USE REAL DATA

Search must not filter a fake frontend array.

Incorrect:

```typescript
jobs.filter(job =>
  job.title.includes(search)
)
```

if `jobs` is a hardcoded mock dataset.

Instead, design the search system to request the backend.

Conceptually:

```text
GET /api/jobs/?search=developer
```

The exact endpoint and query parameter names can be changed to match the Django implementation.

The frontend should make changing these endpoint details easy.

---

# FILTERS MUST USE REAL DATA

Filters such as:

* Job type
* Field
* Location

must operate on real backend data.

Do not create a fake collection just to demonstrate filtering.

The backend should remain the source of truth.

The frontend sends the selected filters to Django.

Django returns matching jobs.

Next.js renders the response.

---

# SAVED JOBS MUST BE REAL

Saved Jobs must come from the backend.

Do not declare:

```typescript
const savedJobs = [...]
```

Do not make the bookmark state permanently static.

Use API operations such as:

```text
GET /api/jobs/saved/
POST /api/jobs/{id}/save/
DELETE /api/jobs/{id}/save/
```

The exact endpoints can be adjusted.

When the user saves a job:

**Next.js → Django → PostgreSQL**

When the user opens Saved Jobs:

**Next.js → Django → PostgreSQL → Next.js**

---

# JOB DETAILS MUST BE REAL

When a user opens a job:

Do not display a static details page.

Use the actual job ID.

Conceptually:

```text
/jobs/123
```

↓

```text
GET /api/jobs/123/
```

↓

Django returns current job data.

↓

Next.js renders it.

The following must come from the API:

* Title
* Organization
* Location
* Job type
* Field
* Description
* Skills
* Closing date
* Source
* Source URL
* Match score
* Match explanation

If a field is missing, display an appropriate missing-data state.

Never invent it.

---

# PROFILE MUST BE API-DRIVEN

Profile preferences must come from Django.

Conceptually:

```text
GET /api/profile/
```

The user should see their actual saved preferences.

When they change them:

```text
PUT /api/profile/preferences/
```

After successful update, the application should request updated recommendations.

Do not pretend that the update succeeded if the API request fails.

---

# TELEGRAM INTEGRATION

CareerMatch is a Telegram Mini App.

Use the Telegram WebApp SDK for Telegram user identity.

The frontend should have a dedicated authentication/Telegram integration layer.

Do not place Telegram initialization logic randomly inside visual components.

The Telegram identity should eventually be verified by Django.

For local browser testing, a development authentication abstraction may be provided.

However, the real Telegram architecture must remain clear.

Do not replace Telegram identity with a fake login form.

---

# RELIEFWEB IS THE REAL EXTERNAL SOURCE

The project proposal defines ReliefWeb as the primary real-world source.

The frontend should NOT contain ReliefWeb job data.

The frontend should NOT directly depend on the ReliefWeb response format.

Django is responsible for converting ReliefWeb's response into the internal CareerMatch Job format.

Therefore:

**ReliefWeb raw JSON**

↓

**Django normalization**

↓

**CareerMatch Job**

↓

**PostgreSQL**

↓

**Django REST API**

↓

**Next.js**

This separation is mandatory.

---

# API FAILURE STATES ARE PART OF THE PRODUCT

Design the actual UI for:

### Loading

Skeleton cards.

### API Error

"Unable to load jobs."

Retry button.

### Empty Recommendations

"No matching jobs found."

Suggestion to change preferences or browse all jobs.

### Empty Saved Jobs

"No saved jobs yet."

### Job Not Found

"The job is no longer available."

### Missing Data

"Location not specified"

"Closing date not provided"

Do not replace missing information with fake values.

---

# VISUAL DATA MUST NEVER BE FABRICATED

Even statistics and counts must be dynamic.

Do not create decorative statistics such as:

"1,248 Jobs"

"92% Match"

"342 Saved"

unless they come from an actual API response.

Do not create fake "latest jobs" timestamps.

Do not create fake organization logos.

Do not create fake recommendation explanations.

Every displayed piece of application data must have a legitimate source:

**API response, authenticated user state, or UI state.**

If there is no legitimate source, don't display the value.

---

# DESIGN THE EMPTY STATE FIRST

Because the application depends on a real API, the design must remain professional even when there is no data.

The interface should not rely on fake content to look good.

A high-quality CareerMatch design must look intentional with:

* Loading state
* Empty state
* Error state
* Real data state

This is a real application, not a static presentation.

---

# STRICT ACCEPTANCE TEST

The generated application should be considered incorrect if it does any of the following:

1. Contains a hardcoded `jobs` array.
2. Contains `mockJobs`.
3. Contains fake recommendation data.
4. Contains fake match percentages.
5. Contains fake saved jobs.
6. Displays fake job information when the API fails.
7. Uses localStorage as the main persistent data source.
8. Calls ReliefWeb directly from React instead of Django.
9. Calculates recommendation scores in the frontend.
10. Generates fake job listings.
11. Uses placeholder company names as actual application data.
12. Hardcodes job descriptions.
13. Hardcodes source URLs.
14. Hardcodes recommendation reasons.
15. Treats example JSON as actual data.
16. Creates a static job search experience.
17. Creates a static saved-jobs experience.

If the backend is not connected, the correct behavior is to show **loading/error/empty states**, not fabricated content.

---

# THE MOST IMPORTANT RULE

**DO NOT MAKE THE UI LOOK COMPLETE BY INVENTING DATA.**

A partially empty application connected to a real API is preferable to a beautiful application filled with fake data.

The goal is to create a frontend that can genuinely connect to the CareerMatch Django backend.

The application should be able to transition from:

**API unavailable → Error state**

to:

**API available → Real ReliefWeb-derived jobs**

without changing the UI architecture.

The visual design should therefore be built around dynamic data from the beginning.

---

# FINAL ARCHITECTURE

The completed frontend must represent this architecture:

```text
                    RELIEFWEB
                        │
                        ▼
              Django Ingestion
                        │
                        ▼
             Normalize / Validate
                        │
                        ▼
                   PostgreSQL
                        │
                        ▼
             Recommendation Engine
                        │
                        ▼
                Django REST API
                        │
                        ▼
             Next.js / React / TS
                        │
          ┌─────────────┼─────────────┐
          ▼             ▼             ▼
      Web Browser    Telegram      Mobile
                     Mini App
```

Build the frontend around this architecture.

Do not simulate this architecture with mock data.

Do not create a fake backend inside the frontend.

Do not use static job objects to make the screens look populated.

The final result must be a **real API-driven CareerMatch frontend**, with the Django REST API acting as the source of truth for jobs, recommendations, preferences, saved jobs, and job details.
