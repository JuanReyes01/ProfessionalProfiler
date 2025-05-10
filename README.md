# ProfessionalProfiler

---

## Objective

Extract the professional degrees (type and field) of U.S. opinion-article authors who have a Wikipedia page.

---

## Dataset

### 1. Overview

- **Source:** ProQuest USNewsStream (Universidad de los Andes license)
- **Period:** 1980 – November 2024
- **Sample size:** 98 729 unique authors
- **Selection:** Opinion columnists from the top-circulating U.S. dailies per Statista 2023:
  - Star Tribune
  - Chicago Tribune
  - New York Post
  - Tampa Bay Times
  - The New York Times
  - Newsday
  - The Boston Globe
  - The Washington Post
  - The Wall Street Journal
  - USA Today
  - Los Angeles Times

> **Note:** Investigate Statista’s methodology to identify any potential selection biases.

### 2. Schema & Preprocessing

#### 2.1 Named-Entity Recognition (NER)

- Apply an NER model to extract author names from unstructured text blocks, e.g.:
  > “This article was written by [person1] from [newspaper1], and [person2] from [newspaper2]…”
- Separate the extracted `author` column from the main articles table.
- Normalize many-to-many relations via three tables.

#### 2.2 Database Structure

- **Articles**

  ```json
  {
    "article_id":    <int>,
    "full_text":     <string>,
    "title":         <string>,
    "publication":   <string>,
    "publish_date":  <date>,
    "editorial":     <string>,
    "source_type":   <string>
  }
  ```

- **Authors**

  ```json
  {
    "author_id": <int>,
    "name":      <string>
  }
  ```

- **AuthorArticle** (join table)

  ```json
  {
    "article_id": <int>,
    "author_id":  <int>
  }
  ```

All provenance and relational queries can be handled via SQL across these tables.

---

## Architecture

### 1. Scraping

1. **Wikipedia API**

   - Up to **3 retries** with exponential backoff on failures.

2. **Agent-Driven Pipeline**

   - Modular steps for validation, extraction, chunking, and evaluation.

---

### 2. Data Validation (Pydantic)

```python
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field

class FieldEnum(str, Enum):
    ASSOCIATE = "Associate's"
    BACHELOR  = "Bachelor's"
    MASTER    = "Master's"
    DOCTOR    = "Doctor's"
    UNKNOWN   = "Unknown"
    NONE      = "No degree"

class Study(BaseModel):
    degree_type:  FieldEnum        = Field(..., description="Academic degree type")
    degree_field: Optional[List[str]] = Field(default_factory=list, description="Field(s) of study")

class ProfessionalProfiler(BaseModel):
    studies: List[Study] = Field(default_factory=list, description="List of academic degrees")
```

---

### 3. Prompt Engineering

**Goal:** Identify and categorize academic degrees from a Wikipedia text snippet.

**Steps:**

1. Scan for keywords (e.g., B.A., M.A., Bachelor, Master, Doctor).
2. Map each mention to a `FieldEnum`.
3. Extract associated study fields (optional).
4. Detect incomplete degrees (“dropped out”, “did not graduate”) and ignore.
5. If no completed degree is found, return a single entry with `FieldEnum.NONE`.

**Output schema (exact JSON):**

```json
[
  {
    "studies": [
      {
        "degree_type": "<FieldEnum>",
        "degree_field": ["<string>", ...]
      }
    ]
  }
]
```

**Examples:**

> **Q1:**
> “He attended the Tree of Life Synagogue as a youth.\[7] He received his Bachelor of Arts from Harvard College in 1980. After graduating, he worked as a sports reporter for the Associated Press and as a production assistant for feature films.\[1]\[8]
> He received his Juris Doctor from the University of California at Berkeley in 1986, where he was editor-in-chief of the California Law Review and graduated Order of the Coif.\[1]\[5]\[9]”

```json
[
  {
    "studies": [
      {
        "degree_type": "BACHELOR",
        "degree_field": []
      },
      {
        "degree_type": "DOCTOR",
        "degree_field": ["Juris Doctor"]
      }
    ]
  }
]
```

> **Q2:**
> “After attending University City High School in St. Louis, Missouri, Moyn earned his A.B. degree from Washington University in St. Louis in history and French literature (1994). He continued his education, earning a Ph.D. from the University of California at Berkeley (2000) and his J.D. from Harvard Law School (2001).\[2]”

```json
[
  {
    "studies": [
      {
        "degree_type": "BACHELOR",
        "degree_field": ["History", "French literature"]
      },
      {
        "degree_type": "DOCTOR",
        "degree_field": ["Ph.D"]
      },
      {
        "degree_type": "DOCTOR",
        "degree_field": ["J.D"]
      }
    ]
  }
]
```

> **Q3:**
> “Foster was born in July 1976.\[7]\[1] His father, Lawrence Foster, was a franchise developer for Dunkin' Donuts.\[1] He grew up in Plymouth, Massachusetts,\[7] and spent summers at his grandparents' cottage on Peaks Island, Maine.\[1] Foster graduated from Falmouth Academy in 1994.\[8] He enrolled at the College of William & Mary, where he studied physics and film studies before dropping out his senior year.\[7] He learned HTML and moved to Washington D.C., where he worked for government agencies.\[7]”

```json
[
  {
    "studies": [
      {
        "degree_type": "NONE",
        "degree_field": []
      }
    ]
  }
]
```

---

### 4. Test Dataset

- **100 manually-annotated individuals** (JSON format):

  ```json
  {
    "Name": "Harry Litman",
    "Degrees": [
      { "degree_type": "Bachelor's", "degree_field": [] },
      { "degree_type": "Doctor's", "degree_field": ["J.D"] }
    ],
    "id": 1
  }
  ```

---

### 5. Chunking & Text Processing

- Extract relevant sections (infobox, education, early life, career).
- **Token limit:** 5 000 tokens per chunk
- **Overlap:** 25% to preserve context across boundaries.

---

### 6. Evaluation Metrics

- **Field-level**, **Type-level**, and **Full-match** (both type + field).
- **Baseline:** Regex-based extraction.

---

## Limitations

1. **Multiple same-type degrees:** Grouped under a single `degree_type`.
2. **Lack of detail:** No institution or year captured.
3. **Non-U.S. degrees:** Labeled as `UNKNOWN`.
4. **Ambiguous phrasing:** “Studied at Harvard” → `UNKNOWN`.

---

## LLM Configuration

```yaml
model: Deepseek-Chat
chunk_token_threshold: 5000
apply_chunking: true
overlap_rate: 0.25
extra_args:
  temperature: 0.0
```

---
