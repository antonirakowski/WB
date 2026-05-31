"""
Telephone game experiment — v2 (heated argument format).

Changes vs v1 telephone:
- Starting message: provocative contested claim instead of neutral factual statement
- Hop prompt: "Respond to this claim in your own words" instead of neutral restate
- Personas stripped of "structured debate" framing
- phi3.5 excluded (confirmed broken)
"""

import json
import time
from datetime import datetime
from pathlib import Path

import ollama
from tqdm import tqdm

from personas import PAIRS
from experiment_v2 import MODELS, PROVOCATIONS, strip_debate_framing

RESULTS_DIR = Path("results_telephone_v2")
CHAIN_LENGTH = 6
TEMPERATURE = 0.7
NUM_CTX = 2048

HOP_PROMPT = (
    "The following claim has been made about a conflict that is part of your history. "
    "Restate it in your own words, as someone with your background would understand "
    "and tell it. Don't hold back:\n\n{message}"
)


def chat(model: str, system: str, user: str) -> str:
    response = ollama.chat(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        options={"temperature": TEMPERATURE, "num_ctx": NUM_CTX},
    )
    return response["message"]["content"].strip()


def run_chain(model: str, pair_key: str, pair: dict) -> dict:
    a = pair["agent_a"]
    b = pair["agent_b"]
    original = PROVOCATIONS[pair_key]
    agents = [a if i % 2 == 0 else b for i in range(CHAIN_LENGTH)]

    chain = []
    current_message = original

    for hop_idx, agent in enumerate(agents):
        t0 = time.time()
        response = chat(
            model=model,
            system=strip_debate_framing(agent["system"]),
            user=HOP_PROMPT.format(message=current_message),
        )
        elapsed = time.time() - t0

        chain.append({
            "hop": hop_idx,
            "agent_id": agent["id"],
            "name": agent["name"],
            "received": current_message,
            "text": response,
            "elapsed_s": round(elapsed, 2),
        })
        current_message = response

    return {
        "model": model,
        "pair": pair_key,
        "pair_label": pair["pair_label"],
        "agent_a_id": a["id"],
        "agent_b_id": b["id"],
        "original_message": original,
        "chain_length": CHAIN_LENGTH,
        "timestamp": datetime.utcnow().isoformat(),
        "chain": chain,
    }


def save_result(result: dict) -> Path:
    RESULTS_DIR.mkdir(exist_ok=True)
    model_safe = result["model"].replace(":", "_").replace(".", "_")
    fname = RESULTS_DIR / f"{model_safe}__{result['pair']}.json"
    fname.write_text(json.dumps(result, indent=2, ensure_ascii=False))
    return fname


def pull_if_needed(model: str) -> None:
    try:
        ollama.show(model)
    except ollama.ResponseError:
        print(f"  Pulling {model}...")
        ollama.pull(model)


def main() -> None:
    total = len(MODELS) * len(PAIRS)
    print(f"Telephone v2 (heated): {total} chains | {CHAIN_LENGTH} hops each\n")

    with tqdm(total=total, unit="chain") as bar:
        for model in MODELS:
            pull_if_needed(model)
            for pair_key, pair in PAIRS.items():
                bar.set_description(f"{model} | {pair['pair_label']}")

                model_safe = model.replace(":", "_").replace(".", "_")
                out_path = RESULTS_DIR / f"{model_safe}__{pair_key}.json"
                if out_path.exists():
                    bar.set_postfix(status="skipped")
                    bar.update(1)
                    continue

                try:
                    result = run_chain(model, pair_key, pair)
                    path = save_result(result)
                    bar.set_postfix(file=path.name)
                except Exception as e:
                    bar.write(f"ERROR {model} / {pair_key}: {e}")
                bar.update(1)

    print("\nDone. Results in ./results_telephone_v2/")


if __name__ == "__main__":
    main()
