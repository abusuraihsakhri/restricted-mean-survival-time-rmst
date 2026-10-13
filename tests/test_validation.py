"""Failure modes and validation for Kaplan–Meier RMST, security and CLI."""
import pytest
from rmst_calc import calculate_metrics, process_batch, main, read_observations
from agents.base import AuditTrail, PHIGuard, SecurityException


@pytest.mark.parametrize("rows,tau,match", [
    ([], 5, "observation"),
    ([{"time": 1, "event": 1}], 0, "tau"),
    ([{"time": 1, "event": 1}], float("nan"), "finite"),
    ([{"time": 1, "event": 1}], 2, "exceeds"),
    ([{"time": -1, "event": 1}], 1, "negative"),
    ([{"time": float("inf"), "event": 1}], 2, "finite"),
    ([{"time": 1, "event": "yes"}], 1, "event"),
    ([{"time": 1, "event": 2}], 1, "event"),
    ([{"time": 1, "event": 1, "group": ""}], 1, "group"),
    ([{"time": 1, "event": 1, "group": "A"},
      {"time": 1, "event": 1, "group": "B"},
      {"time": 1, "event": 1, "group": "C"}], 1, "two groups"),
    ([{"time": 1, "event": 1, "group": "A"},
      {"time": 3, "event": 0, "group": "B"}], 2, "group"),
])
def test_invalid_input(rows, tau, match):
    with pytest.raises(ValueError, match=match):
        calculate_metrics(rows, tau)


def test_invalid_csv_paths(tmp_path):
    with pytest.raises(FileNotFoundError):
        process_batch(str(tmp_path / "missing.csv"), str(tmp_path / "out.csv"), 3)
    invalid = tmp_path / "input.txt"
    invalid.write_text("time,event\n2,1\n")
    with pytest.raises(ValueError, match="CSV or TSV"):
        read_observations(invalid)
    empty = tmp_path / "empty.csv"
    empty.write_text("")
    with pytest.raises(ValueError, match="columns"):
        read_observations(empty)
    malformed = tmp_path / "malformed.csv"
    malformed.write_text("time,event\n2,1,extra\n")
    with pytest.raises(ValueError, match="too many fields"):
        read_observations(malformed)
    with pytest.raises(ValueError, match="differ"):
        process_batch(str(malformed), str(malformed), 2)


def test_cli_error_codes(tmp_path, capsys):
    assert main(["batch","-i",str(tmp_path / "no.csv"),"--tau","3"]) == 1
    assert "Error:" in capsys.readouterr().err
    assert main(["single","--times","1","2","--events","1","--tau","2"]) == 1
    assert main(["single","--times","1","--events","1","--tau","2"]) == 1


@pytest.mark.parametrize("text", [
    "Patient MRN-12345678",
    "SSN: 123-45-6789",
    "Call (555) 123-4567",
    "Email: patient@hospital.org",
    "DOB: 01/15/1985",
    "Patient John Smith admitted",
])
def test_phi_pattern_guard(text):
    with pytest.raises(SecurityException):
        PHIGuard.assert_no_phi(text)


def test_audit_integrity_and_last_entry_tamper():
    trail = AuditTrail(secret_key="test-key")
    trail.log("actor", "tier", "EVENT", {"data": 1})
    trail.log("actor", "tier", "EVENT", {"data": 2})
    assert trail.verify_integrity()
    trail.logs[-1]["event_type"] = "ALTERED"
    assert not trail.verify_integrity()


def test_audit_phi_guard():
    trail = AuditTrail(secret_key="test-key")
    with pytest.raises(SecurityException):
        trail.log("actor", "tier", "EVENT", {"patient": "MRN-12345678"})
