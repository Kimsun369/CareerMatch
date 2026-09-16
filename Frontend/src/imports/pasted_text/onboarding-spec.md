## ONBOARDING — 3 QUESTIONS ONLY

CareerMatch onboarding must contain **exactly three questions**.

Do **not** ask for the user's name, email address, age, phone number, resume, education, work experience, salary, or any other personal information during onboarding.

The purpose of onboarding is only to collect the three preference categories required by the CareerMatch recommendation system:

1. Job type
2. Field
3. Location

The onboarding should be extremely simple and friendly for non-technical users.

Use large, clear selection buttons/cards with one-tap interaction.

Do not use emojis anywhere in the onboarding interface.

Use professional icons where an icon improves recognition, but keep the interface clean and uncluttered.

---

### QUESTION 1 — What are you looking for?

Display the question:

**What are you looking for?**

Provide large visual selection cards/buttons:

* Full-time job
* Part-time / Flexible
* Internship
* Freelance / Gig

Each option should be easy to understand without technical knowledge.

Use appropriate professional icons if useful:

* Full-time → briefcase/work icon
* Part-time / Flexible → clock icon
* Internship → graduation-cap icon
* Freelance / Gig → tools/work icon

Do not use emoji characters.

The user should be able to select an option with one tap.

If the backend supports multiple job-type preferences, allow multiple selections. Otherwise, use the backend-supported selection behavior.

The selected state must be visually obvious.

Do not hardcode a fake recommendation based on the selection.

The selected preference must eventually be sent to the Django REST API and persisted for the user.

---

### QUESTION 2 — What field?

Display the question:

**What field are you interested in?**

Use simple language that ordinary job seekers can immediately understand.

Avoid technical industry terminology and complicated category names.

Display large selection cards/buttons for:

* Hotel & Tourism
* Tech & IT
* Marketing & Sales
* Health & NGO
* Finance & Banking
* Education & Teaching
* Construction & Engineering
* Logistics & Supply Chain
* Any / Show me everything

Use professional icons where appropriate.

Do not use emojis.

The user should be able to select their preferred field with one tap.

The **Any / Show me everything** option is important.

If the user selects **Any / Show me everything**, the system should not restrict recommendations based on field.

Do not treat "Any" as a literal job sector.

Instead, send an appropriate value/state to the backend indicating that the user has no field restriction.

The available categories should correspond to the categories supported by the CareerMatch backend.

The frontend should be structured so these options can later be supplied by the Django API rather than being tightly coupled to hardcoded frontend data.

However, the initial interface should use the categories defined above because they represent the intended CareerMatch onboarding experience.

The selected field must be persisted through the Django REST API.

---

### QUESTION 3 — Where?

Display the question:

**Where would you like to work?**

Initially show two simple choices:

* Cambodia
* Abroad

Do not display the country list immediately.

The interaction should be conditional.

#### If the user selects Cambodia:

The onboarding continues to completion.

The user's location preference should be stored as:

**Cambodia**

The recommendation system can then use this preference when ranking available jobs.

#### If the user selects Abroad:

Immediately reveal a second selection step asking:

**Which country?**

Display a searchable country selector.

The user should be able to search for and select a country.

For example:

* Japan
* Singapore
* Thailand
* South Korea
* Australia
* United States
* United Kingdom
* Canada
* Germany
* France

These examples should not be treated as the complete country list.

The country selector should use a proper country dataset or backend-supported country list rather than manually maintaining a small list of countries in the frontend.

The country selection should be searchable because the complete list of countries may be long.

Do not display every country as a huge wall of buttons.

Use a clean searchable selection interface.

After the user selects a country, show the selected country clearly and allow them to continue.

The selected location preference must be sent to the Django REST API and persisted.

---

## IMPORTANT ONBOARDING BEHAVIOR

The onboarding must remain exactly **three main questions**.

The Abroad → Country selection is a conditional sub-step of Question 3, not a fourth onboarding question.

The flow should therefore be:

**Question 1**
What are you looking for?

↓

**Question 2**
What field are you interested in?

↓

**Question 3**
Where would you like to work?

↓

If **Cambodia** → Finish

If **Abroad** → Select country → Finish

↓

**Get my recommendations**

---

## PROGRESS INDICATOR

Show a simple progress indicator:

**1 of 3**

**2 of 3**

**3 of 3**

For the Abroad country selector, keep the user within Question 3.

Do not change the progress indicator to "4 of 4."

The interface should make it obvious that the country selection is part of the location question.

---

## ONBOARDING DESIGN

The onboarding should feel:

* Friendly
* Simple
* Fast
* Visual
* Professional
* Easy for first-time users
* Suitable for students and general job seekers

Avoid dense forms.

Avoid text-heavy explanations.

Avoid technical terminology.

Avoid unnecessary personal questions.

Avoid emojis.

Avoid dropdown-heavy interfaces except where a searchable country selector is appropriate.

Use large touch-friendly controls.

The user should be able to complete onboarding quickly without feeling like they are filling out a job application.

---

## DATA REQUIREMENT

Every onboarding selection must represent real application state.

Do not simply change the visual selected state.

The completed preferences must be submitted to the Django REST API.

Conceptually:

```typescript
interface UserPreferences {
  job_types: string[];
  fields: string[];
  location_type: "cambodia" | "abroad";
  country?: string;
}
```

The exact API schema can be adjusted to match the Django backend.

When onboarding is completed:

**Next.js → Django REST API → PostgreSQL**

The backend stores the user's preferences.

The frontend then requests recommendations from Django.

The frontend must not calculate the recommendation results itself.

---

## NO NAME COLLECTION

Do not include a name field anywhere in the onboarding.

Do not create:

* "What's your name?"
* "Tell us your name"
* "What should we call you?"
* Name input
* Profile-name setup

Telegram already provides user identity through the Telegram WebApp integration, while the CareerMatch recommendation algorithm only requires the user's job preferences.

The onboarding should therefore focus entirely on:

**Job Type → Field → Location**

Nothing else.

---

## AFTER ONBOARDING

After the user completes the three questions, transition to the CareerMatch recommendation screen.

The recommendation page should request real recommendation data from the Django REST API.

Do not show fake loading results or hardcoded example jobs.

The user should see actual jobs returned by the backend.

The backend is responsible for:

* Finding available jobs
* Comparing jobs against preferences
* Calculating match scores
* Ranking recommendations
* Optionally generating concise match explanations

The frontend only displays the returned results.

The core experience should be:

**Answer 3 simple questions → Get relevant jobs**
