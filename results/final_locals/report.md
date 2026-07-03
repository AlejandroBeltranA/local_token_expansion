# Unified Weekend Sweep

## Baseline

- Mistral-7B-Instruct-v0.3: rec=abort triggers=['latency_cliff', 'over_expansion', 'persistent_failure'] contract_failures=9 recoverable=4 unrecoverable=5 first_gated=15 mean_latency_ms=6360.6
- Mistral-7B-Instruct-v0.3: rec=abort triggers=['latency_cliff', 'over_expansion', 'persistent_failure'] contract_failures=9 recoverable=4 unrecoverable=5 first_gated=15 mean_latency_ms=6360.5
- Mistral-7B-Instruct-v0.3: rec=abort triggers=['latency_cliff', 'over_expansion', 'persistent_failure'] contract_failures=9 recoverable=4 unrecoverable=5 first_gated=15 mean_latency_ms=6350.6
- Mistral-7B-Instruct-v0.3: rec=abort triggers=['latency_cliff', 'over_expansion', 'persistent_failure'] contract_failures=9 recoverable=4 unrecoverable=5 first_gated=15 mean_latency_ms=6351.2
- Mistral-7B-Instruct-v0.3: rec=abort triggers=['latency_cliff', 'over_expansion', 'persistent_failure'] contract_failures=9 recoverable=4 unrecoverable=5 first_gated=15 mean_latency_ms=6349.1
- Mistral-7B-Instruct-v0.3: rec=abort triggers=['latency_cliff', 'over_expansion', 'persistent_failure'] contract_failures=9 recoverable=4 unrecoverable=5 first_gated=15 mean_latency_ms=6357.9
- Meta-Llama-3.1-8B-Instruct-3bit: rec=escalate triggers=['context_decay', 'over_expansion'] contract_failures=13 recoverable=6 unrecoverable=7 first_gated=None mean_latency_ms=4468.8
- Meta-Llama-3.1-8B-Instruct-3bit: rec=escalate triggers=['context_decay', 'over_expansion'] contract_failures=13 recoverable=6 unrecoverable=7 first_gated=None mean_latency_ms=4568.5
- Meta-Llama-3.1-8B-Instruct-3bit: rec=escalate triggers=['context_decay', 'over_expansion'] contract_failures=13 recoverable=6 unrecoverable=7 first_gated=None mean_latency_ms=4567.2
- Meta-Llama-3.1-8B-Instruct-3bit: rec=escalate triggers=['context_decay', 'over_expansion'] contract_failures=13 recoverable=6 unrecoverable=7 first_gated=None mean_latency_ms=4567.2
- Meta-Llama-3.1-8B-Instruct-3bit: rec=escalate triggers=['context_decay', 'over_expansion'] contract_failures=13 recoverable=6 unrecoverable=7 first_gated=None mean_latency_ms=4568.6
- Meta-Llama-3.1-8B-Instruct-3bit: rec=escalate triggers=['context_decay', 'over_expansion'] contract_failures=13 recoverable=6 unrecoverable=7 first_gated=None mean_latency_ms=4458.5
- Phi-4-mini-instruct-8bit: rec=retry triggers=['over_expansion'] contract_failures=8 recoverable=5 unrecoverable=3 first_gated=None mean_latency_ms=2419.2
- Phi-4-mini-instruct-8bit: rec=retry triggers=['over_expansion'] contract_failures=8 recoverable=5 unrecoverable=3 first_gated=None mean_latency_ms=2416.4
- Phi-4-mini-instruct-8bit: rec=retry triggers=['over_expansion'] contract_failures=8 recoverable=5 unrecoverable=3 first_gated=None mean_latency_ms=2415.8
- Phi-4-mini-instruct-8bit: rec=retry triggers=['over_expansion'] contract_failures=8 recoverable=5 unrecoverable=3 first_gated=None mean_latency_ms=2415.0
- Phi-4-mini-instruct-8bit: rec=retry triggers=['over_expansion'] contract_failures=8 recoverable=5 unrecoverable=3 first_gated=None mean_latency_ms=2416.5
- Phi-4-mini-instruct-8bit: rec=retry triggers=['over_expansion'] contract_failures=8 recoverable=5 unrecoverable=3 first_gated=None mean_latency_ms=2415.0
- Phi-3-mini-4k-instruct-4bit: rec=abort triggers=['context_decay', 'latency_cliff', 'near_cap_pressure', 'over_expansion', 'persistent_failure'] contract_failures=14 recoverable=9 unrecoverable=5 first_gated=15 mean_latency_ms=3884.8
- Phi-3-mini-4k-instruct-4bit: rec=abort triggers=['context_decay', 'latency_cliff', 'near_cap_pressure', 'over_expansion', 'persistent_failure'] contract_failures=14 recoverable=9 unrecoverable=5 first_gated=15 mean_latency_ms=3885.1
- Phi-3-mini-4k-instruct-4bit: rec=abort triggers=['context_decay', 'latency_cliff', 'near_cap_pressure', 'over_expansion', 'persistent_failure'] contract_failures=14 recoverable=9 unrecoverable=5 first_gated=15 mean_latency_ms=3884.6
- Phi-3-mini-4k-instruct-4bit: rec=abort triggers=['context_decay', 'latency_cliff', 'near_cap_pressure', 'over_expansion', 'persistent_failure'] contract_failures=14 recoverable=9 unrecoverable=5 first_gated=15 mean_latency_ms=3883.7
- Phi-3-mini-4k-instruct-4bit: rec=abort triggers=['context_decay', 'latency_cliff', 'near_cap_pressure', 'over_expansion', 'persistent_failure'] contract_failures=14 recoverable=9 unrecoverable=5 first_gated=15 mean_latency_ms=3882.9
- Phi-3-mini-4k-instruct-4bit: rec=abort triggers=['context_decay', 'latency_cliff', 'near_cap_pressure', 'over_expansion', 'persistent_failure'] contract_failures=14 recoverable=9 unrecoverable=5 first_gated=15 mean_latency_ms=3884.2
- SmolLM-1.7B-Instruct-4bit: rec=abort triggers=['context_decay', 'near_cap_pressure', 'over_expansion', 'persistent_failure'] contract_failures=17 recoverable=6 unrecoverable=11 first_gated=None mean_latency_ms=2868.0
- SmolLM-1.7B-Instruct-4bit: rec=abort triggers=['context_decay', 'near_cap_pressure', 'over_expansion', 'persistent_failure'] contract_failures=17 recoverable=6 unrecoverable=11 first_gated=None mean_latency_ms=2863.7
- SmolLM-1.7B-Instruct-4bit: rec=abort triggers=['context_decay', 'near_cap_pressure', 'over_expansion', 'persistent_failure'] contract_failures=17 recoverable=6 unrecoverable=11 first_gated=None mean_latency_ms=2864.7
- SmolLM-1.7B-Instruct-4bit: rec=abort triggers=['context_decay', 'near_cap_pressure', 'over_expansion', 'persistent_failure'] contract_failures=17 recoverable=6 unrecoverable=11 first_gated=None mean_latency_ms=2866.7
- SmolLM-1.7B-Instruct-4bit: rec=abort triggers=['context_decay', 'near_cap_pressure', 'over_expansion', 'persistent_failure'] contract_failures=17 recoverable=6 unrecoverable=11 first_gated=None mean_latency_ms=2867.0
- SmolLM-1.7B-Instruct-4bit: rec=abort triggers=['context_decay', 'near_cap_pressure', 'over_expansion', 'persistent_failure'] contract_failures=17 recoverable=6 unrecoverable=11 first_gated=None mean_latency_ms=2866.3
- Meta-Llama-3.1-8B-Instruct-8bit: rec=escalate triggers=['context_decay', 'over_expansion'] contract_failures=6 recoverable=1 unrecoverable=5 first_gated=None mean_latency_ms=5482.9
- Meta-Llama-3.1-8B-Instruct-8bit: rec=escalate triggers=['context_decay', 'over_expansion'] contract_failures=6 recoverable=1 unrecoverable=5 first_gated=None mean_latency_ms=5475.8
- Meta-Llama-3.1-8B-Instruct-8bit: rec=escalate triggers=['context_decay', 'over_expansion'] contract_failures=6 recoverable=1 unrecoverable=5 first_gated=None mean_latency_ms=5482.0
- Meta-Llama-3.1-8B-Instruct-8bit: rec=escalate triggers=['context_decay', 'over_expansion'] contract_failures=6 recoverable=1 unrecoverable=5 first_gated=None mean_latency_ms=5478.8
- Meta-Llama-3.1-8B-Instruct-8bit: rec=escalate triggers=['context_decay', 'over_expansion'] contract_failures=6 recoverable=1 unrecoverable=5 first_gated=None mean_latency_ms=5481.6
- Meta-Llama-3.1-8B-Instruct-8bit: rec=escalate triggers=['context_decay', 'over_expansion'] contract_failures=6 recoverable=1 unrecoverable=5 first_gated=None mean_latency_ms=5481.4
- Gemma-2-9b-it-4bit: rec=abort triggers=['context_decay', 'over_expansion', 'persistent_failure'] contract_failures=19 recoverable=8 unrecoverable=11 first_gated=None mean_latency_ms=4504.7
- Gemma-2-9b-it-4bit: rec=abort triggers=['context_decay', 'over_expansion', 'persistent_failure'] contract_failures=19 recoverable=8 unrecoverable=11 first_gated=None mean_latency_ms=4505.7
- Gemma-2-9b-it-4bit: rec=abort triggers=['context_decay', 'over_expansion', 'persistent_failure'] contract_failures=19 recoverable=8 unrecoverable=11 first_gated=None mean_latency_ms=4502.7
- Gemma-2-9b-it-4bit: rec=abort triggers=['context_decay', 'over_expansion', 'persistent_failure'] contract_failures=19 recoverable=8 unrecoverable=11 first_gated=None mean_latency_ms=4504.8
- Gemma-2-9b-it-4bit: rec=abort triggers=['context_decay', 'over_expansion', 'persistent_failure'] contract_failures=19 recoverable=8 unrecoverable=11 first_gated=None mean_latency_ms=4504.5
- Gemma-2-9b-it-4bit: rec=abort triggers=['context_decay', 'over_expansion', 'persistent_failure'] contract_failures=19 recoverable=8 unrecoverable=11 first_gated=None mean_latency_ms=4504.7

## Expansion

- No expansion runs executed.

