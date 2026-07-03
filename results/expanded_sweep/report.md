# Unified Weekend Sweep

## Baseline

- Mistral-7B-Instruct-v0.3: rec=abort triggers=['latency_cliff', 'over_expansion', 'persistent_failure'] contract_failures=4 recoverable=3 unrecoverable=1 first_gated=15 mean_latency_ms=6356.6
- Mistral-7B-Instruct-v0.3: rec=abort triggers=['latency_cliff', 'over_expansion', 'persistent_failure'] contract_failures=4 recoverable=3 unrecoverable=1 first_gated=15 mean_latency_ms=6357.6
- Mistral-7B-Instruct-v0.3: rec=abort triggers=['latency_cliff', 'over_expansion', 'persistent_failure'] contract_failures=4 recoverable=3 unrecoverable=1 first_gated=15 mean_latency_ms=6366.8
- Mistral-7B-Instruct-v0.3: rec=abort triggers=['latency_cliff', 'over_expansion', 'persistent_failure'] contract_failures=4 recoverable=3 unrecoverable=1 first_gated=15 mean_latency_ms=6357.4
- Mistral-7B-Instruct-v0.3: rec=abort triggers=['latency_cliff', 'over_expansion', 'persistent_failure'] contract_failures=4 recoverable=3 unrecoverable=1 first_gated=15 mean_latency_ms=6361.7
- Mistral-7B-Instruct-v0.3: rec=abort triggers=['latency_cliff', 'over_expansion', 'persistent_failure'] contract_failures=4 recoverable=3 unrecoverable=1 first_gated=15 mean_latency_ms=6357.3
- Meta-Llama-3.1-8B-Instruct-3bit: rec=escalate triggers=['context_decay', 'over_expansion'] contract_failures=9 recoverable=5 unrecoverable=4 first_gated=None mean_latency_ms=4475.9
- Meta-Llama-3.1-8B-Instruct-3bit: rec=escalate triggers=['context_decay', 'over_expansion'] contract_failures=9 recoverable=5 unrecoverable=4 first_gated=None mean_latency_ms=4473.6
- Meta-Llama-3.1-8B-Instruct-3bit: rec=escalate triggers=['context_decay', 'over_expansion'] contract_failures=9 recoverable=5 unrecoverable=4 first_gated=None mean_latency_ms=4469.7
- Meta-Llama-3.1-8B-Instruct-3bit: rec=escalate triggers=['context_decay', 'over_expansion'] contract_failures=9 recoverable=5 unrecoverable=4 first_gated=None mean_latency_ms=4471.5
- Meta-Llama-3.1-8B-Instruct-3bit: rec=escalate triggers=['context_decay', 'over_expansion'] contract_failures=9 recoverable=5 unrecoverable=4 first_gated=None mean_latency_ms=4474.6
- Meta-Llama-3.1-8B-Instruct-3bit: rec=escalate triggers=['context_decay', 'over_expansion'] contract_failures=9 recoverable=5 unrecoverable=4 first_gated=None mean_latency_ms=4477.7
- Phi-4-mini-instruct-8bit: rec=retry triggers=['over_expansion'] contract_failures=5 recoverable=4 unrecoverable=1 first_gated=None mean_latency_ms=2457.8
- Phi-4-mini-instruct-8bit: rec=retry triggers=['over_expansion'] contract_failures=5 recoverable=4 unrecoverable=1 first_gated=None mean_latency_ms=2454.5
- Phi-4-mini-instruct-8bit: rec=retry triggers=['over_expansion'] contract_failures=5 recoverable=4 unrecoverable=1 first_gated=None mean_latency_ms=2454.1
- Phi-4-mini-instruct-8bit: rec=retry triggers=['over_expansion'] contract_failures=5 recoverable=4 unrecoverable=1 first_gated=None mean_latency_ms=2460.5
- Phi-4-mini-instruct-8bit: rec=retry triggers=['over_expansion'] contract_failures=5 recoverable=4 unrecoverable=1 first_gated=None mean_latency_ms=2451.0
- Phi-4-mini-instruct-8bit: rec=retry triggers=['over_expansion'] contract_failures=5 recoverable=4 unrecoverable=1 first_gated=None mean_latency_ms=2451.2
- Phi-3-mini-4k-instruct-4bit: rec=abort triggers=['context_decay', 'latency_cliff', 'near_cap_pressure', 'over_expansion', 'persistent_failure'] contract_failures=11 recoverable=8 unrecoverable=3 first_gated=15 mean_latency_ms=3906.5
- Phi-3-mini-4k-instruct-4bit: rec=abort triggers=['context_decay', 'latency_cliff', 'near_cap_pressure', 'over_expansion', 'persistent_failure'] contract_failures=11 recoverable=8 unrecoverable=3 first_gated=15 mean_latency_ms=3938.3
- Phi-3-mini-4k-instruct-4bit: rec=abort triggers=['context_decay', 'latency_cliff', 'near_cap_pressure', 'over_expansion', 'persistent_failure'] contract_failures=11 recoverable=8 unrecoverable=3 first_gated=15 mean_latency_ms=3996.6
- Phi-3-mini-4k-instruct-4bit: rec=abort triggers=['context_decay', 'latency_cliff', 'near_cap_pressure', 'over_expansion', 'persistent_failure'] contract_failures=11 recoverable=8 unrecoverable=3 first_gated=15 mean_latency_ms=3995.8
- Phi-3-mini-4k-instruct-4bit: rec=abort triggers=['context_decay', 'latency_cliff', 'near_cap_pressure', 'over_expansion', 'persistent_failure'] contract_failures=11 recoverable=8 unrecoverable=3 first_gated=15 mean_latency_ms=3995.5
- Phi-3-mini-4k-instruct-4bit: rec=abort triggers=['context_decay', 'latency_cliff', 'near_cap_pressure', 'over_expansion', 'persistent_failure'] contract_failures=11 recoverable=8 unrecoverable=3 first_gated=15 mean_latency_ms=4000.7
- SmolLM-1.7B-Instruct-4bit: rec=abort triggers=['context_decay', 'near_cap_pressure', 'over_expansion', 'persistent_failure'] contract_failures=11 recoverable=5 unrecoverable=6 first_gated=None mean_latency_ms=2917.7
- SmolLM-1.7B-Instruct-4bit: rec=abort triggers=['context_decay', 'near_cap_pressure', 'over_expansion', 'persistent_failure'] contract_failures=11 recoverable=5 unrecoverable=6 first_gated=None mean_latency_ms=2916.0
- SmolLM-1.7B-Instruct-4bit: rec=abort triggers=['context_decay', 'near_cap_pressure', 'over_expansion', 'persistent_failure'] contract_failures=11 recoverable=5 unrecoverable=6 first_gated=None mean_latency_ms=2918.7
- SmolLM-1.7B-Instruct-4bit: rec=abort triggers=['context_decay', 'near_cap_pressure', 'over_expansion', 'persistent_failure'] contract_failures=11 recoverable=5 unrecoverable=6 first_gated=None mean_latency_ms=2915.7
- SmolLM-1.7B-Instruct-4bit: rec=abort triggers=['context_decay', 'near_cap_pressure', 'over_expansion', 'persistent_failure'] contract_failures=11 recoverable=5 unrecoverable=6 first_gated=None mean_latency_ms=2862.7
- SmolLM-1.7B-Instruct-4bit: rec=abort triggers=['context_decay', 'near_cap_pressure', 'over_expansion', 'persistent_failure'] contract_failures=11 recoverable=5 unrecoverable=6 first_gated=None mean_latency_ms=2861.0
- Meta-Llama-3.1-8B-Instruct-8bit: rec=escalate triggers=['context_decay', 'over_expansion'] contract_failures=5 recoverable=1 unrecoverable=4 first_gated=None mean_latency_ms=5484.0
- Meta-Llama-3.1-8B-Instruct-8bit: rec=escalate triggers=['context_decay', 'over_expansion'] contract_failures=5 recoverable=1 unrecoverable=4 first_gated=None mean_latency_ms=5479.3
- Meta-Llama-3.1-8B-Instruct-8bit: rec=escalate triggers=['context_decay', 'over_expansion'] contract_failures=5 recoverable=1 unrecoverable=4 first_gated=None mean_latency_ms=5484.1
- Meta-Llama-3.1-8B-Instruct-8bit: rec=escalate triggers=['context_decay', 'over_expansion'] contract_failures=5 recoverable=1 unrecoverable=4 first_gated=None mean_latency_ms=5477.8
- Meta-Llama-3.1-8B-Instruct-8bit: rec=escalate triggers=['context_decay', 'over_expansion'] contract_failures=5 recoverable=1 unrecoverable=4 first_gated=None mean_latency_ms=5478.9
- Meta-Llama-3.1-8B-Instruct-8bit: rec=escalate triggers=['context_decay', 'over_expansion'] contract_failures=5 recoverable=1 unrecoverable=4 first_gated=None mean_latency_ms=5588.0
- Gemma-2-9b-it-4bit: rec=abort triggers=['context_decay', 'over_expansion', 'persistent_failure'] contract_failures=13 recoverable=7 unrecoverable=6 first_gated=None mean_latency_ms=4623.8
- Gemma-2-9b-it-4bit: rec=abort triggers=['context_decay', 'over_expansion', 'persistent_failure'] contract_failures=13 recoverable=7 unrecoverable=6 first_gated=None mean_latency_ms=4610.9
- Gemma-2-9b-it-4bit: rec=abort triggers=['context_decay', 'over_expansion', 'persistent_failure'] contract_failures=13 recoverable=7 unrecoverable=6 first_gated=None mean_latency_ms=4613.5
- Gemma-2-9b-it-4bit: rec=abort triggers=['context_decay', 'over_expansion', 'persistent_failure'] contract_failures=13 recoverable=7 unrecoverable=6 first_gated=None mean_latency_ms=4606.0
- Gemma-2-9b-it-4bit: rec=abort triggers=['context_decay', 'over_expansion', 'persistent_failure'] contract_failures=13 recoverable=7 unrecoverable=6 first_gated=None mean_latency_ms=4603.2
- Gemma-2-9b-it-4bit: rec=abort triggers=['context_decay', 'over_expansion', 'persistent_failure'] contract_failures=13 recoverable=7 unrecoverable=6 first_gated=None mean_latency_ms=4609.0

## Expansion

- No expansion runs executed.

