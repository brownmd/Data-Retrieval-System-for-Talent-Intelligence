-- GitHub AI Talent - BigQuery GitHub Profiles Query
-- ---------------------------------------------------
-- Single month:  FROM `githubarchive.month.202601`
-- Multi-month:   FROM `githubarchive.month.*` WHERE _TABLE_SUFFIX BETWEEN '202301' AND '202603'
--
-- Output: username, master_ai_literacy_score, literacy_tier, total_events, first_event, last_event

SELECT
  actor.login AS username,

  -- 1. MASTER SCORING LOGIC
  SUM(
    CASE 
      WHEN type = 'ReleaseEvent'           THEN 30
      WHEN type = 'PullRequestReviewEvent' THEN 25
      WHEN type = 'DeploymentEvent'        THEN 25
      WHEN type = 'PullRequestEvent'       THEN 20
      WHEN type = 'CheckRunEvent'          THEN 15
      WHEN type = 'PushEvent'              THEN 10
      WHEN type = 'WorkflowRunEvent'       THEN 10
      WHEN type = 'MemberEvent'            THEN 10
      WHEN type = 'IssuesEvent'            THEN 5
      WHEN type = 'IssueCommentEvent'      THEN 4
      WHEN type = 'ForkEvent'              THEN 2
      WHEN type = 'WatchEvent'             THEN 1
      ELSE 1 
    END
    *
    CASE 
      -- ELITE (L5-L6): Scaling, Interpretability, RL
      WHEN REGEXP_CONTAINS(LOWER(repo.name), r'grpo|prm|triton-lang|sae-lens|unsloth|vllm|sglang|deepseek-r1|transformer-lens|nnsight|logit-lens|activation-patching|sparse-autoencoder|cuda-mode') THEN 5.0
      -- AGENTIC (L4): Orchestration & MCP
      WHEN REGEXP_CONTAINS(LOWER(repo.name), r'langgraph|pydantic-ai|mcp-server|model-context-protocol|fastmcp|mem0|inngest|crewai|dspy|dify|langflow') THEN 3.5
      -- BUILDER (L3): SDKs & Frameworks
      WHEN REGEXP_CONTAINS(LOWER(repo.name), r'vercel-ai|ai-sdk|langchain|llamaindex|huggingface|trl|axolotl|llama-factory|ragas|deepeval') THEN 2.0
      -- VIBE/USER (L1-L2): Local Tools & UI
      WHEN REGEXP_CONTAINS(LOWER(repo.name), r'cursor|aider|bolt-new|clawbot|openclaw|ollama|open-webui|lm-studio|lmstudio') THEN 1.5
      ELSE 1.0 
    END
  ) AS master_ai_literacy_score,

  -- 2. PERSONA CATEGORIZATION
  CASE 
    -- L6: Code review activity AND elite repo exposure
    WHEN SUM(CASE WHEN type = 'PullRequestReviewEvent' THEN 1 ELSE 0 END) > 5 
         AND MAX(CASE WHEN REGEXP_CONTAINS(LOWER(repo.name), r'cuda-mode|triton-lang|grpo|sae-lens|transformer-lens') THEN 1 ELSE 0 END) = 1 
         THEN 'L6: AI Architect'

    -- L5: Releases AND works on frontier/infra repos
    WHEN SUM(CASE WHEN type = 'ReleaseEvent' THEN 1 ELSE 0 END) > 2
         AND MAX(CASE WHEN REGEXP_CONTAINS(LOWER(repo.name), r'vllm|sglang|unsloth|deepseek|tensorrt-llm|flash-attn|mamba-ssm') THEN 1 ELSE 0 END) = 1
         THEN 'L5: Frontier Engineer'

    -- L4: Full orchestration ecosystem
    WHEN MAX(CASE WHEN REGEXP_CONTAINS(LOWER(repo.name), r'langgraph|mcp-server|model-context-protocol|fastmcp|crewai|pydantic-ai|autogen|dspy|mem0|inngest|dify|langflow|agno') THEN 1 ELSE 0 END) = 1 
         THEN 'L4: Agentic Architect'

    -- L3: Active pusher with builder-tier repos
    WHEN SUM(CASE WHEN type = 'PushEvent' THEN 1 ELSE 0 END) > 20
         AND MAX(CASE WHEN REGEXP_CONTAINS(LOWER(repo.name), r'langchain|llamaindex|huggingface|trl|axolotl|ragas|deepeval|qlora|litellm') THEN 1 ELSE 0 END) = 1
         THEN 'L3: Production Builder'

    -- L2: AI-assisted dev tools
    WHEN MAX(CASE WHEN REGEXP_CONTAINS(LOWER(repo.name), r'cursor|bolt-new|v0-dev|lovable|replit-ai|windsurf|aider') THEN 1 ELSE 0 END) = 1 
         THEN 'L2: Vibe Coder'

    ELSE 'L1: AI Curious'
  END AS literacy_tier,

  COUNT(*) AS total_events,

  -- 3. ACTIVITY DATE RANGE
  MIN(created_at) AS first_event,
  MAX(created_at) AS last_event

FROM `githubarchive.month.*`
WHERE _TABLE_SUFFIX BETWEEN '202101' AND '202603'

WHERE
  -- llama.cpp isolated to guarantee correct regex escaping of the dot
  REGEXP_CONTAINS(LOWER(repo.name), r'llama\.cpp')

  OR REGEXP_CONTAINS(LOWER(repo.name), r'(' ||

    -- 1. HUGGING FACE ECOSYSTEM
    'huggingface|transformers|diffusers|peft|accelerate|safetensors|datasets|tokenizers|hf-mirror|' ||

    -- 2. AGENTIC & ORCHESTRATION
    'dspy|langgraph|openclaw|crewai|pydantic-ai|autogen|memgpt|browser-use|' ||
    'langchain|llamaindex|haystack|smolagents|phidata|agno|taskweaver|' ||
    'mem0|inngest|temporal-io|agent-ops|dify|langflow|' ||
    'open-operator|self-operating-computer|computer-use|agent-protocol|clawbot|' ||

    -- 3. AI CODING AGENTS
    'aider|continue-dev|tabby|opencodeinterpreter|claude-code|cursor|windsurf|coderabbit|greptile|' ||
    'bolt-new|lovable|v0-dev|replit-ai|idx-ai|' ||

    -- 4. INTERPRETABILITY & ALIGNMENT
    'transformer-lens|nnsight|sae-lens|sparse-autoencoder|logit-lens|activation-patching|' ||
    'alignment-handbook|dpo-trainer|rlhf|reward-model|math-verify|reasoning-trace|' ||
    'deepseek-r1|grpo|verifiers|prm|' ||

    -- 5. SYNTHETIC DATA
    'distilabel|gretel|mostly-ai|ydata|firecrawl|data-juicer|uniflow|' ||

    -- 6. FOUNDATION LABS & MODELS
    'deepseek|mistral|xai-org|meta-llama|google-gemini|anthropic|' ||
    'internlm|01-ai|cohere|togethercomputer|minicpm|phi-4|yi-34b|' ||

    -- 7. QWEN & ZHIPU
    'zai-org|zhipu|chatglm|glm-5|cogvlm|codegeex|qwen3|qwen-vl|qwen-mt|' ||

    -- 8. TRAINING & FINE-TUNING
    'unsloth|axolotl|llama-factory|torchtune|torchao|trl|qlora|' ||
    'bitnet|triton-lang|modular-mojo|max-engine|cuda-mode|' ||

    -- 9. ARCHITECTURE & OPTIMIZATION
    'sglang|vllm|tensorrt-llm|flash-attn|bitblas|autoawq|' ||
    'mamba-ssm|speculative-decoding|gguf|exl2|mlx-lm|litellm|' ||

    -- 10. EVALUATION & OBSERVABILITY
    'ragas|deepeval|promptfoo|langsmith|truelens|arize|phoenix|colpali|' ||
    'lm-evaluation-harness|lighteval|inspect-ai|evidently-ai|wandb|' ||

    -- 11. RED-TEAMING & SECURITY
    'garak|pyrit|mindgard|dioptra|jailbreak-eval|llm-security|' ||

    -- 12. LOCAL LLM ECOSYSTEM
    'ollama|open-webui|ggerganov|lm-studio|lmstudio|koboldcpp|jan-ai|' ||

    -- 13. MCP & TOOL PROTOCOL
    'model-context-protocol|mcp-server|fastmcp|' ||

    -- 14. ADVANCED RAG
    'graphrag|lightrag|hipporag|ragatouille|colbert|falkordb|' ||

    -- 15. VECTOR STORES
    'lancedb|chromadb|weaviate|qdrant|milvus|pinecone|pgvector|faiss|' ||

    -- 16. MULTIMODAL & GENERATIVE MEDIA
    'flux-ai|stable-diffusion|comfyui|invokeai|whisper|kokoro|mochi|ltx-video|f5-tts|' ||

    -- 17. MLOPS & DEPLOYMENT
    'replicate|modal-labs|groq-api|bentoml|vercel-ai|ai-sdk' ||

  ')')

GROUP BY 1
ORDER BY master_ai_literacy_score DESC
LIMIT 1000000;
