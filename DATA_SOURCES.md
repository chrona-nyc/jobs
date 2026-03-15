# Additional Data Sources

Datasets that can enrich this project, ranked by usefulness.

---

## Tier 1: High value, easy to join

### O*NET (Occupational Information Network)
- **What:** The most detailed occupation database in the US. Covers 923 occupations with granular data on **tasks, skills, abilities, work activities, tools & technology, and work context** for each job.
- **Why it matters:** Instead of scoring an entire job, we could score **individual tasks** within a job. A nurse might be 2/10 on "Administer medications" but 8/10 on "Document patient records." Much richer picture.
- **Format:** Free CSV/Excel download, updated quarterly
- **Join key:** SOC codes (already in `occupations.csv`) — O*NET provides a [direct crosswalk to OOH occupations](https://www.onetcenter.org/crosswalks.html)
- **Download:** [onetcenter.org/database.html](https://www.onetcenter.org/database.html)
- **Key files to grab:**
  - `Task Statements.csv` — Every task for every occupation
  - `Skills.csv` — Skill importance and level ratings
  - `Abilities.csv` — Required abilities (cognitive, physical, psychomotor)
  - `Work Activities.csv` — Generalized and detailed work activities
  - `Work Context.csv` — Physical conditions, social interactions, etc.
  - `Technology Skills.csv` — Software and tools used on the job

### BLS Occupational Employment and Wage Statistics (OEWS)
- **What:** Employment counts and wage distributions by **state and metro area** for ~830 occupations.
- **Why it matters:** Enables the **geographic heat map** — "Austin's workforce has avg exposure 6.8, Bakersfield is 3.2." Shows which local economies are most AI-exposed.
- **Format:** Excel/CSV, published annually (May reference period)
- **Join key:** SOC codes
- **Download:** [bls.gov/oes](https://www.bls.gov/oes/)
- **Key files:**
  - National estimates by occupation
  - State estimates by occupation
  - MSA (metro area) estimates by occupation

---

## Tier 2: High value, moderate effort

### Frey & Osborne (2013) — "The Future of Employment"
- **What:** The famous Oxford study that scored 702 occupations for "probability of computerization" — predicted *before* the current AI wave.
- **Why it matters:** Historical comparison. "In 2013 they said software developers were safe. In 2025, AI says 8/10." The delta tells the story of how AI surprised everyone.
- **Format:** PDF appendix with scores; community-extracted CSVs exist on GitHub
- **Join key:** SOC codes (2010 vintage — may need crosswalk to 2018 SOC)
- **Paper:** [The Future of Employment (Frey & Osborne, 2013)](https://www.sciencedirect.com/science/article/abs/pii/S0040162516302244)
- **Note:** The scores were based on expert workshops with 70 ML researchers. Methodology has been [critiqued](https://melbourneinstitute.unimelb.edu.au/__data/assets/pdf_file/0005/3197111/wp2019n10.pdf) but the dataset remains the most-cited automation risk benchmark.

### World Economic Forum — Future of Jobs Report 2025
- **What:** Survey of 1,000+ global employers covering 14M workers across 55 economies. Identifies fastest-growing and fastest-declining roles, top skills in demand, and employer AI adoption timelines.
- **Why it matters:** Employer perspective complements our AI-scored analysis. "Here's what AI *could* do" vs "here's what employers *plan* to do."
- **Format:** PDF report with data tables; interactive data explorer available
- **Download:** [weforum.org/publications/the-future-of-jobs-report-2025](https://www.weforum.org/publications/the-future-of-jobs-report-2025/)
- **Key data points:**
  - Top 10 growing and declining roles
  - Skills outlook (what employers want in 5 years)
  - Technology adoption timelines by industry
  - Workforce strategy trends (upskilling, automation, augmentation)

---

## Tier 3: Interesting for specific features

### BLS Current Population Survey (CPS) — Demographics
- **What:** Demographic data (age, race, gender) by occupation
- **Why it matters:** "AI exposure disproportionately affects [demographic]" — important equity story
- **Download:** [bls.gov/cps](https://www.bls.gov/cps/)

### Census Bureau — American Community Survey (ACS)
- **What:** Detailed occupation data by geography, commuting patterns, remote work rates
- **Why it matters:** Remote work rate is a strong proxy for "digital job" — could validate our scoring
- **Download:** [data.census.gov](https://data.census.gov/)

### LinkedIn Economic Graph / Indeed Hiring Lab
- **What:** Real-time job posting data, skills in demand, hiring trends
- **Why it matters:** Forward-looking signal — are employers *already* hiring fewer of certain roles?
- **Caveat:** Not freely downloadable as raw data; available via reports and limited APIs

### OECD Programme for International Assessment of Adult Competencies (PIAAC)
- **What:** Measures adult skills (literacy, numeracy, problem-solving) across 40+ countries
- **Why it matters:** Could compare AI exposure internationally
- **Download:** [oecd.org/skills/piaac](https://www.oecd.org/en/about/programmes/piaac.html)

---

## How to join these datasets

All of these use some variant of the **Standard Occupational Classification (SOC)** system. Our `occupations.csv` already has SOC codes. The join process:

```
Our data (342 occupations, SOC codes)
    ↕ SOC code join
O*NET (923 occupations, O*NET-SOC codes)
    ↕ O*NET provides crosswalk files
BLS OEWS (830 occupations, SOC codes)
    ↕ SOC codes
Frey & Osborne (702 occupations, 2010 SOC codes — need crosswalk)
```

O*NET provides [crosswalk files](https://www.onetcenter.org/crosswalks.html) that map between different SOC vintages and classification systems, making this join straightforward.
