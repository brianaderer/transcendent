"""What the report agent is asked (atlas plates 50, 60 and 70). Both versions get exactly
these words; the only difference between them is the tools that come with them: version A's
reading a few posts, version B's retrieval (OPEN-39)."""

from dataclasses import dataclass
from datetime import date, timedelta

from pydantic import BaseModel, Field

from voices.comparison.commitment import NamedTopic, PredictedTopic
from voices.explore.day_range import DayRange
from voices.reddit_links import SUBREDDIT

COMMUNITY = f"r/{SUBREDDIT}"
TOPICS_TO_NAME = "five to eight"


class Report(BaseModel):
    """The Community Voices Document, and the fixed list of its topics (atlas OPEN-25)."""

    document: str = Field(
        description="The document in Markdown: '## The period in brief' (one paragraph), then "
        "'## What the community talked about' with one '### ' section per topic (what it was, "
        "how it went, notable threads, and short quotes from real posts with the author and "
        "date where you have them, each quote a Markdown link to its post: [quote](link), "
        "using the post's link exactly as the tools gave it)."
    )
    topics: list[NamedTopic] = Field(
        description="The topics your document covers, rank 1 the biggest, each with whether it "
        "was rising, steady, fading or new: its momentum within the period, the second half "
        "against the first."
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


# The same promise for both tasks and both versions: write concretely from whatever the tools
# show (A's reading, B's searches) and be honest about how much that is.
FROM_WHAT_YOU_CAN_SEE = (
    "what you can see in the community's posts with your tools, and from what you know of "
    "this community and the season; say plainly where your evidence is thin"
)


def write_task(days: DayRange) -> Task:
    instructions = f"""You write the Community Voices Document for {COMMUNITY}, the Reddit community
about sailing, for {_spoken(days.start)} to {_spoken(days.end)}.

Say what the community talked about in those days: name the {TOPICS_TO_NAME} main topics in
order of how much they were discussed, and for each, whether it was rising, steady or fading
within those days (growing toward their end, holding, or dying away), or new. For each
topic, also say where it looks to be heading next, and why. Be specific to this community
and these days. Write the document from {FROM_WHAT_YOU_CAN_SEE}.

Answer by calling Report once, with the document and its list of topics."""
    return Task("write", instructions, Report)


def predict_task(days: DayRange) -> Task:
    today = days.start - timedelta(days=1)
    instructions = f"""Today is {_spoken(today)}. Predict what {COMMUNITY}, the Reddit community
about sailing, will discuss most in the next {days.length} days ({_spoken(days.start)} to
{_spoken(days.end)}): name the {TOPICS_TO_NAME} topics you expect to lead, and for each, whether it
will be rising, steady or fading through those days (growing toward their end, holding, or
dying away), or new. Brand-new
conversations can't be foreseen; forecast the ones already in motion. Your tools show the
community only up to today. Make the prediction from {FROM_WHAT_YOU_CAN_SEE}.

Answer by calling Prediction once."""
    return Task("predict", instructions, Prediction)


def _spoken(day: date) -> str:
    return f"{day.day} {day.strftime('%B %Y')}"
