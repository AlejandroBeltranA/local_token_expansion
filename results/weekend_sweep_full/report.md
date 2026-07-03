# Unified Weekend Sweep

## Baseline

- Mistral-7B-Instruct-v0.3: rec=abort triggers=['latency_cliff', 'over_expansion', 'persistent_failure'] contract_failures=4 recoverable=3 unrecoverable=1 first_gated=15 mean_latency_ms=6340.3
- Mistral-7B-Instruct-v0.3: rec=abort triggers=['latency_cliff', 'over_expansion', 'persistent_failure'] contract_failures=4 recoverable=3 unrecoverable=1 first_gated=15 mean_latency_ms=6309.4
- Mistral-7B-Instruct-v0.3: rec=abort triggers=['latency_cliff', 'over_expansion', 'persistent_failure'] contract_failures=4 recoverable=3 unrecoverable=1 first_gated=15 mean_latency_ms=6313.7
- Mistral-7B-Instruct-v0.3: rec=abort triggers=['latency_cliff', 'over_expansion', 'persistent_failure'] contract_failures=4 recoverable=3 unrecoverable=1 first_gated=15 mean_latency_ms=6285.2
- Mistral-7B-Instruct-v0.3: rec=abort triggers=['latency_cliff', 'over_expansion', 'persistent_failure'] contract_failures=4 recoverable=3 unrecoverable=1 first_gated=15 mean_latency_ms=6275.6
- Mistral-7B-Instruct-v0.3: rec=abort triggers=['latency_cliff', 'over_expansion', 'persistent_failure'] contract_failures=4 recoverable=3 unrecoverable=1 first_gated=15 mean_latency_ms=6283.9
- Meta-Llama-3.1-8B-Instruct-3bit: rec=escalate triggers=['context_decay', 'over_expansion'] contract_failures=9 recoverable=5 unrecoverable=4 first_gated=None mean_latency_ms=4440.5
- Meta-Llama-3.1-8B-Instruct-3bit: rec=escalate triggers=['context_decay', 'over_expansion'] contract_failures=9 recoverable=5 unrecoverable=4 first_gated=None mean_latency_ms=4419.9
- Meta-Llama-3.1-8B-Instruct-3bit: rec=escalate triggers=['context_decay', 'over_expansion'] contract_failures=9 recoverable=5 unrecoverable=4 first_gated=None mean_latency_ms=4439.6
- Meta-Llama-3.1-8B-Instruct-3bit: rec=escalate triggers=['context_decay', 'over_expansion'] contract_failures=9 recoverable=5 unrecoverable=4 first_gated=None mean_latency_ms=4426.7
- Meta-Llama-3.1-8B-Instruct-3bit: rec=escalate triggers=['context_decay', 'over_expansion'] contract_failures=9 recoverable=5 unrecoverable=4 first_gated=None mean_latency_ms=4422.7
- Meta-Llama-3.1-8B-Instruct-3bit: rec=escalate triggers=['context_decay', 'over_expansion'] contract_failures=9 recoverable=5 unrecoverable=4 first_gated=None mean_latency_ms=4425.5
- Phi-3-mini-4k-instruct-4bit: rec=abort triggers=['context_decay', 'near_cap_pressure', 'over_expansion', 'persistent_failure'] contract_failures=11 recoverable=8 unrecoverable=3 first_gated=None mean_latency_ms=5192.7
- Phi-3-mini-4k-instruct-4bit: rec=abort triggers=['context_decay', 'near_cap_pressure', 'over_expansion', 'persistent_failure'] contract_failures=11 recoverable=8 unrecoverable=3 first_gated=None mean_latency_ms=5270.3
- Phi-3-mini-4k-instruct-4bit: rec=abort triggers=['context_decay', 'near_cap_pressure', 'over_expansion', 'persistent_failure'] contract_failures=11 recoverable=8 unrecoverable=3 first_gated=None mean_latency_ms=5242.3
- Phi-3-mini-4k-instruct-4bit: rec=abort triggers=['context_decay', 'near_cap_pressure', 'over_expansion', 'persistent_failure'] contract_failures=11 recoverable=8 unrecoverable=3 first_gated=None mean_latency_ms=5226.0
- Phi-3-mini-4k-instruct-4bit: rec=abort triggers=['context_decay', 'near_cap_pressure', 'over_expansion', 'persistent_failure'] contract_failures=11 recoverable=8 unrecoverable=3 first_gated=None mean_latency_ms=5212.0
- Phi-3-mini-4k-instruct-4bit: rec=abort triggers=['context_decay', 'near_cap_pressure', 'over_expansion', 'persistent_failure'] contract_failures=11 recoverable=8 unrecoverable=3 first_gated=None mean_latency_ms=5213.3
- SmolLM-1.7B-Instruct-4bit: rec=abort triggers=['context_decay', 'near_cap_pressure', 'over_expansion', 'persistent_failure'] contract_failures=12 recoverable=6 unrecoverable=6 first_gated=None mean_latency_ms=2935.3
- SmolLM-1.7B-Instruct-4bit: rec=abort triggers=['context_decay', 'near_cap_pressure', 'over_expansion', 'persistent_failure'] contract_failures=12 recoverable=6 unrecoverable=6 first_gated=None mean_latency_ms=2916.0
- SmolLM-1.7B-Instruct-4bit: rec=abort triggers=['context_decay', 'near_cap_pressure', 'over_expansion', 'persistent_failure'] contract_failures=12 recoverable=6 unrecoverable=6 first_gated=None mean_latency_ms=2872.7
- SmolLM-1.7B-Instruct-4bit: rec=abort triggers=['context_decay', 'near_cap_pressure', 'over_expansion', 'persistent_failure'] contract_failures=12 recoverable=6 unrecoverable=6 first_gated=None mean_latency_ms=2919.7
- SmolLM-1.7B-Instruct-4bit: rec=abort triggers=['context_decay', 'near_cap_pressure', 'over_expansion', 'persistent_failure'] contract_failures=12 recoverable=6 unrecoverable=6 first_gated=None mean_latency_ms=2948.7
- SmolLM-1.7B-Instruct-4bit: rec=abort triggers=['context_decay', 'near_cap_pressure', 'over_expansion', 'persistent_failure'] contract_failures=12 recoverable=6 unrecoverable=6 first_gated=None mean_latency_ms=2955.0
- Phi-4-mini-instruct-8bit: rec=escalate triggers=['context_decay', 'over_expansion'] contract_failures=7 recoverable=4 unrecoverable=3 first_gated=None mean_latency_ms=2931.0
- Phi-4-mini-instruct-8bit: rec=escalate triggers=['context_decay', 'over_expansion'] contract_failures=7 recoverable=4 unrecoverable=3 first_gated=None mean_latency_ms=2913.1
- Phi-4-mini-instruct-8bit: rec=escalate triggers=['context_decay', 'over_expansion'] contract_failures=7 recoverable=4 unrecoverable=3 first_gated=None mean_latency_ms=2868.8
- Phi-4-mini-instruct-8bit: rec=escalate triggers=['context_decay', 'over_expansion'] contract_failures=7 recoverable=4 unrecoverable=3 first_gated=None mean_latency_ms=2852.5
- Phi-4-mini-instruct-8bit: rec=escalate triggers=['context_decay', 'over_expansion'] contract_failures=7 recoverable=4 unrecoverable=3 first_gated=None mean_latency_ms=2790.0
- Phi-4-mini-instruct-8bit: rec=escalate triggers=['context_decay', 'over_expansion'] contract_failures=7 recoverable=4 unrecoverable=3 first_gated=None mean_latency_ms=2845.9

## Expansion

- Mistral-7B-Instruct-v0.3 temp=0.5 max_tokens=128 seed=0: rec=abort triggers=['latency_cliff', 'over_expansion', 'persistent_failure'] contract_failures=4 recoverable=3 unrecoverable=1 first_gated=15 mean_latency_ms=6315.7
- Mistral-7B-Instruct-v0.3 temp=0.5 max_tokens=128 seed=1: rec=abort triggers=['latency_cliff', 'over_expansion', 'persistent_failure'] contract_failures=4 recoverable=3 unrecoverable=1 first_gated=15 mean_latency_ms=6276.4
- Mistral-7B-Instruct-v0.3 temp=0.5 max_tokens=128 seed=2: rec=abort triggers=['latency_cliff', 'over_expansion', 'persistent_failure'] contract_failures=4 recoverable=3 unrecoverable=1 first_gated=15 mean_latency_ms=6321.5
- Mistral-7B-Instruct-v0.3 temp=0.5 max_tokens=256 seed=0: rec=abort triggers=['latency_cliff', 'over_expansion', 'persistent_failure'] contract_failures=4 recoverable=3 unrecoverable=1 first_gated=15 mean_latency_ms=6284.7
- Mistral-7B-Instruct-v0.3 temp=0.5 max_tokens=256 seed=1: rec=abort triggers=['latency_cliff', 'over_expansion', 'persistent_failure'] contract_failures=4 recoverable=3 unrecoverable=1 first_gated=15 mean_latency_ms=6256.2
- Mistral-7B-Instruct-v0.3 temp=0.5 max_tokens=256 seed=2: rec=abort triggers=['latency_cliff', 'over_expansion', 'persistent_failure'] contract_failures=4 recoverable=3 unrecoverable=1 first_gated=15 mean_latency_ms=6253.2
- Meta-Llama-3.1-8B-Instruct-3bit temp=0.5 max_tokens=128 seed=0: rec=escalate triggers=['context_decay', 'over_expansion'] contract_failures=9 recoverable=5 unrecoverable=4 first_gated=None mean_latency_ms=4440.2
- Meta-Llama-3.1-8B-Instruct-3bit temp=0.5 max_tokens=128 seed=1: rec=escalate triggers=['context_decay', 'over_expansion'] contract_failures=9 recoverable=5 unrecoverable=4 first_gated=None mean_latency_ms=4427.2
- Meta-Llama-3.1-8B-Instruct-3bit temp=0.5 max_tokens=128 seed=2: rec=escalate triggers=['context_decay', 'over_expansion'] contract_failures=9 recoverable=5 unrecoverable=4 first_gated=None mean_latency_ms=4449.1
- Meta-Llama-3.1-8B-Instruct-3bit temp=0.5 max_tokens=256 seed=0: rec=escalate triggers=['context_decay', 'over_expansion'] contract_failures=9 recoverable=5 unrecoverable=4 first_gated=None mean_latency_ms=4493.6
- Meta-Llama-3.1-8B-Instruct-3bit temp=0.5 max_tokens=256 seed=1: rec=escalate triggers=['context_decay', 'over_expansion'] contract_failures=9 recoverable=5 unrecoverable=4 first_gated=None mean_latency_ms=4472.6
- Meta-Llama-3.1-8B-Instruct-3bit temp=0.5 max_tokens=256 seed=2: rec=escalate triggers=['context_decay', 'over_expansion'] contract_failures=9 recoverable=5 unrecoverable=4 first_gated=None mean_latency_ms=4468.8
- Phi-3-mini-4k-instruct-4bit temp=0.5 max_tokens=128 seed=0: rec=abort triggers=['context_decay', 'near_cap_pressure', 'over_expansion', 'persistent_failure'] contract_failures=11 recoverable=8 unrecoverable=3 first_gated=None mean_latency_ms=5195.0
- Phi-3-mini-4k-instruct-4bit temp=0.5 max_tokens=128 seed=1: rec=abort triggers=['context_decay', 'near_cap_pressure', 'over_expansion', 'persistent_failure'] contract_failures=11 recoverable=8 unrecoverable=3 first_gated=None mean_latency_ms=5288.0
- Phi-3-mini-4k-instruct-4bit temp=0.5 max_tokens=128 seed=2: rec=abort triggers=['context_decay', 'near_cap_pressure', 'over_expansion', 'persistent_failure'] contract_failures=11 recoverable=8 unrecoverable=3 first_gated=None mean_latency_ms=5161.3
- Phi-3-mini-4k-instruct-4bit temp=0.5 max_tokens=256 seed=0: rec=abort triggers=['context_decay', 'near_cap_pressure', 'over_expansion', 'persistent_failure'] contract_failures=11 recoverable=8 unrecoverable=3 first_gated=None mean_latency_ms=5149.7
- Phi-3-mini-4k-instruct-4bit temp=0.5 max_tokens=256 seed=1: rec=abort triggers=['context_decay', 'near_cap_pressure', 'over_expansion', 'persistent_failure'] contract_failures=11 recoverable=8 unrecoverable=3 first_gated=None mean_latency_ms=5156.3
- Phi-3-mini-4k-instruct-4bit temp=0.5 max_tokens=256 seed=2: rec=abort triggers=['context_decay', 'near_cap_pressure', 'over_expansion', 'persistent_failure'] contract_failures=11 recoverable=8 unrecoverable=3 first_gated=None mean_latency_ms=5154.3
- SmolLM-1.7B-Instruct-4bit temp=0.5 max_tokens=128 seed=0: rec=abort triggers=['context_decay', 'near_cap_pressure', 'over_expansion', 'persistent_failure'] contract_failures=12 recoverable=6 unrecoverable=6 first_gated=None mean_latency_ms=2772.3
- SmolLM-1.7B-Instruct-4bit temp=0.5 max_tokens=128 seed=1: rec=abort triggers=['context_decay', 'near_cap_pressure', 'over_expansion', 'persistent_failure'] contract_failures=12 recoverable=6 unrecoverable=6 first_gated=None mean_latency_ms=2759.3
- SmolLM-1.7B-Instruct-4bit temp=0.5 max_tokens=128 seed=2: rec=abort triggers=['context_decay', 'near_cap_pressure', 'over_expansion', 'persistent_failure'] contract_failures=12 recoverable=6 unrecoverable=6 first_gated=None mean_latency_ms=2763.0
- SmolLM-1.7B-Instruct-4bit temp=0.5 max_tokens=256 seed=0: rec=abort triggers=['context_decay', 'near_cap_pressure', 'over_expansion', 'persistent_failure'] contract_failures=12 recoverable=6 unrecoverable=6 first_gated=None mean_latency_ms=2834.0
- SmolLM-1.7B-Instruct-4bit temp=0.5 max_tokens=256 seed=1: rec=abort triggers=['context_decay', 'near_cap_pressure', 'over_expansion', 'persistent_failure'] contract_failures=12 recoverable=6 unrecoverable=6 first_gated=None mean_latency_ms=2829.0
- SmolLM-1.7B-Instruct-4bit temp=0.5 max_tokens=256 seed=2: rec=abort triggers=['context_decay', 'near_cap_pressure', 'over_expansion', 'persistent_failure'] contract_failures=12 recoverable=6 unrecoverable=6 first_gated=None mean_latency_ms=2827.0
- Phi-4-mini-instruct-8bit temp=0.5 max_tokens=128 seed=0: rec=escalate triggers=['context_decay', 'over_expansion'] contract_failures=7 recoverable=4 unrecoverable=3 first_gated=None mean_latency_ms=2836.1
- Phi-4-mini-instruct-8bit temp=0.5 max_tokens=128 seed=1: rec=escalate triggers=['context_decay', 'over_expansion'] contract_failures=7 recoverable=4 unrecoverable=3 first_gated=None mean_latency_ms=2845.0
- Phi-4-mini-instruct-8bit temp=0.5 max_tokens=128 seed=2: rec=escalate triggers=['context_decay', 'over_expansion'] contract_failures=7 recoverable=4 unrecoverable=3 first_gated=None mean_latency_ms=2818.0
- Phi-4-mini-instruct-8bit temp=0.5 max_tokens=256 seed=0: rec=escalate triggers=['context_decay', 'over_expansion'] contract_failures=7 recoverable=4 unrecoverable=3 first_gated=None mean_latency_ms=2810.8
- Phi-4-mini-instruct-8bit temp=0.5 max_tokens=256 seed=1: rec=escalate triggers=['context_decay', 'over_expansion'] contract_failures=7 recoverable=4 unrecoverable=3 first_gated=None mean_latency_ms=2817.5
- Phi-4-mini-instruct-8bit temp=0.5 max_tokens=256 seed=2: rec=escalate triggers=['context_decay', 'over_expansion'] contract_failures=7 recoverable=4 unrecoverable=3 first_gated=None mean_latency_ms=2864.0

