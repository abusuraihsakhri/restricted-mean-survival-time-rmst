"""Reference calculations for unadjusted Kaplan–Meier RMST."""
import csv
import json
import pytest

from rmst_calc import calculate_metrics, main, process_batch, read_observations

SAMPLE = [
    {"time": 2, "event": 1, "group": "A"},
    {"time": 4, "event": 0, "group": "A"},
    {"time": 6, "event": 1, "group": "A"},
    {"time": 8, "event": 1, "group": "A"},
    {"time": 10, "event": 0, "group": "A"},
    {"time": 3, "event": 1, "group": "B"},
    {"time": 5, "event": 0, "group": "B"},
    {"time": 7, "event": 1, "group": "B"},
    {"time": 9, "event": 0, "group": "B"},
    {"time": 10, "event": 0, "group": "B"},
]


def test_two_group_reference_result():
    result = calculate_metrics(SAMPLE, tau=10)
    assert result["groups"]["A"]["rmst"] == pytest.approx(6.8)
    assert result["groups"]["B"]["rmst"] == pytest.approx(7.8)
    assert result["groups"]["A"]["rmtl"] == pytest.approx(3.2)
    assert result["contrast"]["difference"] == pytest.approx(1)
    assert result["contrast"]["ratio"] == pytest.approx(7.8 / 6.8)
    assert result["contrast"]["direction"] == "B minus A"


def test_tied_event_and_censor():
    rows = [{"time": 2, "event": 1}, {"time": 2, "event": 0}, {"time": 4, "event": 1}]
    result = calculate_metrics(rows, tau=4)
    assert result["groups"]["All"]["rmst"] == pytest.approx(2 + 2 * (2 / 3))
    assert result["groups"]["All"]["curve"][1]["survival"] == pytest.approx(2 / 3)


def test_no_events():
    rows = [{"time": 3, "event": 0}, {"time": 5, "event": 0}]
    result = calculate_metrics(rows, 5)
    assert result["groups"]["All"]["rmst"] == 5
    assert result["groups"]["All"]["rmtl"] == 0


def test_event_at_time_zero():
    assert calculate_metrics([{"time": 0, "event": 1}, {"time": 4, "event": 0}], 4)["groups"]["All"]["rmst"] == pytest.approx(2)


def test_csv_and_tsv(tmp_path):
    for extension, sep in (("csv", ","), ("tsv", "\t")):
        inp = tmp_path / f"observations.{extension}"
        inp.write_text("time"+sep+"event"+sep+"group\n2"+sep+"1"+sep+"A\n4"+sep+"0"+sep+"A\n", encoding="utf-8")
        result = process_batch(str(inp), str(tmp_path / f"summary-{extension}.csv"), 4)
        assert result["groups"]["A"]["rmst"] == pytest.approx(3)
        with (tmp_path / f"summary-{extension}.csv").open() as stream:
            rows = list(csv.DictReader(stream))
        assert len(rows) == 1 and rows[0]["group"] == "A"
        assert float(rows[0]["rmst"]) == pytest.approx(3)


def test_inline_cli(capsys):
    assert main(["single","--times","2","4","--events","1","0","--tau","4"]) == 0
    assert json.loads(capsys.readouterr().out)["groups"]["All"]["rmst"] == pytest.approx(3)


def test_api_endpoint_without_network():
    from agents.api import RmstRequest, SurvivalObservation, api_rmst
    rows = [SurvivalObservation(time=2, event=1),
            SurvivalObservation(time=4, event=0)]
    result = api_rmst(RmstRequest(tau=4, observations=rows))
    assert result["groups"]["All"]["rmst"] == pytest.approx(3)


def test_legacy_batch_false_flag_is_not_truthy(tmp_path):
    from cli import main as audit_main
    source = tmp_path / "audit.csv"
    output = tmp_path / "audit-out.csv"
    source.write_text(
        "task_id,target_identifier,primary_metric,secondary_metric,status_descriptor,is_critical_flag\n"
        "T1,KEY-01,10,0,NOMINAL,False\n", encoding="utf-8"
    )
    assert audit_main(["batch", "-i", str(source), "-o", str(output)]) == 0
    with output.open(newline="") as stream:
        row = next(csv.DictReader(stream))
    assert row["overall_urgency"] == "ROUTINE"
