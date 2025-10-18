## Provider configs[¶](https://vectorbt.pro/pvt_41531c19/cookbook/knowledge/#provider-configs "Permanent link")

VBT supports a variety of providers for document embedding and completion tasks. Below you can find common configurations for each provider. These configurations can be set globally or per-query.

### OpenAI (ChatGPT)[¶](https://vectorbt.pro/pvt_41531c19/cookbook/knowledge/#openai-chatgpt "Permanent link")

[OpenAI](https://openai.com/) is the default provider in VBT.

OpenAI requires you to set the `OPENAI_API_KEY` environment variable or pass it directly as `api_key`.

Set OpenAI API key

`[](https://vectorbt.pro/pvt_41531c19/cookbook/knowledge/#__codelineno-45-1)env["OPENAI_API_KEY"] = "<YOUR_OPENAI_API_KEY>"`

Embeddings

To use OpenAI (default), override the default `embeddings` configuration.

Set OpenAI as default embeddings provider

`[](https://vectorbt.pro/pvt_41531c19/cookbook/knowledge/#__codelineno-46-1)vbt.settings.set("knowledge.chat.embeddings", "openai")`

The embedding model can be changed in the settings.

Set embedding model

`[](https://vectorbt.pro/pvt_41531c19/cookbook/knowledge/#__codelineno-47-1)vbt.settings.set("knowledge.chat.embeddings_configs.openai.model", "text-embedding-3-large")`

By default, the number of dimensions are truncated to 256 for faster processing. You can revert this by setting the `dimensions` parameter to None.

Use the original dimensions

`[](https://vectorbt.pro/pvt_41531c19/cookbook/knowledge/#__codelineno-48-1)vbt.settings.set("knowledge.chat.embeddings_configs.openai.dimensions", None)`

By default, the number of embeddings processed at once (`batch_size`) is 256, which can also be increased (not recommended, unless the number of tokens in each document is small) or decreased.

Set batch size to 64

`[](https://vectorbt.pro/pvt_41531c19/cookbook/knowledge/#__codelineno-49-1)vbt.settings.set("knowledge.chat.embeddings_configs.openai.batch_size", 64)`

Use `client_kwargs` and `embeddings_kwargs` to pass additional arguments to the OpenAI client and the embeddings API, respectively. Whenever you set a custom key outside of these dictionaries, it will be assigned to either of these dictionaries automatically. See the [OpenAI documentation](https://platform.openai.com/docs/api-reference) for more details.

Set timeout to 20 seconds

`[](https://vectorbt.pro/pvt_41531c19/cookbook/knowledge/#__codelineno-50-1)vbt.settings.set("knowledge.chat.embeddings_configs.openai.client_kwargs.timeout", 20.0)`

Tip

To learn more about the available parameters, check the arguments of [Embeddings](https://vectorbt.pro/pvt_41531c19/api/knowledge/embeddings/#vectorbtpro.knowledge.embeddings.Embeddings) and [OpenAIEmbeddings](https://vectorbt.pro/pvt_41531c19/api/knowledge/embeddings/#vectorbtpro.knowledge.embeddings.OpenAIEmbeddings).

To revert all changes, reset the settings.

Reset embedding settings

`[](https://vectorbt.pro/pvt_41531c19/cookbook/knowledge/#__codelineno-51-1)vbt.settings.get("knowledge.chat.embeddings_configs.openai").reset()`
Completions

To use OpenAI (default), override the default `completions` configuration.

Set OpenAI as default completions provider

`[](https://vectorbt.pro/pvt_41531c19/cookbook/knowledge/#__codelineno-52-1)vbt.settings.set("knowledge.chat.completions", "openai")`

The main and quick (used in `vbt.quick_search()` and `vbt.quick_chat()`) completion models can be changed in the settings.

Set completion models

`[](https://vectorbt.pro/pvt_41531c19/cookbook/knowledge/#__codelineno-53-1)vbt.settings.set("knowledge.chat.completions_configs.openai.model", "gpt-5") [](https://vectorbt.pro/pvt_41531c19/cookbook/knowledge/#__codelineno-53-2)vbt.settings.set("knowledge.chat.completions_configs.openai.quick_model", "gpt-5-mini")`

Reasoning must be enabled explicitly.

Enable reasoning

`[](https://vectorbt.pro/pvt_41531c19/cookbook/knowledge/#__codelineno-54-1)vbt.settings.set("knowledge.chat.completions_configs.openai.reasoning.effort", "medium")`

Chain-of-thought (COT) summaries must be enabled explicitly.

Enable COT summaries

`[](https://vectorbt.pro/pvt_41531c19/cookbook/knowledge/#__codelineno-55-1)vbt.settings.set("knowledge.chat.completions_configs.openai.reasoning.summary", "auto")`

By default, the Responses API is used, but you can easily switch to the Completions API.

Switch to Completions API

`[](https://vectorbt.pro/pvt_41531c19/cookbook/knowledge/#__codelineno-56-1)vbt.settings.set("knowledge.chat.completions_configs.openai.use_responses", "False") [](https://vectorbt.pro/pvt_41531c19/cookbook/knowledge/#__codelineno-56-2)vbt.settings.set("knowledge.chat.completions_configs.openai.reasoning_effort", "medium")`

Note

COT summaries are not supported by the Completions API.

If the selected model returns reasoning output, you can disable it by setting `hide_thoughts` to True.

Disable reasoning output

`[](https://vectorbt.pro/pvt_41531c19/cookbook/knowledge/#__codelineno-57-1)vbt.settings.set("knowledge.chat.completions_configs.openai.hide_thoughts", True)`

Use `client_kwargs` and `completions_kwargs` to pass additional arguments to the OpenAI client and the completions API, respectively. Whenever you set a custom key outside of these dictionaries, it will be assigned to either of these dictionaries automatically. See the [OpenAI documentation](https://platform.openai.com/docs/api-reference) for more details.

Set timeout to 20 seconds

`[](https://vectorbt.pro/pvt_41531c19/cookbook/knowledge/#__codelineno-58-1)vbt.settings.set("knowledge.chat.completions_configs.openai.client_kwargs.timeout", 20.0)`

Tip

To learn more about the available parameters, check the arguments of [Completions](https://vectorbt.pro/pvt_41531c19/api/knowledge/completions/#vectorbtpro.knowledge.completions.Completions) and [OpenAICompletions](https://vectorbt.pro/pvt_41531c19/api/knowledge/completions/#vectorbtpro.knowledge.completions.OpenAICompletions).

To revert all changes, reset the settings.

Reset completion settings

`[](https://vectorbt.pro/pvt_41531c19/cookbook/knowledge/#__codelineno-59-1)vbt.settings.get("knowledge.chat.completions_configs.openai").reset()`

#### Example: OpenRouter[¶](https://vectorbt.pro/pvt_41531c19/cookbook/knowledge/#example-openrouter "Permanent link")

Set the appropriate base URL and API key to use [OpenRouter](https://openrouter.ai/) or other OpenAI-compatible providers.

Configure OpenRouter for DeepSeek R1

`[](https://vectorbt.pro/pvt_41531c19/cookbook/knowledge/#__codelineno-60-1)vbt.settings.set("knowledge.chat.completions", "openai") [](https://vectorbt.pro/pvt_41531c19/cookbook/knowledge/#__codelineno-60-2)vbt.settings.set("knowledge.chat.completions_configs.openai.base_url", "https://openrouter.ai/api/v1") [](https://vectorbt.pro/pvt_41531c19/cookbook/knowledge/#__codelineno-60-3)vbt.settings.set("knowledge.chat.completions_configs.openai.api_key", "<YOUR_OPENROUTER_API_KEY>") [](https://vectorbt.pro/pvt_41531c19/cookbook/knowledge/#__codelineno-60-4)vbt.settings.set("knowledge.chat.completions_configs.openai.model", "deepseek/deepseek-r1") [](https://vectorbt.pro/pvt_41531c19/cookbook/knowledge/#__codelineno-60-5)vbt.settings.set("knowledge.chat.completions_configs.openai.use_responses", False)`  

### Anthropic (Claude)[¶](https://vectorbt.pro/pvt_41531c19/cookbook/knowledge/#anthropic-claude "Permanent link")

[Anthropic](https://www.anthropic.com/) with Claude is a popular LLM provider.

Anthropic requires you to set the `ANTHROPIC_API_KEY` environment variable or pass it directly as `api_key`.

Set Anthropic API key

`[](https://vectorbt.pro/pvt_41531c19/cookbook/knowledge/#__codelineno-61-1)env["ANTHROPIC_API_KEY"] = "<YOUR_ANTHROPIC_API_KEY>"`

Info

Anthropic does not currently support embeddings.

Completions

To use Anthropic, override the default `embeddings` configuration.

Set Anthropic as default embeddings provider

`[](https://vectorbt.pro/pvt_41531c19/cookbook/knowledge/#__codelineno-62-1)vbt.settings.set("knowledge.chat.embeddings", "anthropic")`

The main and quick (used in `vbt.quick_search()` and `vbt.quick_chat()`) completion models can be changed in the settings.

Set completion models

`[](https://vectorbt.pro/pvt_41531c19/cookbook/knowledge/#__codelineno-63-1)vbt.settings.set("knowledge.chat.completions_configs.anthropic.model", "claude-sonnet-4-0") [](https://vectorbt.pro/pvt_41531c19/cookbook/knowledge/#__codelineno-63-2)vbt.settings.set("knowledge.chat.completions_configs.anthropic.quick_model", "claude-3-5-haiku-latest")`

Reasoning must be enabled explicitly by setting the `thinking` parameters.

Enable reasoning

`[](https://vectorbt.pro/pvt_41531c19/cookbook/knowledge/#__codelineno-64-1)vbt.settings.set("knowledge.chat.completions_configs.anthropic.thinking.type", "enabled") [](https://vectorbt.pro/pvt_41531c19/cookbook/knowledge/#__codelineno-64-2)vbt.settings.set("knowledge.chat.completions_configs.anthropic.thinking.budget_tokens", 2048)`

If the selected model returns reasoning output, you can disable it by setting `hide_thoughts` to True.

Disable reasoning output

`[](https://vectorbt.pro/pvt_41531c19/cookbook/knowledge/#__codelineno-65-1)vbt.settings.set("knowledge.chat.completions_configs.anthropic.hide_thoughts", True)`

AWS Bedrock and Google Vertex can be used by setting `client_type` to "bedrock" or "vertex", respectively.

Use AWS Bedrock

`[](https://vectorbt.pro/pvt_41531c19/cookbook/knowledge/#__codelineno-66-1)vbt.settings.set("knowledge.chat.completions_configs.anthropic.client_type", "bedrock")`

Use `client_kwargs` and `messages_kwargs` to pass additional arguments to the Anthropic client and the messages API, respectively. Whenever you set a custom key outside of these dictionaries, it will be assigned to either of these dictionaries automatically. See the [Anthropic documentation](https://docs.anthropic.com/) for more details.

Set maximum output tokens to 4096

`[](https://vectorbt.pro/pvt_41531c19/cookbook/knowledge/#__codelineno-67-1)vbt.settings.set("knowledge.chat.completions_configs.anthropic.messages_kwargs.max_tokens", 4096)`

Tip

To learn more about the available parameters, check the arguments of [Completions](https://vectorbt.pro/pvt_41531c19/api/knowledge/completions/#vectorbtpro.knowledge.completions.Completions) and [AnthropicCompletions](https://vectorbt.pro/pvt_41531c19/api/knowledge/completions/#vectorbtpro.knowledge.completions.AnthropicCompletions).

To revert all changes, reset the settings.

Reset completion settings

`[](https://vectorbt.pro/pvt_41531c19/cookbook/knowledge/#__codelineno-68-1)vbt.settings.get("knowledge.chat.completions_configs.anthropic").reset()`

### Google (Gemini)[¶](https://vectorbt.pro/pvt_41531c19/cookbook/knowledge/#google-gemini "Permanent link")

[Gemini](https://ai.google.dev/) is Google's latest LLM offering.

Google requires you to set the `GEMINI_API_KEY` environment variable or pass it directly as `api_key`.

Set Gemini API key

`[](https://vectorbt.pro/pvt_41531c19/cookbook/knowledge/#__codelineno-69-1)env["GEMINI_API_KEY"] = "<YOUR_GEMINI_API_KEY>"`

Embeddings

To use Gemini, override the default `embeddings` configuration.

Set Gemini as default embeddings provider

`[](https://vectorbt.pro/pvt_41531c19/cookbook/knowledge/#__codelineno-70-1)vbt.settings.set("knowledge.chat.embeddings", "gemini")`

The embedding model can be changed in the settings.

Set embedding model

`[](https://vectorbt.pro/pvt_41531c19/cookbook/knowledge/#__codelineno-71-1)vbt.settings.set("knowledge.chat.embeddings_configs.gemini.model", "gemini-embedding-001")`

By default, the number of dimensions are truncated to 768 (and normalized) for faster processing. You can revert this by setting the `output_dimensionality` parameter to None.

Use the original dimensions

`[](https://vectorbt.pro/pvt_41531c19/cookbook/knowledge/#__codelineno-72-1)vbt.settings.set("knowledge.chat.embeddings_configs.gemini.config.output_dimensionality", None)`

By default, the number of embeddings processed at once (`batch_size`) is 256, which can also be increased (not recommended, unless the number of tokens in each document is small) or decreased.

Set batch size to 64

`[](https://vectorbt.pro/pvt_41531c19/cookbook/knowledge/#__codelineno-73-1)vbt.settings.set("knowledge.chat.embeddings_configs.gemini.batch_size", 64)`

Use `client_kwargs` and `embeddings_kwargs` to pass additional arguments to the Gemini client and the embeddings API, respectively. Whenever you set a custom key outside of these dictionaries, it will be assigned to either of these dictionaries automatically. See the [Gemini documentation](https://ai.google.dev/gemini-api/docs/) for more details.

Use Vertex AI

`[](https://vectorbt.pro/pvt_41531c19/cookbook/knowledge/#__codelineno-74-1)vbt.settings.set("knowledge.chat.embeddings_configs.gemini.client_kwargs.vertexai", True) [](https://vectorbt.pro/pvt_41531c19/cookbook/knowledge/#__codelineno-74-2)vbt.settings.set("knowledge.chat.embeddings_configs.gemini.client_kwargs.project", "my-project-id") [](https://vectorbt.pro/pvt_41531c19/cookbook/knowledge/#__codelineno-74-3)vbt.settings.set("knowledge.chat.embeddings_configs.gemini.client_kwargs.location", "us-central1")`

Tip

To learn more about the available parameters, check the arguments of [Embeddings](https://vectorbt.pro/pvt_41531c19/api/knowledge/embeddings/#vectorbtpro.knowledge.embeddings.Embeddings) and [GeminiEmbeddings](https://vectorbt.pro/pvt_41531c19/api/knowledge/embeddings/#vectorbtpro.knowledge.embeddings.GeminiEmbeddings).

To revert all changes, reset the settings.

Reset embedding settings

`[](https://vectorbt.pro/pvt_41531c19/cookbook/knowledge/#__codelineno-75-1)vbt.settings.get("knowledge.chat.embeddings_configs.gemini").reset()`
Completions

To use Gemini, override the default `completions` configuration.

Set Gemini as default completions provider

`[](https://vectorbt.pro/pvt_41531c19/cookbook/knowledge/#__codelineno-76-1)vbt.settings.set("knowledge.chat.completions", "gemini")`

The main and quick (used in `vbt.quick_search()` and `vbt.quick_chat()`) completion models can be changed in the settings.

Set completion models

`[](https://vectorbt.pro/pvt_41531c19/cookbook/knowledge/#__codelineno-77-1)vbt.settings.set("knowledge.chat.completions_configs.gemini.model", "gemini-2.5-flash") [](https://vectorbt.pro/pvt_41531c19/cookbook/knowledge/#__codelineno-77-2)vbt.settings.set("knowledge.chat.completions_configs.gemini.quick_model", "gemini-2.5-flash-lite")`

Reasoning can be controlled by the `thinking_config` parameters.

Enable dynamic reasoning

`[](https://vectorbt.pro/pvt_41531c19/cookbook/knowledge/#__codelineno-78-1)vbt.settings.set("knowledge.chat.completions_configs.gemini.config.thinking_config.thinking_budget", -1)`

Chain-of-thought (COT) summaries must be enabled explicitly.

Enable COT summaries

`[](https://vectorbt.pro/pvt_41531c19/cookbook/knowledge/#__codelineno-79-1)vbt.settings.set("knowledge.chat.completions_configs.gemini.config.thinking_config.include_thoughts", True)`

If the selected model returns reasoning output, you can disable it by setting VBT's `hide_thoughts` to True.

Disable reasoning output

`[](https://vectorbt.pro/pvt_41531c19/cookbook/knowledge/#__codelineno-80-1)vbt.settings.set("knowledge.chat.completions_configs.gemini.hide_thoughts", True)`

Use `client_kwargs` and `completions_kwargs` to pass additional arguments to the Gemini client and the completions API, respectively. Whenever you set a custom key outside of these dictionaries, it will be assigned to either of these dictionaries automatically. See the [Gemini documentation](https://ai.google.dev/gemini-api/docs/) for more details.

Use Vertex AI

`[](https://vectorbt.pro/pvt_41531c19/cookbook/knowledge/#__codelineno-81-1)vbt.settings.set("knowledge.chat.completions_configs.gemini.client_kwargs.vertexai", True) [](https://vectorbt.pro/pvt_41531c19/cookbook/knowledge/#__codelineno-81-2)vbt.settings.set("knowledge.chat.completions_configs.gemini.client_kwargs.project", "my-project-id") [](https://vectorbt.pro/pvt_41531c19/cookbook/knowledge/#__codelineno-81-3)vbt.settings.set("knowledge.chat.completions_configs.gemini.client_kwargs.location", "us-central1")`

Tip

To learn more about the available parameters, check the arguments of [Completions](https://vectorbt.pro/pvt_41531c19/api/knowledge/completions/#vectorbtpro.knowledge.completions.Completions) and [GeminiCompletions](https://vectorbt.pro/pvt_41531c19/api/knowledge/completions/#vectorbtpro.knowledge.completions.GeminiCompletions).

To revert all changes, reset the settings.

Reset completion settings

`[](https://vectorbt.pro/pvt_41531c19/cookbook/knowledge/#__codelineno-82-1)vbt.settings.get("knowledge.chat.completions_configs.gemini").reset()`

### Hugging Face Inference[¶](https://vectorbt.pro/pvt_41531c19/cookbook/knowledge/#hugging-face-inference "Permanent link")

[Hugging Face](https://huggingface.co/) provides a wide range of models and APIs. The Inference API allows you to use these models for embeddings and completions without needing to host your own infrastructure.

Hugging Face requires you to set the `HF_TOKEN` environment variable or pass it directly as `api_key`.

Set Hugging Face API key

`[](https://vectorbt.pro/pvt_41531c19/cookbook/knowledge/#__codelineno-83-1)env["HF_TOKEN"] = "<YOUR_HF_TOKEN>"`

Embeddings

To use Hugging Face Inference, override the default `embeddings` configuration.

Set Hugging Face Inference as default embeddings provider

`[](https://vectorbt.pro/pvt_41531c19/cookbook/knowledge/#__codelineno-84-1)vbt.settings.set("knowledge.chat.embeddings", "hf_inference")`

The embedding model can be changed in the settings.

Set embedding model

`[](https://vectorbt.pro/pvt_41531c19/cookbook/knowledge/#__codelineno-85-1)vbt.settings.set("knowledge.chat.embeddings_configs.hf_inference.model", "Qwen/Qwen3-Embedding-8B")`

By default, the number of embeddings processed at once (`batch_size`) is 256, which can also be increased (not recommended, unless the number of tokens in each document is small) or decreased.

Set batch size to 64

`[](https://vectorbt.pro/pvt_41531c19/cookbook/knowledge/#__codelineno-86-1)vbt.settings.set("knowledge.chat.embeddings_configs.hf_inference.batch_size", 64)`

Use `client_kwargs` and `feature_extraction_kwargs` to pass additional arguments to the Hugging Face Inference client and the feature-extraction API, respectively. Whenever you set a custom key outside of these dictionaries, it will be assigned to either of these dictionaries automatically. See the [Hugging Face documentation](https://huggingface.co/docs) for more details.

Set timeout to 20 seconds

`[](https://vectorbt.pro/pvt_41531c19/cookbook/knowledge/#__codelineno-87-1)vbt.settings.set("knowledge.chat.embeddings_configs.hf_inference.client_kwargs.timeout", 20)`

Tip

To learn more about the available parameters, check the arguments of [Embeddings](https://vectorbt.pro/pvt_41531c19/api/knowledge/embeddings/#vectorbtpro.knowledge.embeddings.Embeddings) and [HFInferenceEmbeddings](https://vectorbt.pro/pvt_41531c19/api/knowledge/embeddings/#vectorbtpro.knowledge.embeddings.HFInferenceEmbeddings).

To revert all changes, reset the settings.

Reset embedding settings

`[](https://vectorbt.pro/pvt_41531c19/cookbook/knowledge/#__codelineno-88-1)vbt.settings.get("knowledge.chat.embeddings_configs.hf_inference").reset()`
Completions

To use Hugging Face Inference, override the default `completions` configuration.

Set Hugging Face Inference as default completions provider

`[](https://vectorbt.pro/pvt_41531c19/cookbook/knowledge/#__codelineno-89-1)vbt.settings.set("knowledge.chat.completions", "hf_inference")`

The main and quick (used in `vbt.quick_search()` and `vbt.quick_chat()`) completion models can be changed in the settings.

Set completion models

`[](https://vectorbt.pro/pvt_41531c19/cookbook/knowledge/#__codelineno-90-1)vbt.settings.set("knowledge.chat.completions_configs.hf_inference.model", "openai/gpt-oss-120b") [](https://vectorbt.pro/pvt_41531c19/cookbook/knowledge/#__codelineno-90-2)vbt.settings.set("knowledge.chat.completions_configs.hf_inference.quick_model", "openai/gpt-oss-20b")`

If the selected model returns reasoning output, you can disable it by setting `hide_thoughts` to True.

Disable reasoning output

`[](https://vectorbt.pro/pvt_41531c19/cookbook/knowledge/#__codelineno-91-1)vbt.settings.set("knowledge.chat.completions_configs.hf_inference.hide_thoughts", True)`

Use `client_kwargs` and `chat_completion_kwargs` to pass additional arguments to the Hugging Face Inference client and the chat-completion API, respectively. Whenever you set a custom key outside of these dictionaries, it will be assigned to either of these dictionaries automatically. See the [Hugging Face documentation](https://huggingface.co/docs) for more details.

Use Together AI as inference provider

`[](https://vectorbt.pro/pvt_41531c19/cookbook/knowledge/#__codelineno-92-1)vbt.settings.set("knowledge.chat.completions_configs.hf_inference.chat_completion.provider", "together")`

Tip

To learn more about the available parameters, check the arguments of [Completions](https://vectorbt.pro/pvt_41531c19/api/knowledge/completions/#vectorbtpro.knowledge.completions.Completions) and [HFInferenceCompletions](https://vectorbt.pro/pvt_41531c19/api/knowledge/completions/#vectorbtpro.knowledge.completions.HFInferenceCompletions).

To revert all changes, reset the settings.

Reset completion settings

`[](https://vectorbt.pro/pvt_41531c19/cookbook/knowledge/#__codelineno-93-1)vbt.settings.get("knowledge.chat.completions_configs.hf_inference").reset()`

### LiteLLM[¶](https://vectorbt.pro/pvt_41531c19/cookbook/knowledge/#litellm "Permanent link")

[LiteLLM](https://www.litellm.ai/) is an LLM gateway in OpenAI format.

There isn't a specific API key for LiteLLM; you need to set the environment variable for the provider you want to use, such as `DEEPSEEK_API_KEY` for DeepSeek, or pass it directly as `api_key`. See the [LiteLLM documentation](https://docs.litellm.ai/) for more details.

Set API keys

`[](https://vectorbt.pro/pvt_41531c19/cookbook/knowledge/#__codelineno-94-1)env["OPENAI_API_KEY"] = "<YOUR_OPENAI_API_KEY>" [](https://vectorbt.pro/pvt_41531c19/cookbook/knowledge/#__codelineno-94-2)env["ANTHROPIC_API_KEY"] = "<YOUR_ANTHROPIC_API_KEY>" [](https://vectorbt.pro/pvt_41531c19/cookbook/knowledge/#__codelineno-94-3)env["GEMINI_API_KEY"] = "<YOUR_GEMINI_API_KEY>" [](https://vectorbt.pro/pvt_41531c19/cookbook/knowledge/#__codelineno-94-4)...`

Embeddings

To use LiteLLM, override the default `embeddings` configuration.

Set LiteLLM as default embeddings provider

`[](https://vectorbt.pro/pvt_41531c19/cookbook/knowledge/#__codelineno-95-1)vbt.settings.set("knowledge.chat.embeddings", "litellm")`

The embedding provider and/or model can be changed in the settings.

Set embedding model

`[](https://vectorbt.pro/pvt_41531c19/cookbook/knowledge/#__codelineno-96-1)vbt.settings.set("knowledge.chat.embeddings_configs.litellm.model", "gemini/gemini-embedding-001")`

By default, the number of dimensions are truncated to 256 for faster processing. You can revert this by setting the `dimensions` parameter to None.

Use the original dimensions

`[](https://vectorbt.pro/pvt_41531c19/cookbook/knowledge/#__codelineno-97-1)vbt.settings.set("knowledge.chat.embeddings_configs.litellm.dimensions", None)`

By default, the number of embeddings processed at once (`batch_size`) is 256, which can also be increased (not recommended, unless the number of tokens in each document is small) or decreased.

Set batch size to 64

`[](https://vectorbt.pro/pvt_41531c19/cookbook/knowledge/#__codelineno-98-1)vbt.settings.set("knowledge.chat.embeddings_configs.litellm.batch_size", 64)`

Use `embedding_kwargs` to pass additional arguments to the LiteLLM embedding API. See the [LiteLLM documentation](https://docs.litellm.ai/) for more details.

Set timeout to 20 seconds

`[](https://vectorbt.pro/pvt_41531c19/cookbook/knowledge/#__codelineno-99-1)vbt.settings.set("knowledge.chat.embeddings_configs.litellm.embedding_kwargs.timeout", 20.0)`

Tip

To learn more about the available parameters, check the arguments of [Embeddings](https://vectorbt.pro/pvt_41531c19/api/knowledge/embeddings/#vectorbtpro.knowledge.embeddings.Embeddings) and [LiteLLMEmbeddings](https://vectorbt.pro/pvt_41531c19/api/knowledge/embeddings/#vectorbtpro.knowledge.embeddings.LiteLLMEmbeddings).

To revert all changes, reset the settings.

Reset embedding settings

`[](https://vectorbt.pro/pvt_41531c19/cookbook/knowledge/#__codelineno-100-1)vbt.settings.get("knowledge.chat.embeddings_configs.litellm").reset()`
Completions

To use LiteLLM, override the default `completions` configuration.

Set LiteLLM as default completions provider

`[](https://vectorbt.pro/pvt_41531c19/cookbook/knowledge/#__codelineno-101-1)vbt.settings.set("knowledge.chat.completions", "litellm")`

The main and quick (used in `vbt.quick_search()` and `vbt.quick_chat()`) completion models can be changed in the settings.

Set completion models

`[](https://vectorbt.pro/pvt_41531c19/cookbook/knowledge/#__codelineno-102-1)vbt.settings.set("knowledge.chat.completions_configs.litellm.model", "gemini/gemini-2.5-flash") [](https://vectorbt.pro/pvt_41531c19/cookbook/knowledge/#__codelineno-102-2)vbt.settings.set("knowledge.chat.completions_configs.litellm.quick_model", "gemini/gemini-2.5-flash-lite")`

Reasoning must be enabled explicitly by setting `reasoning_effort`.

Enable reasoning

`[](https://vectorbt.pro/pvt_41531c19/cookbook/knowledge/#__codelineno-103-1)vbt.settings.set("knowledge.chat.completions_configs.litellm.reasoning_effort", "medium")`

If the selected model returns reasoning output, you can disable it by setting `hide_thoughts` to True.

Disable reasoning output

`[](https://vectorbt.pro/pvt_41531c19/cookbook/knowledge/#__codelineno-104-1)vbt.settings.set("knowledge.chat.completions_configs.litellm.hide_thoughts", True)`

Use `completion_kwargs` to pass additional arguments to the LiteLLM completion API. See the [LiteLLM documentation](https://docs.litellm.ai/) for more details.

Set timeout to 20 seconds

`[](https://vectorbt.pro/pvt_41531c19/cookbook/knowledge/#__codelineno-105-1)vbt.settings.set("knowledge.chat.completions_configs.litellm.completion_kwargs.timeout", 20.0)`

Tip

To learn more about the available parameters, check the arguments of [Completions](https://vectorbt.pro/pvt_41531c19/api/knowledge/completions/#vectorbtpro.knowledge.completions.Completions) and [LiteLLMCompletions](https://vectorbt.pro/pvt_41531c19/api/knowledge/completions/#vectorbtpro.knowledge.completions.LiteLLMCompletions).

To revert all changes, reset the settings.

Reset completion settings

`[](https://vectorbt.pro/pvt_41531c19/cookbook/knowledge/#__codelineno-106-1)vbt.settings.get("knowledge.chat.completions_configs.litellm").reset()`

### LlamaIndex[¶](https://vectorbt.pro/pvt_41531c19/cookbook/knowledge/#llamaindex "Permanent link")

[LlamaIndex](https://llamaindex.ai/) is a framework for building LLM applications that supports various data sources and integrations. While it provides a (somewhat) unified interface for working with different LLM providers, you may need to install and configure each provider individually.

There isn't a specific API key for LlamaIndex; you need to set the environment variable for the provider you want to use, such as `DEEPSEEK_API_KEY` for DeepSeek, or pass it directly as `api_key`. See the [LlamaIndex documentation](https://docs.llamaindex.ai/) for more details.

Set API keys

`[](https://vectorbt.pro/pvt_41531c19/cookbook/knowledge/#__codelineno-107-1)env["OPENAI_API_KEY"] = "<YOUR_OPENAI_API_KEY>" [](https://vectorbt.pro/pvt_41531c19/cookbook/knowledge/#__codelineno-107-2)env["ANTHROPIC_API_KEY"] = "<YOUR_ANTHROPIC_API_KEY>" [](https://vectorbt.pro/pvt_41531c19/cookbook/knowledge/#__codelineno-107-3)env["GEMINI_API_KEY"] = "<YOUR_GEMINI_API_KEY>" [](https://vectorbt.pro/pvt_41531c19/cookbook/knowledge/#__codelineno-107-4)...`

Embeddings

To use LlamaIndex, override the default `embeddings` configuration.

Set LlamaIndex as default embeddings provider

`[](https://vectorbt.pro/pvt_41531c19/cookbook/knowledge/#__codelineno-108-1)vbt.settings.set("knowledge.chat.embeddings", "llama_index")`

The embedding provider can be changed in the settings. For that, you need to set the `embedding` parameter to either the name of the class or its qualified name, such as "openai" or "llama\_index.llms.openai.OpenAI".

Set embedding provider

`[](https://vectorbt.pro/pvt_41531c19/cookbook/knowledge/#__codelineno-109-1)vbt.settings.set("knowledge.chat.embeddings_configs.llama_index.embedding", "openai")`

The embedding model and other provider-specific settings can be configured under the lowercase-formatted provider name in `embedding_configs`.

Set embedding model

`[](https://vectorbt.pro/pvt_41531c19/cookbook/knowledge/#__codelineno-110-1)vbt.settings.set("knowledge.chat.embeddings_configs.llama_index.embedding_configs.openai.model", "text-embedding-3-large")`

By default, the number of embeddings processed at once (`batch_size`) is 256, which can also be increased (not recommended, unless the number of tokens in each document is small) or decreased. This can be done both globally and per-provider.

Set batch size to 64

`[](https://vectorbt.pro/pvt_41531c19/cookbook/knowledge/#__codelineno-111-1)vbt.settings.set("knowledge.chat.embeddings_configs.llama_index.embedding_configs.openai.batch_size", 64)`

Tip

To learn more about the available parameters, check the arguments of [Embeddings](https://vectorbt.pro/pvt_41531c19/api/knowledge/embeddings/#vectorbtpro.knowledge.embeddings.Embeddings) and [LlamaIndexEmbeddings](https://vectorbt.pro/pvt_41531c19/api/knowledge/embeddings/#vectorbtpro.knowledge.embeddings.LlamaIndexEmbeddings).

To revert all changes, reset the settings. This can be done both globally and per-provider.

Reset embedding settings

`[](https://vectorbt.pro/pvt_41531c19/cookbook/knowledge/#__codelineno-112-1)vbt.settings.get("knowledge.chat.embeddings_configs.llama_index.embedding_configs.openai").reset()`
Completions

To use LlamaIndex, override the default `completions` configuration.

Set LlamaIndex as default completions provider

`[](https://vectorbt.pro/pvt_41531c19/cookbook/knowledge/#__codelineno-113-1)vbt.settings.set("knowledge.chat.completions", "llama_index")`

The completion provider can be changed in the settings. For that, you need to set the `llm` parameter to either the name of the class or its qualified name (both are case-insensitive), such as "openai" or "llama\_index.llms.openai.OpenAI".

Set completion provider

`[](https://vectorbt.pro/pvt_41531c19/cookbook/knowledge/#__codelineno-114-1)vbt.settings.set("knowledge.chat.completions_configs.llama_index.llm", "openai")`

The main and quick (used in `vbt.quick_search()` and `vbt.quick_chat()`) completion models and other provider-specific settings can be configured under the lowercase-formatted provider name in `llm_configs`.

Set completion models

`[](https://vectorbt.pro/pvt_41531c19/cookbook/knowledge/#__codelineno-115-1)vbt.settings.set("knowledge.chat.completions_configs.llama_index.llm_configs.openai.model", "gpt-5) [](https://vectorbt.pro/pvt_41531c19/cookbook/knowledge/#__codelineno-115-2)vbt.settings.set("knowledge.chat.completions_configs.llama_index.llm_configs.openai.quick_model", "gpt-5-mini")`

If the selected model returns reasoning output, you can disable it by setting `hide_thoughts` to True.

Disable reasoning output

`[](https://vectorbt.pro/pvt_41531c19/cookbook/knowledge/#__codelineno-116-1)vbt.settings.set("knowledge.chat.completions_configs.llama_index.llm_configs.openai.hide_thoughts", True)`

Tip

To learn more about the available parameters, check the arguments of [Completions](https://vectorbt.pro/pvt_41531c19/api/knowledge/completions/#vectorbtpro.knowledge.completions.Completions) and [LlamaIndexCompletions](https://vectorbt.pro/pvt_41531c19/api/knowledge/completions/#vectorbtpro.knowledge.completions.LlamaIndexCompletions).

To revert all changes, reset the settings. This can be done both globally and per-provider.

Reset completion settings

`[](https://vectorbt.pro/pvt_41531c19/cookbook/knowledge/#__codelineno-117-1)vbt.settings.get("knowledge.chat.completions_configs.llama_index.llm_configs.openai").reset()`

#### Example: Local HF[¶](https://vectorbt.pro/pvt_41531c19/cookbook/knowledge/#example-local-hf "Permanent link")

LlamaIndex can be configured to use local Hugging Face models for embeddings and completions.

Configure LlamaIndex for Hugging Face

`[](https://vectorbt.pro/pvt_41531c19/cookbook/knowledge/#__codelineno-118-1)vbt.settings.set("knowledge.chat.embeddings", "llama_index") [](https://vectorbt.pro/pvt_41531c19/cookbook/knowledge/#__codelineno-118-2)vbt.settings.set("knowledge.chat.embeddings_configs.llama_index.embedding", "huggingface") [](https://vectorbt.pro/pvt_41531c19/cookbook/knowledge/#__codelineno-118-3)vbt.settings.set("knowledge.chat.embeddings_configs.llama_index.model_name", "BAAI/bge-small-en-v1.5")   [](https://vectorbt.pro/pvt_41531c19/cookbook/knowledge/#__codelineno-118-4)vbt.settings.set("knowledge.chat.embeddings_configs.llama_index.batch_size", 64)   [](https://vectorbt.pro/pvt_41531c19/cookbook/knowledge/#__codelineno-118-5)[](https://vectorbt.pro/pvt_41531c19/cookbook/knowledge/#__codelineno-118-6)vbt.settings.set("knowledge.chat.completions", "llama_index") [](https://vectorbt.pro/pvt_41531c19/cookbook/knowledge/#__codelineno-118-7)vbt.settings.set("knowledge.chat.completions_configs.llama_index.llm", "huggingface") [](https://vectorbt.pro/pvt_41531c19/cookbook/knowledge/#__codelineno-118-8)vbt.settings.set("knowledge.chat.completions_configs.llama_index.model_name", "deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B")   [](https://vectorbt.pro/pvt_41531c19/cookbook/knowledge/#__codelineno-118-9)vbt.settings.set("knowledge.chat.completions_configs.llama_index.tokenizer_name", "deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B") [](https://vectorbt.pro/pvt_41531c19/cookbook/knowledge/#__codelineno-118-10)[](https://vectorbt.pro/pvt_41531c19/cookbook/knowledge/#__codelineno-118-11)vbt.settings.set("knowledge.chat.rank_kwargs.dataset_id", "local")`

### Ollama[¶](https://vectorbt.pro/pvt_41531c19/cookbook/knowledge/#ollama "Permanent link")

[Ollama](https://ollama.com/) is a platform for running LLMs on your own hardware.

Embeddings

To use Ollama, override the default `embeddings` configuration.

Set Ollama as default embeddings provider

`[](https://vectorbt.pro/pvt_41531c19/cookbook/knowledge/#__codelineno-119-1)vbt.settings.set("knowledge.chat.embeddings", "ollama")`

The model (search for available models [here](https://ollama.com/search)) can be changed in the settings.

Set embedding model

`[](https://vectorbt.pro/pvt_41531c19/cookbook/knowledge/#__codelineno-120-1)vbt.settings.set("knowledge.chat.embeddings_configs.ollama.model", "dengcao/Qwen3-Embedding-0.6B")`

Info

The model will be automatically downloaded when you first use it. The progress bar will indicate the download status. To disable the progress bar, set `show_progress` to False.

By default, the number of embeddings processed at once (`batch_size`) is 256, which can also be increased or decreased depending on your hardware specifications.

Set batch size to 64

`[](https://vectorbt.pro/pvt_41531c19/cookbook/knowledge/#__codelineno-121-1)vbt.settings.set("knowledge.chat.embeddings_configs.ollama.batch_size", 64)`

Use `client_kwargs` and `embed_kwargs` to pass additional arguments to the Ollama client and the embed API, respectively. Whenever you set a custom key outside of these dictionaries, it will be assigned to either of these dictionaries automatically. See the [Ollama documentation](https://github.com/ollama/ollama-python) for more details.

Set timeout to 20 seconds

`[](https://vectorbt.pro/pvt_41531c19/cookbook/knowledge/#__codelineno-122-1)vbt.settings.set("knowledge.chat.embeddings_configs.ollama.embedding_kwargs.timeout", 20.0)`

Tip

To learn more about the available parameters, check the arguments of [Embeddings](https://vectorbt.pro/pvt_41531c19/api/knowledge/embeddings/#vectorbtpro.knowledge.embeddings.Embeddings) and [OllamaEmbeddings](https://vectorbt.pro/pvt_41531c19/api/knowledge/embeddings/#vectorbtpro.knowledge.embeddings.OllamaEmbeddings).

To revert all changes, reset the settings.

Reset embedding settings

`[](https://vectorbt.pro/pvt_41531c19/cookbook/knowledge/#__codelineno-123-1)vbt.settings.get("knowledge.chat.embeddings_configs.ollama").reset()`
Completions

To use Ollama, override the default `completions` configuration.

Set Ollama as default completions provider

`[](https://vectorbt.pro/pvt_41531c19/cookbook/knowledge/#__codelineno-124-1)vbt.settings.set("knowledge.chat.completions", "ollama")`

The main and quick (used in `vbt.quick_search()` and `vbt.quick_chat()`) completion models (search for available models [here](https://ollama.com/search)) can be changed in the settings.

Set completion models

`[](https://vectorbt.pro/pvt_41531c19/cookbook/knowledge/#__codelineno-125-1)vbt.settings.set("knowledge.chat.completions_configs.ollama.model", "qwen3:4b") [](https://vectorbt.pro/pvt_41531c19/cookbook/knowledge/#__codelineno-125-2)vbt.settings.set("knowledge.chat.completions_configs.ollama.quick_model", "qwen3:0.6b")`

Info

The model will be automatically downloaded when you first use it. The progress bar will indicate the download status. To disable the progress bar, set `show_progress` to False.

If the selected model returns reasoning output, you can disable it by setting `hide_thoughts` to True.

Disable reasoning output

`[](https://vectorbt.pro/pvt_41531c19/cookbook/knowledge/#__codelineno-126-1)vbt.settings.set("knowledge.chat.completions_configs.ollama.hide_thoughts", True)`

Use `client_kwargs` and `chat_kwargs` to pass additional arguments to the Ollama client and the chat API, respectively. Whenever you set a custom key outside of these dictionaries, it will be assigned to either of these dictionaries automatically. See the [Ollama documentation](https://github.com/ollama/ollama-python) for more details.

Set timeout to 20 seconds

`[](https://vectorbt.pro/pvt_41531c19/cookbook/knowledge/#__codelineno-127-1)vbt.settings.set("knowledge.chat.completions_configs.ollama.completion_kwargs.timeout", 20.0)`

Tip

To learn more about the available parameters, check the arguments of [Completions](https://vectorbt.pro/pvt_41531c19/api/knowledge/completions/#vectorbtpro.knowledge.completions.Completions) and [OllamaCompletions](https://vectorbt.pro/pvt_41531c19/api/knowledge/completions/#vectorbtpro.knowledge.completions.OllamaCompletions).

To revert all changes, reset the settings.

Reset completion settings

`[](https://vectorbt.pro/pvt_41531c19/cookbook/knowledge/#__codelineno-128-1)vbt.settings.get("knowledge.chat.completions_configs.ollama").reset()`

#### Example: GPT-OSS[¶](https://vectorbt.pro/pvt_41531c19/cookbook/knowledge/#example-gpt-oss "Permanent link")

[GPT-OSS](https://openai.com/index/introducing-gpt-oss/) is OpenAI's open-source alternative to ChatGPT mini models, designed to provide similar capabilities while being freely available.

Configure Ollama for high-reasoning GPT-OSS

`[](https://vectorbt.pro/pvt_41531c19/cookbook/knowledge/#__codelineno-129-1)vbt.settings.set("knowledge.chat.completions", "ollama") [](https://vectorbt.pro/pvt_41531c19/cookbook/knowledge/#__codelineno-129-2)vbt.settings.set("knowledge.chat.completions_configs.ollama.model", "gpt-oss:20b") [](https://vectorbt.pro/pvt_41531c19/cookbook/knowledge/#__codelineno-129-3)system_prompt = vbt.settings.get("knowledge.chat.system_prompt") [](https://vectorbt.pro/pvt_41531c19/cookbook/knowledge/#__codelineno-129-4)vbt.settings.set("knowledge.chat.completions_configs.ollama.system_prompt", f"{system_prompt}\n\n---\n\nReasoning: high")`