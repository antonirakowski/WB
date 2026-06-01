| Model | Pair | Mean Drift | Final Drift | Avg Sentiment | Distinct-1 |
|-------|------|:----------:|:-----------:|:-------------:|:----------:|
| dolphin-mistral:7b | Israel / Palestine | 0.239 | 0.272 | -0.211 | 0.301 |
| dolphin-mistral:7b | Turkey / Armenia | 0.203 | 0.125 | -0.352 | 0.391 |
| dolphin-mistral:7b | Tutsi / Hutu (Rwanda) | 0.127 | 0.121 | -0.312 | 0.294 |
| gemma2:9b | Israel / Palestine | 0.493 | 0.537 | 0.029 | 0.224 |
| gemma2:9b | Turkey / Armenia | 0.482 | 0.569 | 0.011 | 0.306 |
| gemma2:9b | Tutsi / Hutu (Rwanda) | 0.478 | 0.503 | -0.087 | 0.202 |
| llama3.1:8b | Israel / Palestine | 0.561 | 0.665 | 0.004 | 0.221 |
| llama3.1:8b | Turkey / Armenia | 0.362 | 0.429 | 0.100 | 0.291 |
| llama3.1:8b | Tutsi / Hutu (Rwanda) | 0.501 | 0.613 | -0.012 | 0.206 |
| mistral:7b | Israel / Palestine | 0.469 | 0.564 | -0.170 | 0.263 |
| mistral:7b | Turkey / Armenia | 0.259 | 0.297 | -0.341 | 0.284 |
| mistral:7b | Tutsi / Hutu (Rwanda) | 0.351 | 0.781 | -0.415 | 0.391 |
| phi3.5:3.8b | Israel / Palestine | 0.490 | 0.577 | -0.053 | 0.265 |
| phi3.5:3.8b | Turkey / Armenia | 0.684 | 0.979 | 0.271 | 0.278 |
| phi3.5:3.8b | Tutsi / Hutu (Rwanda) | 0.971 | 0.916 | 0.202 | 0.625 |
| qwen2.5:7b | Israel / Palestine | 0.334 | 0.353 | 0.246 | 0.197 |
| qwen2.5:7b | Turkey / Armenia | 0.198 | 0.269 | 0.155 | 0.246 |
| qwen2.5:7b | Tutsi / Hutu (Rwanda) | 0.330 | 0.692 | -0.134 | 0.255 |

## Semantic Drift per Hop

![Drift curves](plots/drift_curves.png)

![Drift heatmap](plots/drift_heatmap.png)

## Drift by Agent Group

![Drift by agent](plots/drift_by_agent.png)

## Sentiment Evolution

![Sentiment evolution](plots/sentiment_evolution.png)

## Distinct-1 per Hop Agent

![Distinct-1 heatmap](plots/distinct1_heatmap.png)

## LLM Judge Scores

### Hostility

![hostility](plots/judge_hostility_heatmap.png)

### Stereotyping

![stereotyping](plots/judge_stereotyping_heatmap.png)

### Topic Adherence

![topic_adherence](plots/judge_topic_adherence_heatmap.png)