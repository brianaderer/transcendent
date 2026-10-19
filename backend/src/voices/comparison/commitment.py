"""What a report commits to beside its prose (atlas OPEN-25): its topics, each with a rank
and a direction, and the topics it expects to be prominent. This list is what gets scored."""

from pydantic import BaseModel

from voices.explore.direction import Direction


class NamedTopic(BaseModel):
    name: str
    rank: int  # 1 is the biggest
    direction: Direction


class PredictedTopic(BaseModel):
    name: str
    direction: Direction


class Commitment(BaseModel):
    topics: list[NamedTopic]
    predicted: list[PredictedTopic]

    def topic_names(self) -> list[str]:
        return [t.name for t in self.topics]

    def predicted_names(self) -> list[str]:
        return [p.name for p in self.predicted]
