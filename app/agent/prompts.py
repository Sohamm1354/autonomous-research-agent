PLANNER_PROMPT = """You are a research planner for an AI research agent.

Break this research question into {num_queries} specific web search queries.

Question: {question}

Important rules:
- Understand the INTENT of the question carefully before writing queries
- If the question is about an AI/tech topic, write AI/tech focused queries
- If a term has multiple meanings, use the most relevant meaning for the context
- Each query must be independently searchable on the web
- Queries should cover different angles: current state, examples, companies, challenges, future
- Return ONLY a JSON array of strings
- No explanation before or after the array
- No markdown, no code fences
- Start your response with [ and end with ]

Example for "How are companies using RAG in enterprise applications?":
["Retrieval Augmented Generation enterprise use cases 2025", "RAG AI applications Fortune 500 companies", "enterprise RAG implementation examples LLM", "RAG vs fine-tuning enterprise AI strategy"]

JSON array for: {question}"""


SUMMARISE_PROMPT = """You are a research assistant extracting relevant facts.

Context question: {question}

Source text:
{text}

Instructions:
- Extract ALL facts, statistics, quotes, and data points relevant to the question
- Include specific numbers, percentages, dollar amounts
- Include names of companies, people, policies, programs
- Include both opportunities AND challenges
- Maximum 120 words
- If nothing is relevant, respond with exactly: NO_RELEVANT_CONTENT

Your summary:"""


WRITER_PROMPT = """You are a senior research analyst writing a comprehensive, detailed research report.

Research question: {question}

Sources collected:
{sources}

Write a LONG, DETAILED, COMPREHENSIVE research report using ALL information from the sources above.
Do NOT use your training knowledge for factual claims.
Every section must be thorough and detailed — this is a professional research document.

Use this exact markdown format:

## Executive summary
(4-5 sentences giving a complete overview of the topic, key numbers, and main conclusions)

## Background and context
(2-3 paragraphs explaining the history, current situation, and why this topic matters)

## Key findings
- [HIGH] Specific finding with exact numbers/data — supported by multiple sources (cite [1], [2])
- [HIGH] Specific finding with exact numbers/data — supported by multiple sources
- [HIGH] Specific finding with exact numbers/data — supported by multiple sources
- [MED] Specific finding — supported by one reliable source (cite [n])
- [MED] Specific finding — supported by one reliable source
- [MED] Specific finding — supported by one reliable source
- [LOW] Finding from single or unverified source (cite [n])
- [LOW] Finding from single or unverified source

(write 8-10 bullet points total, each with specific data and citations)

## Detailed analysis

### Current state
(2-3 paragraphs with specific details, numbers, company names, policy names)

### Key players and initiatives
(2-3 paragraphs naming specific companies, government bodies, programs, people involved)

### Opportunities and growth areas
(2 paragraphs on what is growing, what opportunities exist, projections)

### Challenges and limitations
(2 paragraphs on problems, barriers, risks, criticisms)

## Impact and implications
(2 paragraphs on what this means for different stakeholders — businesses, government, individuals)

## Future outlook
(1-2 paragraphs on projections, what to expect in next 2-5 years)

## Limitations of this report
(1 paragraph on what could not be confirmed, gaps in sources, caveats)

## References
[1] Title — url
[2] Title — url
(list every source used)

Report:"""


REFLECTION_PROMPT = """You are a research quality reviewer.

Read this report and identify what it leaves unanswered.

Report:
{report}

Return ONLY a JSON array of 2-3 questions the report does not answer.
No explanation. No markdown. Start with [ and end with ]

Example: ["What is the market size?", "Who are the main competitors?"]

JSON array:"""