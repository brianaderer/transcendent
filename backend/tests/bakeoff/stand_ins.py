"""Stand-in chat models for the bake-off tests: each answers every case the same way."""

from langchain_core.messages import AIMessage

USAGE = {"input_tokens": 1000, "output_tokens": 100, "total_tokens": 1100}


def decision_call(arguments):
    call = {"name": "Decision", "args": arguments, "id": "1"}
    return AIMessage(content="", tool_calls=[call], usage_metadata=USAGE)


class Answers:
    def __init__(self, **arguments):
        self.arguments = {"reason": "Stand-in.", **arguments}

    def bind_tools(self, tools):
        return self

    def invoke(self, messages):
        return decision_call(self.arguments)


class AlwaysAttachesToTheft:
    def bind_tools(self, tools):
        return self

    def invoke(self, messages):
        arguments = {"action": "attach", "topic_id": 1, "reason": "Theft."}
        call = {"name": "Decision", "args": arguments, "id": "1"}
        return AIMessage(content="", tool_calls=[call], usage_metadata=USAGE)


class NeverDecides:
    def bind_tools(self, tools):
        return self

    def invoke(self, messages):
        return AIMessage(content="hmm", usage_metadata=USAGE)
