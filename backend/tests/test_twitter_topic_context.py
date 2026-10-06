from types import SimpleNamespace

from app.services.twitter_topic_context import (
    OpenAITopicContextGenerator,
    TopicContextData,
)


def test_topic_context_uses_structured_responses_output():
    generator = OpenAITopicContextGenerator.__new__(OpenAITopicContextGenerator)
    generator.model = "gpt-test"
    calls = {}

    class FakeResponses:
        def parse(self, **kwargs):
            calls.update(kwargs)
            return SimpleNamespace(
                output_parsed=TopicContextData(
                    x_search_query='  "cheap LLM" OR "low cost inference"  ',
                    context_sentences=[
                        "People compare affordable hosted LLM APIs.",
                        "Developers discuss low token prices.",
                        "Teams seek inexpensive inference providers.",
                        "Posts evaluate budget language model hosting.",
                        "Builders balance model quality with inference cost.",
                    ],
                )
            )

    generator.client = SimpleNamespace(responses=FakeResponses())
    result = generator.generate("Cheap LLM Providers")

    assert result["x_search_query"] == '"cheap LLM" OR "low cost inference"'
    assert len(result["context_sentences"]) == 5
    assert calls["model"] == "gpt-test"
    assert calls["reasoning"] == {"effort": "none"}
    assert calls["text_format"] is TopicContextData
    assert calls["input"][1]["content"].endswith("Cheap LLM Providers")
