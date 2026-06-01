| Model | Pair | Exchanges | Consensus | Avg Sentiment | Distinct-1 | Sem Div |
|-------|------|:---------:|:---------:|:-------------:|:----------:|:-------:|
| dolphin-mistral:7b | Israel / Palestine | 20 | ❌ | 0.469 | 0.103 | 0.253 |
| dolphin-mistral:7b | Turkey / Armenia | 3 | ✅ | 0.211 | 0.264 | 0.139 |
| dolphin-mistral:7b | Tutsi / Hutu (Rwanda) | 3 | ✅ | 0.201 | 0.269 | 0.199 |
| gemma2:9b | Israel / Palestine | 4 | ✅ | -0.026 | 0.272 | 0.381 |
| gemma2:9b | Turkey / Armenia | 4 | ✅ | -0.016 | 0.333 | 0.336 |
| gemma2:9b | Tutsi / Hutu (Rwanda) | 5 | ✅ | -0.058 | 0.258 | 0.326 |
| llama3.1:8b | Israel / Palestine | 4 | ✅ | 0.145 | 0.244 | 0.294 |
| llama3.1:8b | Turkey / Armenia | 3 | ✅ | -0.011 | 0.278 | 0.311 |
| llama3.1:8b | Tutsi / Hutu (Rwanda) | 4 | ✅ | 0.104 | 0.241 | 0.346 |
| mistral:7b | Israel / Palestine | 9 | ✅ | 0.394 | 0.113 | 0.207 |
| mistral:7b | Turkey / Armenia | 3 | ✅ | 0.452 | 0.288 | 0.185 |
| mistral:7b | Tutsi / Hutu (Rwanda) | 10 | ✅ | 0.477 | 0.097 | 0.097 |
| qwen2.5:7b | Israel / Palestine | 4 | ✅ | 0.251 | 0.212 | 0.346 |
| qwen2.5:7b | Turkey / Armenia | 8 | ✅ | 0.203 | 0.095 | 0.158 |
| qwen2.5:7b | Tutsi / Hutu (Rwanda) | 4 | ✅ | 0.163 | 0.173 | 0.160 |

## Consensus

![Consensus heatmap](plots/consensus_heatmap.png)

## Sentiment (VADER)

![Sentiment heatmap](plots/sentiment_heatmap.png)

## Topic Drift

![Topic drift curves](plots/topic_drift_curves.png)

## Distinct-1 (Lexical Diversity)

![Distinct-1 heatmap](plots/distinct1_heatmap.png)

## Semantic Diversity

![Semantic diversity heatmap](plots/sem_div_heatmap.png)

## Verbosity


![Verbosity chart](plots/verbosity_ratio.png)

## LLM Judge Scores

### Hostility

![hostility](plots/judge_hostility_heatmap.png)

### Stereotyping

![stereotyping](plots/judge_stereotyping_heatmap.png)

### Topic Adherence

![topic_adherence](plots/judge_topic_adherence_heatmap.png)