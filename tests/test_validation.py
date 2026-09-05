"""
Tests for input validation, security, and edge cases.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from rmst_calc import calculate_metrics, process_batch, main
from agents.base import AuditTrail, PHIGuard, SecurityException


# =============================================================================
# calculate_metrics edge cases
# =============================================================================

class TestCalculateMetrics:
    def test_empty_params(self):
        """calculate_metrics with no params should return default score."""
        res = calculate_metrics()
        assert res["score"] == 1.0
        assert res["classification"] == "Low / Standard"

    def test_single_param(self):
        """Single parameter should be used as primary value."""
        res = calculate_metrics(v1=15.0)
        assert res["score"] == 15.0

    def test_multiple_params(self):
        """Multiple params should compute weighted sum."""
        res = calculate_metrics(v1=10.0, v2=4.0, v3=2.0)
        # score = 10.0 + 4.0/2 + 2.3 = 10.0 + 2.0 + 0.67 = 12.67
        assert res["score"] == round(10.0 + 4.0/2 + 2.0/3, 2)

    def test_none_params_skipped(self):
        """None values should be skipped."""
        res = calculate_metrics(v1=10.0, v2=None, v3=5.0)
        assert res["score"] == round(10.0 + 5.0/2, 2)

    def test_string_params_converted(self):
        """String params should be kept as strings, not included in numeric calc."""
        res = calculate_metrics(v1="hello", v2=10.0)
        # v1 becomes "hello" (string), v2 becomes 10.0 (float)
        assert res["score"] == 10.0

    def test_negative_values(self):
        """Negative values should work in calculation."""
        res = calculate_metrics(v1=-5.0, v2=3.0)
        assert res["score"] == round(-5.0 + 3.0/2, 2)

    def test_zero_values(self):
        """Zero values should be handled correctly."""
        res = calculate_metrics(v1=0.0, v2=0.0)
        assert res["score"] == 0.0
        assert res["classification"] == "Low / Standard"

    def test_classification_low(self):
        """Score < 10 should be Low / Standard."""
        res = calculate_metrics(v1=5.0)
        assert res["classification"] == "Low / Standard"
        assert "Standard monitoring" in res["clinical_recommendation"]

    def test_classification_moderate(self):
        """Score 10-25 should be Moderate / Intermediate."""
        res = calculate_metrics(v1=15.0)
        assert res["classification"] == "Moderate / Intermediate"
        assert "Close observation" in res["clinical_recommendation"]

    def test_classification_high(self):
        """Score >= 25 should be High / Severe."""
        res = calculate_metrics(v1=30.0)
        assert res["classification"] == "High / Severe"
        assert "Urgent clinical intervention" in res["clinical_recommendation"]

    def test_result_structure(self):
        """Result should have all expected keys."""
        res = calculate_metrics(v1=10.0)
        assert "tool" in res
        assert "score" in res
        assert "classification" in res
        assert "clinical_recommendation" in res
        assert "inputs_evaluated" in res


# =============================================================================
# process_batch validation
# =============================================================================

class TestProcessBatchValidation:
    def test_missing_file_raises_error(self, tmp_path):
        """Non-existent input file should raise FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            str(process_batch(str(tmp_path / "nonexistent.csv"), str(tmp_path / "out.csv")))

    def test_invalid_extension_raises_error(self, tmp_path):
        """Non-CSV file should raise ValueError."""
        bad_file = tmp_path / "data.txt"
        bad_file.write_text("test")
        with pytest.raises(ValueError, match="CSV or TSV"):
            process_batch(str(bad_file), str(tmp_path / "out.csv"))

    def test_empty_csv_raises_error(self, tmp_path):
        """Empty CSV file should raise ValueError."""
        empty = tmp_path / "empty.csv"
        empty.write_text("")
        with pytest.raises(ValueError, match="no headers"):
            process_batch(str(empty), str(tmp_path / "out.csv"))

    def test_headers_only_warns(self, tmp_path, capsys):
        """CSV with headers but no rows should warn but not error."""
        csv_in = tmp_path / "headers_only.csv"
        csv_out = tmp_path / "out.csv"
        csv_in.write_text("Patient_ID,v1,v2,v3\n")
        process_batch(str(csv_in), str(csv_out))
        captured = capsys.readouterr()
        assert "no data rows" in captured.out or "Warning" in captured.out

    def test_valid_batch_processing(self, tmp_path):
        """Valid CSV should process correctly."""
        csv_in = tmp_path / "valid.csv"
        csv_out = tmp_path / "out.csv"
        csv_in.write_text("Patient_ID,v1,v2,v3\nPT-001,10.0,5.0,2.0\n")
        process_batch(str(csv_in), str(csv_out))
        assert csv_out.exists()
        content = csv_out.read_text()
        assert "PT-001" in content
        assert "score" in content


# =============================================================================
# CLI error handling
# =============================================================================

class TestCLIErrorHandling:
    def test_batch_missing_file_exits_nonzero(self):
        """CLI batch with missing file should exit with code 1."""
        with pytest.raises(SystemExit) as exc_info:
            main(["batch", "-i", "nonexistent_file_12345.csv"])
        assert exc_info.value.code == 1

    def test_batch_invalid_extension_exits_nonzero(self, tmp_path):
        """CLI batch with invalid extension should exit with code 1."""
        bad_file = tmp_path / "data.json"
        bad_file.write_text("{}")
        with pytest.raises(SystemExit) as exc_info:
            main(["batch", "-i", str(bad_file)])
        assert exc_info.value.code == 1

    def test_single_default_values(self):
        """CLI single with defaults should work."""
        result = main(["single"])
        assert result is None  # process_single prints to stdout, returns None


# =============================================================================
# PHI Guard Security Tests
# =============================================================================

class TestPHIGuard:
    def test_mrn_detected(self):
        """MRN patterns should be detected."""
        with pytest.raises(SecurityException):
            PHIGuard.assert_no_phi("Patient MRN-12345678")

    def test_ssn_detected(self):
        """SSN patterns should be detected."""
        with pytest.raises(SecurityException):
            PHIGuard.assert_no_phi("SSN: 123-45-6789")

    def test_phone_detected(self):
        """Phone number patterns should be detected."""
        with pytest.raises(SecurityException):
            PHIGuard.assert_no_phi("Call (555) 123-4567")

    def test_email_detected(self):
        """Email patterns should be detected."""
        with pytest.raises(SecurityException):
            PHIGuard.assert_no_phi("Email: patient@hospital.org")

    def test_dob_detected(self):
        """Date of birth patterns should be detected."""
        with pytest.raises(SecurityException):
            PHIGuard.assert_no_phi("DOB: 01/15/1985")

    def test_patient_name_detected(self):
        """Patient name patterns should be detected."""
        with pytest.raises(SecurityException):
            PHIGuard.assert_no_phi("Patient John Smith admitted")

    def test_clean_text_passes(self):
        """Clean clinical text without PHI should pass."""
        PHIGuard.assert_no_phi("Specimen KEY-001 analytical result nominal")

    def test_empty_text_passes(self):
        """Empty text should pass."""
        PHIGuard.assert_no_phi("")

    def test_none_text_passes(self):
        """None text should pass."""
        PHIGuard.assert_no_phi(None)

    def test_redact_phi(self):
        """PHI should be redacted."""
        redacted = PHIGuard.redact_phi("Patient MRN-12345678 admitted")
        assert "MRN" not in redacted or "[REDACTED" in redacted


# =============================================================================
# Audit Trail Tests
# =============================================================================

class TestAuditTrail:
    def test_audit_trail_integrity(self):
        """Audit trail should maintain integrity."""
        trail = AuditTrail(secret_key="test-secret-key")
        trail.log("actor1", "tier1", "TEST_EVENT", {"data": "value1"})
        trail.log("actor2", "tier2", "TEST_EVENT", {"data": "value2"})
        assert trail.verify_integrity() is True

    def test_audit_trail_chain(self):
        """Audit trail entries should be chained."""
        trail = AuditTrail(secret_key="test-secret-key")
        trail.log("actor1", "tier1", "TEST_EVENT", {"data": "value1"})
        trail.log("actor2", "tier2", "TEST_EVENT", {"data": "value2"})
        logs = trail.get_trail()
        assert len(logs) == 2
        assert logs[1]["prev_hash"] == logs[0]["current_hash"]

    def test_audit_trail_empty(self):
        """Empty audit trail should verify as valid."""
        trail = AuditTrail(secret_key="test-secret-key")
        assert trail.verify_integrity() is True

    def test_audit_trail_tamper_detection(self):
        """Tampered audit trail should fail verification."""
        trail = AuditTrail(secret_key="test-secret-key")
        trail.log("actor1", "tier1", "TEST_EVENT", {"data": "value1"})
        trail.log("actor2", "tier2", "TEST_EVENT", {"data": "value2"})
        # Tamper with the first entry
        trail.logs[0]["current_hash"] = "TAMPERED"
        assert trail.verify_integrity() is False

    def test_audit_trail_phi_blocked(self):
        """Audit trail should reject PHI in details."""
        trail = AuditTrail(secret_key="test-secret-key")
        with pytest.raises(SecurityException):
            trail.log("actor1", "tier1", "TEST_EVENT", {"patient": "MRN-12345678"})
