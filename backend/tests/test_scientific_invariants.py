"""Tests for strict scientific invariant enforcement."""

import pytest
from httpx import AsyncClient


class TestScientificInvariants:
    """Verify scientific invariants and honesty caveats."""

    @pytest.mark.asyncio
    async def test_boundary_caveat_enforcement(self, client: AsyncClient, seed_experiment):
        """Invariant 1: Boundary metrics MUST include mandated disclaimer."""
        response = await client.get("/api/experiments/EXP-0241")
        assert response.status_code == 200
        data = response.json()

        results = data.get("results")
        assert results is not None

        # Check observedBoundary
        if results.get("observedBoundary") is not None:
            # Must have either observedBoundaryLabel or observed_boundary_caveat with exact text
            disclaimer = "Observed failure boundary under the specified experimental configuration."
            assert (
                results.get("observedBoundaryLabel") == disclaimer
                or results.get("observed_boundary_caveat") == disclaimer
            )

    @pytest.mark.asyncio
    async def test_feature_sensitivity_caveat_enforcement(self, client: AsyncClient, seed_experiment):
        """Invariant 2: Feature sensitivities MUST include mandated caveat."""
        response = await client.get("/api/experiments/EXP-0241")
        assert response.status_code == 200
        data = response.json()

        results = data.get("results")
        assert results is not None
        vulns = results.get("featureVulnerabilities") or []
        assert len(vulns) > 0

        expected_caveat = "Empirical sensitivity — not a causal explanation."
        for item in vulns:
            assert "caveat" in item
            assert item["caveat"] == expected_caveat

    @pytest.mark.asyncio
    async def test_no_aggregate_robustness_score_or_grade(self, client: AsyncClient, seed_experiment):
        """Invariant 3: NO aggregate robustness score, letter grade, or subjective rating in any response."""
        response = await client.get("/api/experiments")
        assert response.status_code == 200
        data = response.json()

        forbidden_keys = [
            "robustness_score",
            "robustnessScore",
            "overall_score",
            "overallScore",
            "letter_grade",
            "letterGrade",
            "grade",
            "rating",
            "subjective_rating",
            "subjectiveRating",
        ]

        def check_no_forbidden_keys(obj, path=""):
            if isinstance(obj, dict):
                for k, v in obj.items():
                    for forbidden in forbidden_keys:
                        assert k.lower() != forbidden.lower(), f"Forbidden key '{k}' found at {path}"
                    check_no_forbidden_keys(v, f"{path}.{k}")
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    check_no_forbidden_keys(item, f"{path}[{i}]")

        check_no_forbidden_keys(data)

