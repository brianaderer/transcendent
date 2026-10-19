"""What the report agent is asked (atlas plates 50, 60 and 70). Both versions get exactly
these words; the only difference between them is whether tools come with them."""

from dataclasses import dataclass
from datetime import date, timedelta

from pydantic import BaseModel, Field

from voices.comparison.commitment import NamedTopic, PredictedTopic
from voices.explore.day_range import DayRange

COMMUNITY = "r/sailing"
TOPICS_TO_NAME = "five to eight"


class Report(BaseModel):
    """The Community Voices Document, and the fixed list of its topics (atlas OPEN-25)."""

    document: str = Field(
        description="The document in Markdown: '## The period in brief' (one paragraph), then "
        "'## What the community talked about' with one '### ' section per topic (what it was, "
        "how it went, notable threads, and short quotes from real posts with the author and "
        "date where you have them)."
    )
    topics: list[NamedTopic] = Field(
        description="The topics your document covers, rank 1 the biggest, each with whether it "
        "was rising, steady, fading or new compared with the period just before."
    )


class Prediction(BaseModel):
    """The topics expected to lead the coming period, committed as a fixed list (OPEN-22)."""

    predicted: list[PredictedTopic] = Field(
        description="The topics you expect to be most discussed in the coming period, each with "
        "whether it will be rising, steady, fading or new."
    )
    reasoning: str = Field(description="Two or three sentences on what the forecast rests on.")


@dataclass(frozen=True)
class Task:
    phase: str  # "write" or "predict", for the live events
    instructions: str
    answer: type[BaseModel]  # the tool the answer comes back through


def write_task(days: DayRange) -> Task:
    instructions = f"""You write the Community Voices Document for {COMMUNITY}, the Reddit community
about sailing, for {_spoken(days.start)} to {_spoken(days.end)}.

Say what the community talked about in those days: name the {TOPICS_TO_NAME} main topics in
order of how much they were discussed, and for each, whether it was rising, steady, fading or
new compared with the same number of days just before. Be specific to this community and these
days. If you have tools, use them to ground what you write in the community's own posts.

Answer by calling Report once, with the document and its list of topics."""
    return Task("write", instructions, Report)


def predict_task(days: DayRange) -> Task:
    today = days.start - timedelta(days=1)
    instructions = f"""Today is {_spoken(today)}. Predict what {COMMUNITY}, the Reddit community
about sailing, will discuss most in the next {days.length} days ({_spoken(days.start)} to
{_spoken(days.end)}): name the {TOPICS_TO_NAME} topics you expect to lead, and for each, whether it
will be rising, steady, fading or new compared with the {days.length} days before. Brand-new
conversations can't be foreseen; forecast the ones already in motion. If you have tools, use
them: they show the community only up to today.

Answer by calling Prediction once."""
    return Task("predict", instructions, Prediction)


def _spoken(day: date) -> str:
    return f"{day.day} {day.strftime('%B %Y')}"
