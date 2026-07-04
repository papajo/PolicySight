A **Forward Deployed Engineer** is an engineer who works very close to real users, customers, operations teams, or business teams instead of only coding from behind a desk.

In simple words:

A normal engineer may ask, “What should I build?”

A **Forward Deployed Engineer** asks, “What problem is happening in the real world, and how do I build/fix something right there to solve it?”

## Key concepts

### 1. “Forward deployed” means close to the front line

“Forward deployed” originally sounds military: someone is placed near where the action is happening.

In software, it means the engineer works close to the customer, business process, or real workflow.

**Example:**

For an auto insurance AI tool, the engineer may sit with claims adjusters and watch how they read policies, review accident photos, check coverage, and decide next steps.

They are not just guessing from a requirements document.

---

### 2. They translate messy real-world problems into software

Customers often explain problems in vague ways:

> “This policy is confusing.”
>
> “Claims take too long.”
>
> “The AI answer doesn’t match the policy language.”

The Forward Deployed Engineer turns that into concrete technical work.

**Example:**

A claims team says:

> “The AI keeps missing exclusions.”

The engineer figures out:

> “We need a better policy section parser, citation system, exclusion detector, and confidence score.”

---

### 3. They build fast, practical solutions

A Forward Deployed Engineer usually does not wait months to design the “perfect” system. They build useful fixes quickly, test them with users, and improve.

**Example:**

Instead of building a huge insurance platform first, they may quickly create:

> “Upload auto policy → extract declarations page → identify coverage limits → explain deductible → cite exact policy section.”

Then they test it with real claim examples.

---

### 4. They understand both tech and the business domain

They need to know coding, APIs, data, AI models, and debugging.

But they also need to understand the customer’s world.

For insurance, that means understanding things like:

* policy declarations
* deductibles
* exclusions
* liability limits
* comprehensive vs collision
* claims workflows
* state-specific coverage rules
* carrier-specific policy language

**Example:**

A regular engineer may say:

> “The model extracted `$500` from the document.”

A Forward Deployed Engineer asks:

> “Is that the collision deductible, comprehensive deductible, rental reimbursement limit, or towing limit?”

That distinction matters.

---

### 5. They often customize the product for specific customers

They may adapt the product to fit one company’s workflow, documents, data formats, or internal systems.

**Example:**

Carrier A stores policies as PDFs.

Carrier B stores policy sections in a database.

Carrier C has scanned documents with bad OCR.

The Forward Deployed Engineer makes the AI tool work across those real conditions.

---

### 6. They close the gap between “demo” and “production”

A demo can look impressive.

A production system has to survive real users, weird documents, bad inputs, edge cases, compliance issues, and angry customers.

**Example:**

Demo:

> “AI explains a clean auto policy.”

Production reality:

> “AI must handle blurry scans, missing pages, endorsements, state amendments, conflicting policy terms, and must cite the exact clause before giving an answer.”

The Forward Deployed Engineer helps bridge that gap.

## In the PolicySight context

For **PolicySight — Your Policy, Decoded. Your Claim, De**, a Forward Deployed Engineer would likely help turn the tool from a nice policy-explanation app into a real claims-support product.

They might work on things like:

* testing real auto insurance policies
* improving policy text extraction
* validating AI answers against actual policy clauses
* building claim scenario workflows
* adding “show me where the policy says that” citations
* handling confusing coverage edge cases
* integrating with carrier or adjuster systems
* turning user complaints into product fixes

## Simple example

A user uploads an auto policy and asks:

> “Am I covered if my friend drove my car and crashed it?”

A basic AI may answer generally.

A Forward Deployed Engineer would make sure the system checks:

* who is an insured driver
* permissive-use language
* exclusions
* liability coverage
* collision coverage
* state-specific endorsements
* exact policy citations

Better answer:

> “Possibly, if your friend had permission to drive your car. The policy’s ‘Who Is An Insured’ section includes permissive users, but coverage may be limited by exclusions. Here are the exact policy sections to review…”

That is the kind of real-world improvement a Forward Deployed Engineer drives.

Below are **test case scenarios for a Forward Deployed Engineer working on PolicySight**, especially for an **AI-driven auto insurance policy + claim explanation tool**.

These test whether the engineer can handle messy real-world insurance workflows, not just clean demos.

---

## Test Case 1: Clean Policy Upload + Basic Coverage Question

**Scenario:**
A user uploads a clear auto insurance policy PDF and asks:

> “What is my collision deductible?”

**What the system should do:**

* Detect the declarations page.
* Find collision coverage.
* Extract the deductible amount.
* Explain it simply.
* Cite the exact policy/declarations text.

**Expected result:**

> “Your collision deductible is $500. This means if your covered vehicle is damaged in a collision, you usually pay the first $500 before insurance pays the rest.”

**Pass condition:**
The answer includes the correct deductible and references the right policy section.

---

## Test Case 2: Confusing Deductibles

**Scenario:**
The policy has:

* Comprehensive deductible: $250
* Collision deductible: $1,000
* Glass deductible: $0

User asks:

> “What’s my deductible?”

**Risk:**
The AI may give only one deductible or confuse coverage types.

**Expected result:**

> “Your deductible depends on the type of claim. Collision is $1,000, comprehensive is $250, and glass appears to have no deductible.”

**Pass condition:**
The system does not oversimplify. It separates deductible types clearly.

---

## Test Case 3: Permissive Driver Claim

**Scenario:**
The insured’s friend borrowed the car with permission and caused an accident.

User asks:

> “Is my friend covered if they crashed my car?”

**What the system should check:**

* “Who is an insured” language
* permissive-use clause
* exclusions
* liability coverage
* collision coverage
* state endorsements

**Expected result:**

> “The policy may cover a person using your covered auto with your permission, but coverage depends on exclusions and limits. The relevant section is…”

**Pass condition:**
The answer avoids a hard yes/no unless the policy language clearly supports it.

---

## Test Case 4: Excluded Driver

**Scenario:**
The policy includes a named driver exclusion for “John Smith.” John drives the car and crashes.

User asks:

> “Will my insurance cover this accident?”

**Expected result:**

> “The policy lists John Smith as an excluded driver. If he was driving at the time of the accident, coverage may be denied or limited based on that exclusion.”

**Pass condition:**
The system detects the named-driver exclusion and flags it prominently.

---

## Test Case 5: Missing Declarations Page

**Scenario:**
User uploads only the policy booklet, not the declarations page.

User asks:

> “What are my liability limits?”

**Expected result:**

> “I cannot determine your exact liability limits from this document because the declarations page appears to be missing. The policy booklet explains how liability coverage works, but your actual limits are usually listed on the declarations page.”

**Pass condition:**
The AI admits missing information instead of guessing.

---

## Test Case 6: Bad OCR / Scanned PDF

**Scenario:**
User uploads a blurry scanned auto policy.

The OCR reads:

> “Bodly Injury Liabllty $25,O00/$5O,O00”

**Expected result:**

* Detect likely OCR errors.
* Interpret cautiously.
* Mark confidence as low or medium.
* Ask for clearer document or human review.

**Expected answer:**

> “This appears to say Bodily Injury Liability may be $25,000/$50,000, but the scan quality is poor. Please verify this against the original declarations page.”

**Pass condition:**
The system does not confidently present corrupted OCR as fact.

---

## Test Case 7: Policy Endorsement Changes Coverage

**Scenario:**
The main policy says rental reimbursement is available, but an endorsement removes rental coverage.

User asks:

> “Do I have rental car coverage?”

**Expected result:**

> “The base policy describes rental reimbursement, but the endorsement appears to remove or modify that coverage. The endorsement usually controls if it conflicts with the base policy.”

**Pass condition:**
The system understands that endorsements can override standard policy language.

---

## Test Case 8: State-Specific Minimum Coverage

**Scenario:**
The policy is issued in New Jersey, but the user asks a general question:

> “Is this enough liability coverage?”

**Expected behavior:**

* Identify the state.
* Compare policy limits cautiously against state minimums only if the information is available.
* Avoid giving legal or financial advice as certainty.

**Expected result:**

> “Your policy shows liability limits of $25,000/$50,000. Whether this is enough depends on your state requirements and personal risk. This may satisfy minimum requirements, but minimum coverage may not fully protect you in a serious accident.”

**Pass condition:**
The tool distinguishes legal minimums from adequate protection.

---

## Test Case 9: Claim Scenario With Multiple Coverages

**Scenario:**
User says:

> “A tree fell on my parked car during a storm. Am I covered?”

**Expected checks:**

* comprehensive coverage
* deductible
* excluded causes
* covered auto
* policy active date

**Expected result:**

> “This type of damage is usually handled under comprehensive coverage, not collision. Your policy shows comprehensive coverage with a $500 deductible.”

**Pass condition:**
The system routes the claim to the correct coverage type.

---

## Test Case 10: Collision vs Comprehensive Confusion

**Scenario:**
User says:

> “I hit a deer. Is that collision?”

**Expected result:**

> “Hitting an animal is commonly treated under comprehensive coverage, not collision, depending on the policy language.”

**Pass condition:**
The system does not assume “impact = collision.” It checks policy definitions.

---

## Test Case 11: Policy Period Problem

**Scenario:**
Accident date: March 3, 2026
Policy period: March 10, 2026 to September 10, 2026

User asks:

> “Am I covered for this accident?”

**Expected result:**

> “The accident date appears to be before the policy start date. Based on the dates provided, this policy would likely not cover that accident.”

**Pass condition:**
The system checks policy effective dates before analyzing coverage.

---

## Test Case 12: Vehicle Not Listed

**Scenario:**
Policy lists:

* 2021 Toyota Camry
* 2023 Honda CR-V

Accident vehicle:

* 2018 Ford F-150

User asks:

> “Is my truck covered?”

**Expected result:**

> “The Ford F-150 does not appear on the listed vehicles in this policy. Coverage may depend on newly acquired vehicle rules, temporary substitute auto language, or another policy.”

**Pass condition:**
The system flags that the vehicle is not obviously covered.

---

## Test Case 13: AI Citation Accuracy

**Scenario:**
Ask the system:

> “Show me exactly where the policy says I have uninsured motorist coverage.”

**Expected behavior:**

* Provide the policy section.
* Quote or cite only the relevant text.
* Avoid citing unrelated liability or medical payments sections.

**Pass condition:**
The citation points to the correct coverage section, not just a nearby page.

---

## Test Case 14: Contradictory Documents

**Scenario:**
User uploads two declarations pages:

* Old policy: liability $50,000/$100,000
* New policy: liability $100,000/$300,000

User asks:

> “What are my liability limits?”

**Expected result:**

> “I found two different declarations pages with different policy periods. The most recent/current one appears to show $100,000/$300,000, assuming that policy was active on the claim date.”

**Pass condition:**
The system detects conflicting documents and uses policy dates to reason.

---

## Test Case 15: Human Escalation Needed

**Scenario:**
User asks:

> “The carrier denied my claim. Are they wrong?”

**Expected behavior:**

* Analyze policy language.
* Compare denial reason to policy sections.
* Avoid giving legal judgment.
* Recommend review by adjuster, attorney, or licensed insurance professional if needed.

**Expected result:**

> “The denial appears to rely on the excluded-driver clause. The policy language may support that denial, but this should be reviewed by a licensed insurance professional or attorney if you want to dispute it.”

**Pass condition:**
The AI supports claim review without pretending to be a legal authority.

---

## Forward Deployed Engineer Success Checklist

A good Forward Deployed Engineer should confirm that the system can:

| Capability                                       | Must Work? |
| ------------------------------------------------ | ---------: |
| Extract declaration-page values                  |        Yes |
| Identify coverage types correctly                |        Yes |
| Detect exclusions                                |        Yes |
| Handle endorsements                              |        Yes |
| Cite exact policy language                       |        Yes |
| Admit missing information                        |        Yes |
| Handle OCR errors cautiously                     |        Yes |
| Separate general explanation from claim decision |        Yes |
| Escalate high-risk cases                         |        Yes |
| Avoid fake certainty                             |        Yes |

## Strong “Agent Requirement” Version

For the PolicySight AI agent:

> The agent must analyze uploaded auto insurance policies against user claim questions by identifying applicable coverage, exclusions, limits, deductibles, endorsements, policy period, listed vehicles, listed drivers, and relevant state-specific terms. The agent must cite exact policy language, distinguish missing or ambiguous information, assign confidence levels, and escalate cases requiring human review.

You can send the AI Agent prompts in **four main categories**:

1. **Build prompts** — tell the agent what feature to implement.
2. **Test prompts** — tell the agent what scenario to validate.
3. **Debug prompts** — tell the agent what failure to investigate.
4. **Evaluation prompts** — tell the agent how to judge the answer quality.

Below are strong prompt examples for a PolicySight-style insurance AI agent.

---

## 1. General Agent Instruction Prompt

Use this when starting the agent’s task.

```text
You are working on PolicySight, an AI tool that explains auto insurance policies and claim scenarios.

Your job is to improve the system so it can analyze uploaded auto insurance policy documents, answer user coverage questions, cite exact policy language, identify missing information, and avoid unsupported conclusions.

Focus on practical insurance workflows, not generic chatbot answers.

For every change you make, consider:
- policy declarations page
- coverage limits
- deductibles
- exclusions
- endorsements
- policy period
- listed drivers
- listed vehicles
- claim date
- confidence level
- exact policy citation
- when to escalate to human review
```

---

## 2. Prompt to Build Test Cases

```text
Create realistic test cases for an AI auto insurance policy assistant.

Each test case should include:
- scenario name
- uploaded document condition
- user question
- relevant policy sections to inspect
- expected AI answer
- pass condition
- failure modes to watch for

Focus on messy real-world situations such as missing declarations pages, blurry OCR, conflicting endorsements, excluded drivers, permissive drivers, wrong claim dates, and vehicle mismatch.
```

---

## 3. Prompt to Test Deductible Extraction

```text
Test whether the AI agent can correctly identify deductibles from an auto insurance policy.

Use a scenario where the policy contains:
- collision deductible: $1,000
- comprehensive deductible: $250
- glass deductible: $0

The user asks: “What is my deductible?”

The agent should not give only one answer. It should explain that the deductible depends on the claim type, list each deductible separately, and cite the relevant declaration page text.
```

---

## 4. Prompt to Test Missing Information Handling

```text
Test the AI agent’s behavior when the declarations page is missing.

Scenario:
The user uploads only the standard auto policy booklet, not the declarations page.

User asks:
“What are my liability limits?”

Expected behavior:
The agent should explain that the uploaded document describes coverage terms but does not contain the actual selected limits. It should say the declarations page is needed and should not invent numbers.

Check whether the agent admits uncertainty clearly.
```

---

## 5. Prompt to Test Exclusions

```text
Test whether the AI agent can detect and explain an excluded-driver issue.

Scenario:
The policy contains a named driver exclusion for John Smith.

The user says:
“John Smith drove my car and crashed it. Am I covered?”

Expected behavior:
The agent should identify the named driver exclusion, explain that coverage may be denied or limited if John Smith was driving, cite the exclusion language, and recommend human review before making a final claim decision.
```

---

## 6. Prompt to Test Endorsements

```text
Test whether the AI agent understands that endorsements can modify or override the base policy.

Scenario:
The base policy describes rental reimbursement coverage, but a later endorsement removes rental reimbursement.

User asks:
“Do I have rental car coverage?”

Expected behavior:
The agent should compare the base policy and endorsement, recognize the conflict, explain that the endorsement likely controls, and cite both the original coverage section and the modifying endorsement.
```

---

## 7. Prompt to Test Claim-Date Logic

```text
Test whether the AI agent checks the policy period before answering coverage questions.

Scenario:
The accident happened on March 3, 2026.
The policy period is March 10, 2026 to September 10, 2026.

User asks:
“Am I covered for this accident?”

Expected behavior:
The agent should notice that the accident happened before the policy start date. It should explain that this policy likely does not apply to that accident and cite the policy period from the declarations page.
```

---

## 8. Prompt to Test Vehicle Matching

```text
Test whether the AI agent verifies that the claim vehicle is listed on the policy.

Scenario:
The policy lists:
- 2021 Toyota Camry
- 2023 Honda CR-V

The accident involved:
- 2018 Ford F-150

User asks:
“Is my truck covered?”

Expected behavior:
The agent should flag that the Ford F-150 is not listed on the declarations page. It should check whether the policy has newly acquired vehicle or temporary substitute auto language, but it should not assume coverage.
```

---

## 9. Prompt to Test OCR Caution

```text
Test whether the AI agent handles bad OCR safely.

Scenario:
A scanned declarations page has poor OCR. The text appears as:
“Bodly Injury Liabllty $25,O00/$5O,O00”

User asks:
“What are my bodily injury limits?”

Expected behavior:
The agent should recognize possible OCR errors, give a cautious interpretation, mark confidence as low or medium, and ask for a clearer document or manual verification.
```

---

## 10. Prompt to Test Citation Accuracy

```text
Evaluate whether the AI agent cites the correct policy language.

User asks:
“Show me exactly where the policy says I have uninsured motorist coverage.”

Expected behavior:
The agent must cite the uninsured motorist coverage section or declarations page entry. It must not cite unrelated liability, collision, comprehensive, or medical payments sections.

Failure condition:
The agent gives a correct-sounding answer but cites the wrong section.
```

---

## 11. Prompt to Test Safe Claim Advice

```text
Test whether the AI agent avoids acting like a final claim authority.

Scenario:
The carrier denied the claim based on an exclusion.

User asks:
“Is the insurance company wrong?”

Expected behavior:
The agent should compare the denial reason against the policy language, explain what the policy appears to say, cite the relevant sections, and avoid making a final legal or claim determination. It should recommend review by a licensed insurance professional, adjuster, or attorney if the user wants to dispute the denial.
```

---

## 12. Prompt to Ask the Agent to Improve Itself

```text
Review the current PolicySight AI agent behavior against these auto insurance test scenarios.

Identify:
- where the agent is likely to hallucinate
- where it may give false certainty
- where citations may be weak
- where policy sections may be confused
- where claim decisions require escalation
- what validations should be added before the agent answers

Then propose specific product requirements and engineering tasks to fix the gaps.
```

---

## 13. Prompt to Turn Scenarios Into Requirements

```text
Convert the following auto insurance test scenarios into engineering requirements for the PolicySight AI agent.

For each scenario, produce:
- requirement title
- user story
- acceptance criteria
- edge cases
- required document fields
- failure handling
- confidence scoring rule
- citation requirement

Use precise language suitable for a developer ticket.
```

---

## 14. Prompt to Generate Developer Tickets

```text
Create implementation tickets for a Forward Deployed Engineer working on PolicySight.

The tickets should cover:
- declarations page extraction
- coverage limit extraction
- deductible extraction
- exclusion detection
- endorsement conflict detection
- policy period validation
- listed vehicle validation
- listed driver validation
- OCR confidence handling
- citation verification
- human escalation logic

Each ticket should include:
- goal
- technical approach
- inputs
- outputs
- acceptance criteria
- test scenarios
```

---

## 15. Strong “Master Prompt” for Your AI Agent

This is probably the most useful one to start with:

```text
You are an AI engineering agent helping build PolicySight, an AI-powered auto insurance policy and claim explanation tool.

Your task is to design, test, and improve the system so it can answer real-world auto insurance questions using uploaded policy documents.

Create a complete test and implementation plan covering these scenarios:

1. Clean policy upload with basic deductible question
2. Multiple deductible types
3. Permissive driver claim
4. Excluded driver claim
5. Missing declarations page
6. Bad OCR or scanned PDF
7. Endorsement overriding base policy language
8. State-specific coverage concern
9. Tree falling on parked car
10. Deer collision/comprehensive confusion
11. Claim date outside policy period
12. Vehicle not listed on policy
13. Citation accuracy
14. Contradictory documents
15. Carrier denial review

For each scenario, provide:
- user question
- policy facts needed
- expected answer behavior
- required citations
- confidence level
- when to refuse certainty
- when to escalate to human review
- acceptance criteria
- engineering tasks needed to support it

The agent must prioritize accuracy, grounded policy citations, uncertainty handling, and real claims workflow usefulness over sounding confident.
```

---

A good pattern is:

```text
Given this insurance scenario, test whether the agent can:
1. find the right policy section,
2. answer in simple language,
3. cite the exact text,
4. avoid guessing,
5. identify missing facts,
6. escalate when needed.
```

That pattern will keep the AI agent from becoming a “confident explainer” and push it toward being a real **policy reasoning assistant**.
