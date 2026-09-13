from src.extractor import calculate_engagement, parse_metric_value


def test_parse_metric_value_simple():
    assert parse_metric_value("500") == 500
    assert parse_metric_value("0") == 0
    assert parse_metric_value("") == 0
    assert parse_metric_value(None) == 0


def test_parse_metric_value_units():
    assert parse_metric_value("1.5K") == 1500
    assert parse_metric_value("10K") == 10000
    assert parse_metric_value("2.3M") == 2300000
    assert parse_metric_value("1,250") == 1250


def test_calculate_engagement():
    eng = calculate_engagement(likes=100, reposts=50, views=1000, replies=10)
    assert eng.likes == 100
    assert eng.reposts == 50
    assert eng.views == 1000
    assert eng.replies == 10
    # Formula: likes + reposts + views
    assert eng.total_score == 1150
