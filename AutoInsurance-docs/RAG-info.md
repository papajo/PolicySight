Yes — an **FDE absolutely may write custom Python scripts**, especially when the product needs to work against messy real-world customer data.

An FDE is not usually just a “meeting person.” A strong FDE is often a hybrid of:

**software engineer + solutions engineer + product detective + domain problem-solver**

For a PolicySight-style auto insurance AI tool, an FDE might write Python scripts for things like:

### 1. Parsing policy documents

```python
# Example task:
# Extract policy number, effective date, vehicles, drivers, deductibles, and limits
# from uploaded PDF text.
```

They may build scripts that read OCR text from PDFs and pull out fields like:

* policy number
* named insured
* policy period
* liability limits
* collision deductible
* comprehensive deductible
* listed vehicles
* listed drivers

---

### 2. Cleaning bad OCR

Insurance docs are often ugly: scanned, blurry, rotated, or full of OCR mistakes.

An FDE might write a Python script to detect patterns like:

```text
Bodly Injury Liabllty $25,O00/$5O,O00
```

and normalize it to something more likely:

```text
Bodily Injury Liability $25,000/$50,000
```

But the script should also mark the value as **low confidence**, not silently “fix” it as fact.

---

### 3. Building quick internal tools

They may write small utilities like:

```text
compare_policy_versions.py
extract_declarations_page.py
find_exclusions.py
endorsement_diff_checker.py
coverage_limit_validator.py
claim_scenario_tester.py
```

These scripts may never become polished product features, but they help the team understand what the customer actually needs.

---

### 4. Creating test data

For PolicySight, an FDE could generate fake but realistic policy documents or claim scenarios.

Example:

```python
test_case = {
    "claim_date": "2026-03-03",
    "policy_start": "2026-03-10",
    "expected_result": "claim_date_before_policy_period"
}
```

That helps test whether the AI catches obvious coverage problems before answering.

---

### 5. Writing evaluation scripts

This is a big one.

An FDE might write Python evals that check whether the AI answer:

* cited the correct policy section
* extracted the right deductible
* avoided unsupported certainty
* detected missing declarations pages
* flagged excluded drivers
* handled endorsements correctly
* escalated risky cases

Example:

```python
def test_missing_declarations_page(agent_response):
    assert "declarations page" in agent_response.lower()
    assert "cannot determine" in agent_response.lower()
    assert "$25,000" not in agent_response
```

This prevents the AI from sounding smart while being wrong.

---

### 6. Integrating customer systems

If the carrier has claim data in one system, policies in another, and PDFs in S3 or Google Drive, the FDE may write Python glue code:

```text
Pull policy PDF → extract text → call AI model → validate citations → push result to claim review UI
```

This is classic FDE work.

---

## What an FDE usually should not do

They should not only write one-off messy scripts forever with no structure.

A good FDE may start with a quick Python script, but then turn repeated patterns into:

* reusable modules
* APIs
* agent tools
* backend services
* product requirements
* test suites
* documentation

So the rough script becomes a real product capability.

## Simple answer

Yes. In fact, for an AI insurance product, a good FDE would likely write a lot of custom Python scripts for **document parsing, OCR cleanup, policy extraction, test-case generation, evals, integrations, and debugging customer-specific workflows**.

Yes — a good **Forward Deployed Engineer working on an AI product should know about RAG**.

**RAG** means **Retrieval-Augmented Generation**.

In simple words:

> Before the AI answers, it first looks up the relevant documents, then uses those documents to generate the answer.

For **PolicySight**, RAG is extremely important because the AI should not answer insurance questions from memory. It should answer from the **actual uploaded policy**.

## Simple example

User asks:

> “Do I have rental car coverage?”

A weak AI might answer from general insurance knowledge:

> “Many auto policies include rental reimbursement.”

That is dangerous.

A RAG-based AI should do this:

1. Search the uploaded policy.
2. Find the declarations page.
3. Find rental reimbursement language.
4. Check endorsements.
5. Answer only from those retrieved sections.
6. Cite the exact policy text.

Better answer:

> “Your policy appears to include rental reimbursement coverage with a limit of $40 per day / $1,200 maximum. This is shown on the declarations page under Optional Coverages. I also checked the endorsements and did not find one removing this coverage.”

## What an FDE should understand about RAG

They do not always need to be a deep research scientist, but they should understand the practical engineering parts:

### Document ingestion

How PDFs, scans, Word docs, policy booklets, declarations pages, and endorsements get loaded into the system.

For PolicySight:

> Upload policy PDF → extract text → split into sections → store searchable chunks.

### Chunking

How documents are broken into pieces.

Bad chunking can ruin the answer.

Example problem:

> One chunk contains the start of an exclusion, but the next chunk contains the exception to that exclusion.

If the AI only sees the first chunk, it may wrongly say:

> “Not covered.”

### Embeddings

How text is converted into searchable numeric form.

The FDE does not need to reinvent embeddings, but they should know that embeddings help the system find relevant policy sections even when the user phrases the question differently.

User asks:

> “Am I covered if my buddy drove my car?”

The policy may say:

> “Any person using your covered auto with permission.”

RAG should connect those two ideas.

### Retrieval quality

This is huge.

The FDE should test whether the system retrieves the **right sections**, not just any insurance-sounding section.

Example:

User asks:

> “What is my uninsured motorist limit?”

Bad retrieval pulls:

> bodily injury liability

Good retrieval pulls:

> uninsured/underinsured motorist coverage section and declarations page.

### Citation accuracy

For PolicySight, RAG is only useful if the citations are real.

The AI should not say:

> “According to your policy…”

unless it can point to the exact section.

### Hallucination control

RAG reduces hallucination, but it does not eliminate it.

A good FDE should test cases where the AI retrieves partial, outdated, conflicting, or irrelevant policy text.

Example:

The policy booklet says rental coverage exists generally, but the declarations page does not list rental coverage.

The agent should say:

> “The policy explains rental reimbursement as an available coverage, but I do not see it selected on your declarations page.”

## For PolicySight, RAG is almost mandatory

Without RAG, the product becomes a generic insurance chatbot.

With RAG, it becomes a policy-specific assistant.

The difference is:

| Without RAG                    | With RAG                     |
| ------------------------------ | ---------------------------- |
| Answers from general knowledge | Answers from uploaded policy |
| More likely to hallucinate     | More grounded                |
| Weak citations                 | Exact citations              |
| May miss endorsements          | Can retrieve endorsements    |
| Sounds confident               | Can show evidence            |

## What prompts can you give an AI Agent about RAG?

```text
Design a RAG pipeline for PolicySight that can ingest auto insurance policy PDFs, extract text, split documents into meaningful sections, retrieve the most relevant policy language for a user’s claim question, and generate an answer with exact citations.
```

```text
Evaluate the current RAG retrieval quality for PolicySight. Test whether questions about deductibles, exclusions, endorsements, policy periods, listed vehicles, and permissive drivers retrieve the correct policy sections.
```

```text
Create RAG failure test cases for auto insurance policies. Include examples where the agent retrieves the wrong section, misses an endorsement, cites the base policy instead of the declarations page, or answers when the necessary policy text is missing.
```

```text
Improve the PolicySight RAG system so that it prioritizes declarations pages, endorsements, exclusions, and policy-specific definitions before generating claim-related answers.
```

## Simple answer

Yes. An FDE working on an AI insurance product should know RAG well enough to build, test, debug, and improve it.

For **PolicySight**, RAG is not just a fancy AI feature. It is the core mechanism that keeps the agent grounded in the actual policy instead of making confident guesses.

Yes. What people usually mean by a “RAG DB” is a **vector database** or **vector store**: a place where your app stores document chunks + embeddings, then retrieves the most relevant chunks before the LLM answers.

For your **PolicySight** use case, these are the best open-source/local options to download and test.

## Best starting options

| Tool         | Best for                                    | Why it fits PolicySight                                                                                                                                                                                                 |
| ------------ | ------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Chroma**   | Easiest local Python RAG testing            | Very simple for prototypes. Stores documents, metadata, embeddings, and supports retrieval, metadata filtering, dense/sparse/hybrid search. Chroma is open-source and can run locally. ([Chroma Docs][1])               |
| **LanceDB**  | Local embedded DB, no server needed         | Good when you want a local folder-based vector DB inside a Python/TypeScript app. LanceDB’s quickstart supports `pip install lancedb` and connecting to a local filesystem path. ([LanceDB][2])                         |
| **Qdrant**   | Local Docker service / more production-like | Good if you want a real vector DB API service. Qdrant’s local quickstart uses Docker, Python client, collections, vector search, and payload filters. ([Qdrant][3])                                                     |
| **pgvector** | If you already like Postgres/Supabase       | Excellent when you want vectors stored with normal relational data: users, claims, policies, vehicles, etc. It supports exact/approx nearest-neighbor search and multiple distance types inside Postgres. ([GitHub][4]) |

## Heavier but useful options

| Tool           | Best for                              | Notes                                                                                                                                                                                                                                                               |
| -------------- | ------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Weaviate**   | Full RAG platform-style testing       | Open-source vector DB with local Docker quickstart. Their local guide explicitly covers collections, vector search, and RAG with a generative model. They recommend a modern computer with at least 8 GB RAM, preferably 16 GB+. ([Weaviate Documentation][5])      |
| **Milvus**     | Large-scale vector search             | Strong for big-scale workloads, but heavier than Chroma/Qdrant for a first PolicySight prototype. Milvus provides a standalone Docker install path. ([Milvus][6])                                                                                                   |
| **OpenSearch** | Hybrid keyword + vector search        | Useful if you want classic search plus vector search. OpenSearch supports k-NN vector search and can act as a vector database. ([OpenSearch Documentation][7])                                                                                                      |
| **FAISS**      | Lightweight similarity search library | Not really a database. More like a fast vector search engine/library. Great for local experiments, but you must handle metadata, persistence, and app logic yourself. FAISS is built for efficient similarity search and clustering of dense vectors. ([GitHub][8]) |

## My recommendation for you

For **PolicySight**, start in this order:

**1. Chroma** — fastest way to prove the RAG idea.
Use it to test: “Can I upload policy text, chunk it, retrieve the right section, and cite it?”

**2. Qdrant** — once you want a proper local service.
Use it when your agent needs a clean API-backed vector DB.

**3. pgvector** — once you add real app data.
Use it when you want this kind of structure:

```text
users
policies
claims
vehicles
drivers
policy_chunks
embeddings
retrieval_logs
agent_answers
```

For an insurance product, **pgvector is especially attractive** because policy chunks and normal claim/customer metadata can live in the same Postgres system.

## Tiny practical setup idea

For a PolicySight RAG test, create a folder like this:

```text
policysight-rag-lab/
  data/
    sample_policy_01.txt
    sample_policy_02.txt
    sample_endorsement_01.txt
  scripts/
    ingest.py
    query.py
    eval_retrieval.py
  rag_db/
  tests/
    test_deductibles.py
    test_exclusions.py
    test_endorsements.py
```

Then test questions like:

```text
What is my collision deductible?
```

```text
Is John Smith covered if he drove my car?
```

```text
Does this policy include rental reimbursement?
```

```text
Was the claim date inside the policy period?
```

The real test is not “does the AI answer nicely?” The real test is:

```text
Did the RAG DB retrieve the exact correct policy section before the AI answered?
```

## Simple agent prompt you can use

```text
Compare Chroma, Qdrant, LanceDB, and pgvector for a local RAG prototype of PolicySight.

Recommend one for v1.

Then create:
1. a local setup plan,
2. an ingestion script plan,
3. a document chunking strategy,
4. metadata fields for insurance policy chunks,
5. retrieval test cases,
6. failure cases where the wrong section is retrieved,
7. acceptance criteria for citation accuracy.
```

For your current stage, I’d use **Chroma first**, then move to **Qdrant or pgvector** once the PolicySight flow starts feeling real.

[1]: https://docs.trychroma.com/docs/overview/introduction "Introduction - Chroma Docs"
[2]: https://docs.lancedb.com/quickstart "Quickstart - LanceDB"
[3]: https://qdrant.tech/documentation/quickstart/ "Local Quickstart - Qdrant"
[4]: https://github.com/pgvector/pgvector "GitHub - pgvector/pgvector: Open-source vector similarity search for Postgres · GitHub"
[5]: https://docs.weaviate.io/weaviate/quickstart/local "Quickstart: Locally hosted with Docker | Weaviate Documentation"
[6]: https://milvus.io/docs/install_standalone-docker.md?utm_source=chatgpt.com "Run Milvus in Docker (Linux)"
[7]: https://docs.opensearch.org/latest/vector-search/?utm_source=chatgpt.com "Vector search - OpenSearch Documentation"
[8]: https://github.com/facebookresearch/faiss?utm_source=chatgpt.com "facebookresearch/faiss: A library for efficient similarity ..."

In this context, **FDEs** means **Forward Deployed Engineers**: engineers who work close to the customer/product problem, not just in the backend codebase. For PolicySight, they would help turn messy insurance documents into reliable AI answers.

The selected phrase has two big ideas:

## 1. Chunking pipelines

A **chunking pipeline** is the process that takes a long document and cuts it into smaller pieces the AI can actually use.

Insurance policies are huge. An AI agent cannot always read the entire policy at once, so the system needs to break the policy into useful chunks.

Bad chunking:

> “The policy covers liability limits of…”
> “...except when the vehicle is used for rideshare…”

Those two pieces got separated, so the AI may miss the exception.

Good chunking:

> “Liability coverage applies up to $100,000 per person and $300,000 per accident. This coverage does not apply when the vehicle is used for commercial rideshare activity unless the rideshare endorsement is active.”

That chunk keeps the rule and the exception together.

For PolicySight, chunking matters for things like:

* policy declarations
* exclusions
* deductibles
* endorsements
* liability limits
* uninsured motorist coverage
* rental reimbursement
* claim conditions
* state-specific requirements

An FDE should make sure the chunking pipeline does not randomly split important legal/insurance meaning.

## 2. Context harness engineering

A **context harness** is the system that decides **what information gets handed to the AI before it answers**.

Think of it like packing a briefcase for the AI.

The AI should not just get the user’s question. It should get the right supporting context:

User asks:

> “Am I covered if my car was stolen from my driveway?”

A weak context harness gives the AI:

> “Auto policy document, page 1.”

A strong context harness gives the AI:

> “Relevant sections: comprehensive coverage, theft coverage, deductible, exclusions, policy declarations, vehicle coverage status, claim notice conditions.”

Then the AI can answer much more accurately.

In simple words:

**Chunking pipeline = how you cut up the documents.**
**Context harness = how you choose and arrange the right pieces for the AI.**

## What should FDEs do with them?

FDEs should make these systems practical, testable, and customer-specific.

They should not just say, “We use RAG.” They should ask:

> “Is the AI actually retrieving the right policy language for the customer’s question?”

For PolicySight, an FDE should probably work on things like:

### 1. Design better chunks

Instead of blindly splitting every 500 words, chunk by insurance meaning.

Example chunks:

* “Collision Coverage”
* “Comprehensive Coverage”
* “Rental Reimbursement”
* “Exclusions”
* “Endorsements”
* “Duties After Loss”
* “Policy Limits”
* “Named Insured and Vehicles”

This makes retrieval cleaner.

### 2. Preserve metadata

Each chunk should carry labels, such as:

```text
document_type: auto_policy
section: comprehensive_coverage
state: NJ
carrier: Progressive
policy_page: 14
coverage_type: theft
effective_date: 2026-01-01
```

That helps the AI know what it is reading.

Example:

A user asks about theft coverage. The system should prioritize chunks tagged:

```text
coverage_type: comprehensive
claim_type: theft
```

Not random chunks about bodily injury liability.

### 3. Build retrieval tests

FDEs should create test questions and expected retrieved chunks.

Example test:

```text
Question:
“Does this policy cover a rental car after an accident?”

Expected chunks:
- Rental Reimbursement section
- Collision coverage section
- Loss of use limits
- Exclusions for rental vehicles
```

If the AI retrieves only the declarations page, the pipeline failed.

### 4. Handle conflicting policy language

Insurance docs often have base policy text plus endorsements.

Example:

Base policy says:

> “Rideshare activity is excluded.”

Endorsement says:

> “Rideshare coverage applies during Period 1.”

A good context harness must include both, and ideally rank the endorsement higher when relevant.

The FDE should make sure the AI understands:

> “The endorsement modifies the base policy.”

### 5. Prevent hallucinated answers

Without the right context, the AI may guess.

Bad AI answer:

> “Yes, theft is usually covered.”

Better AI answer:

> “The policy appears to cover theft under Comprehensive Coverage, but only if Comprehensive is listed for this vehicle on the declarations page. The deductible shown is $500.”

That answer is grounded in actual policy text.

### 6. Build claim-specific context packs

Different claim types need different context.

For example:

**Rear-end accident**

Relevant context:

* liability coverage
* collision coverage
* deductible
* police report duties
* repair estimate process

**Stolen vehicle**

Relevant context:

* comprehensive coverage
* theft exclusions
* deductible
* claim reporting deadline
* title/keys/cooperation duties

**Hit-and-run**

Relevant context:

* collision
* uninsured motorist property damage
* deductible waiver
* state-specific rules

The FDE can help define these “context recipes.”

## Practical example

User asks:

> “My car was damaged in a flood. Am I covered?”

A weak system may retrieve a random chunk about “property damage liability” and answer incorrectly.

A strong chunking/context system should retrieve:

```text
1. Comprehensive Coverage section
2. Water/flood damage language
3. Vehicle declarations page showing whether Comprehensive applies
4. Deductible amount
5. Any exclusions for intentional damage, wear and tear, or mechanical failure
```

Then the AI answer could be:

> “Flood damage is usually handled under Comprehensive Coverage, not Collision. In this policy, Comprehensive is listed for the 2022 Honda Accord with a $500 deductible. Based on the retrieved policy text, flood damage appears covered unless an exclusion applies.”

## Bottom line

For an FDE, **chunking pipelines** and **context harness engineering** are about making the AI read the right policy parts at the right time.

In plain English:

> The FDE’s job is to make sure the AI does not just sound smart — it actually looks at the correct insurance language before answering.

