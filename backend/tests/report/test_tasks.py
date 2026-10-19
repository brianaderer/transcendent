from datetime import date

from voices.explore.day_range import DayRange
from voices.report.tasks import predict_task, write_task

DAYS = DayRange(date(2026, 10, 12), date(2026, 10, 18))


def test_the_report_names_the_community_and_the_range_and_asks_for_the_fixed_list():
    task = write_task(DAYS)

    assert "r/sailing" in task.instructions
    assert "12 October 2026" in task.instructions and "18 October 2026" in task.instructions
    assert task.answer.__name__ == "Report"


def test_the_prediction_is_made_as_of_the_day_before_the_range():
    task = predict_task(DAYS)

    assert "11 October 2026" in task.instructions
    assert "7 days" in task.instructions
    assert task.answer.__name__ == "Prediction"


def test_both_tasks_say_to_work_from_the_posts_the_tools_show_and_be_honest_where_thin():
    for task in (write_task(DAYS), predict_task(DAYS)):
        assert "what you can see in the community's posts with your tools" in task.instructions
        assert "what you know of this community and the season" in task.instructions
        assert "say plainly where your evidence is thin" in task.instructions


def test_neither_task_suggests_the_model_might_have_no_tools():
    for task in (write_task(DAYS), predict_task(DAYS)):
        assert "no tools" not in task.instructions
        assert "If you have tools" not in task.instructions


def test_the_report_asks_where_each_topic_is_heading_next_and_why():
    assert "where it looks to be heading next, and why" in write_task(DAYS).instructions
