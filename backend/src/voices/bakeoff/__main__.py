"""python -m voices.bakeoff [model ...] runs the bake-off and prints the results page.

With no models named it compares Claude Haiku 5.5 and Claude Sonnet 5.5. It calls the real
models through OpenRouter, so it needs OPENROUTER_API_KEY and spends money (about 20 cents
for the two default models).
"""

import sys
from datetime import date

from voices.bakeoff.live import run_live_bakeoff
from voices.bakeoff.report import render_report
from voices.bakeoff.sample import load_sample_data

DEFAULT_MODELS = ["anthropic/claude-haiku-5.5", "anthropic/claude-sonnet-5.5"]


def main(model_names: list[str]) -> None:
    sample = load_sample_data()
    results = run_live_bakeoff(model_names, sample)
    print(render_report(results, sample, date.today()))


if __name__ == "__main__":
    main(sys.argv[1:] or DEFAULT_MODELS)
