#!/usr/bin/env python3
"""
Editorial Reviewer Agent

LLM-assisted agent that validates proposals through defined gates.
Can auto-approve proposals that pass all gates, or flag for manual review.

Validation Gates:
1. Schema validation - fields match expected types
2. Provenance check - claims have sources
3. URL verification - signup URLs work
4. Policy check - no malicious content
5. Consistency check - doesn't contradict other data
"""
from __future__ import annotations

import json
import os
import re
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from typing import Any

import requests


# ============================================
# Configuration
# ============================================

DEFAULT_API_BASE = "http://localhost:8120"
DEFAULT_REVIEWER_KEY = "ak_reviewer_default"

# Valid field types and patterns
FIELD_SCHEMA = {
    "commission_rate": {"type": str, "pattern": r"^\d+[\d.,]*%?.*$|^Unknown$"},
    "cookie_duration_days": {"type": int, "min": 0, "max": 365},
    "payout_model": {"type": str, "allowed": ["CPA", "CPS", "CPL", "RevShare", "Recurring", "Hybrid", "PPS", "PPL"]},
    "minimum_payout": {"type": str, "pattern": r"^\$?\d+.*$|^Unknown$"},
    "payment_methods": {"type": list},
    "payment_frequency": {"type": str},
    "tracking_platform": {"type": str},
    "requirements": {"type": str},
    "restrictions": {"type": str},
    "signup_url": {"type": str, "pattern": r"^https?://.*$"},
    "languages": {"type": list},
    "countries": {"type": list},
    "regional_links": {"type": dict},
    "deep_researched_at": {"type": str, "pattern": r"^\d{4}-\d{2}-\d{2}.*$"},
}

# Policy rules for content checking
POLICY_RULES = {
    "no_script_injection": r"<script|javascript:|onclick|onerror",
    "no_data_urls": r"data:text/html|data:application/",
    "no_suspicious_redirects": r"bit\.ly|tinyurl\.com|t\.co",
}


@dataclass
class ValidationResult:
    """Result of validating a single gate."""
    gate: str
    passed: bool
    message: str
    details: dict = field(default_factory=dict)


@dataclass
class ReviewResult:
    """Complete review result for a proposal."""
    proposal_id: str
    decision: str  # approve, reject, request_changes
    validation_results: dict
    notes: str
    auto_approved: bool = False


class EditorialReviewer:
    """
    LLM Reviewer that validates proposals through gates.

    Usage:
        reviewer = EditorialReviewer()

        # Review single proposal
        result = reviewer.review_proposal("proposal-uuid")

        # Review all pending proposals
        results = reviewer.review_pending(auto_approve=True)
    """

    def __init__(
        self,
        api_base: str = DEFAULT_API_BASE,
        agent_key: str = DEFAULT_REVIEWER_KEY,
        url_timeout: int = 10
    ):
        self.api_base = api_base.rstrip("/")
        self.agent_key = agent_key
        self.url_timeout = url_timeout

    def _api_get(self, path: str) -> dict:
        """Make authenticated GET request to editorial API."""
        response = requests.get(
            f"{self.api_base}{path}",
            headers={"X-Agent-Key": self.agent_key},
            timeout=30
        )
        response.raise_for_status()
        return response.json()

    def _api_post(self, path: str, data: dict) -> dict:
        """Make authenticated POST request to editorial API."""
        response = requests.post(
            f"{self.api_base}{path}",
            headers={
                "X-Agent-Key": self.agent_key,
                "Content-Type": "application/json",
            },
            json=data,
            timeout=30
        )
        response.raise_for_status()
        return response.json()

    def _validate_schema(self, changes: dict) -> ValidationResult:
        """Gate 1: Validate fields match expected types."""
        errors = []

        for field_name, value in changes.items():
            if field_name.startswith("_"):
                continue  # Skip internal fields

            schema = FIELD_SCHEMA.get(field_name)
            if not schema:
                # Unknown field - allow but note it
                continue

            # Type check
            expected_type = schema.get("type")
            if expected_type and not isinstance(value, expected_type):
                errors.append(f"{field_name}: expected {expected_type.__name__}, got {type(value).__name__}")
                continue

            # Pattern check
            pattern = schema.get("pattern")
            if pattern and isinstance(value, str):
                if not re.match(pattern, value, re.IGNORECASE):
                    errors.append(f"{field_name}: value '{value}' doesn't match expected pattern")

            # Range check for numbers
            if isinstance(value, (int, float)):
                min_val = schema.get("min")
                max_val = schema.get("max")
                if min_val is not None and value < min_val:
                    errors.append(f"{field_name}: value {value} below minimum {min_val}")
                if max_val is not None and value > max_val:
                    errors.append(f"{field_name}: value {value} above maximum {max_val}")

            # Allowed values check
            allowed = schema.get("allowed")
            if allowed and value not in allowed:
                # Check if it's a partial match for payout models
                if field_name == "payout_model":
                    if not any(a.lower() in str(value).lower() for a in allowed):
                        errors.append(f"{field_name}: value '{value}' not in allowed list")

        return ValidationResult(
            gate="schema_valid",
            passed=len(errors) == 0,
            message="; ".join(errors) if errors else "All fields valid",
            details={"errors": errors}
        )

    def _validate_provenance(self, proposal: dict) -> ValidationResult:
        """Gate 2: Check that claims have sources."""
        sources = proposal.get("sources", [])
        reasoning = proposal.get("reasoning", "")
        changes = proposal.get("changes", {})

        # Must have at least one source
        if not sources and not reasoning:
            return ValidationResult(
                gate="provenance_complete",
                passed=False,
                message="No sources or reasoning provided",
                details={"sources_count": 0}
            )

        # Check if sources have URLs
        valid_sources = [s for s in sources if s.get("url")]

        return ValidationResult(
            gate="provenance_complete",
            passed=len(valid_sources) > 0 or len(reasoning) > 10,
            message=f"Found {len(valid_sources)} sources, reasoning: {len(reasoning)} chars",
            details={"sources_count": len(valid_sources), "reasoning_length": len(reasoning)}
        )

    def _validate_urls(self, changes: dict) -> ValidationResult:
        """Gate 3: Verify URLs in changes are accessible."""
        urls_to_check = []

        # Collect URLs from changes
        signup_url = changes.get("signup_url")
        if signup_url and signup_url.startswith("http"):
            urls_to_check.append(("signup_url", signup_url))

        regional_links = changes.get("regional_links", {})
        if isinstance(regional_links, dict):
            for region, url in regional_links.items():
                if url and url.startswith("http"):
                    urls_to_check.append((f"regional_{region}", url))

        if not urls_to_check:
            return ValidationResult(
                gate="urls_verified",
                passed=True,
                message="No URLs to verify",
                details={"checked": 0}
            )

        # Check each URL
        errors = []
        for name, url in urls_to_check:
            try:
                response = requests.head(url, timeout=self.url_timeout, allow_redirects=True)
                if response.status_code >= 400:
                    errors.append(f"{name}: HTTP {response.status_code}")
            except requests.RequestException as e:
                errors.append(f"{name}: {str(e)[:50]}")

        return ValidationResult(
            gate="urls_verified",
            passed=len(errors) == 0,
            message="; ".join(errors) if errors else f"All {len(urls_to_check)} URLs verified",
            details={"checked": len(urls_to_check), "errors": errors}
        )

    def _validate_policy(self, changes: dict, raw_response: str | None) -> ValidationResult:
        """Gate 4: Check for policy violations (no JS injection, cloaking, etc.)."""
        violations = []

        # Check all string values in changes
        def check_string(name: str, value: str):
            for rule_name, pattern in POLICY_RULES.items():
                if re.search(pattern, value, re.IGNORECASE):
                    violations.append(f"{name}: {rule_name}")

        for field_name, value in changes.items():
            if isinstance(value, str):
                check_string(field_name, value)
            elif isinstance(value, list):
                for i, item in enumerate(value):
                    if isinstance(item, str):
                        check_string(f"{field_name}[{i}]", item)
            elif isinstance(value, dict):
                for k, v in value.items():
                    if isinstance(v, str):
                        check_string(f"{field_name}.{k}", v)

        # Also check raw LLM response if available
        if raw_response:
            for rule_name, pattern in POLICY_RULES.items():
                if re.search(pattern, raw_response, re.IGNORECASE):
                    violations.append(f"raw_response: {rule_name}")

        return ValidationResult(
            gate="policy_passed",
            passed=len(violations) == 0,
            message="; ".join(violations) if violations else "No policy violations",
            details={"violations": violations}
        )

    def _validate_no_conflicts(self, proposal: dict) -> ValidationResult:
        """Gate 5: Check for conflicts with existing data."""
        # For now, always pass - could be extended to check for conflicts
        return ValidationResult(
            gate="no_conflicts",
            passed=True,
            message="No conflict detection implemented",
            details={}
        )

    def review_proposal(self, proposal_id: str, auto_submit: bool = True) -> ReviewResult:
        """
        Review a single proposal through all validation gates.

        Args:
            proposal_id: UUID of the proposal to review
            auto_submit: Whether to automatically submit the review decision

        Returns:
            ReviewResult with decision and validation details
        """
        # Fetch proposal
        proposal = self._api_get(f"/editorial/proposals/{proposal_id}")

        if proposal["status"] != "pending_review":
            return ReviewResult(
                proposal_id=proposal_id,
                decision="skip",
                validation_results={"error": f"Status is {proposal['status']}, not pending_review"},
                notes=f"Skipped: status is {proposal['status']}"
            )

        changes = proposal.get("changes", {})
        raw_response = proposal.get("raw_llm_response")

        # Run all gates
        results = []
        results.append(self._validate_schema(changes))
        results.append(self._validate_provenance(proposal))
        results.append(self._validate_urls(changes))
        results.append(self._validate_policy(changes, raw_response))
        results.append(self._validate_no_conflicts(proposal))

        # Compile results
        validation_results = {r.gate: r.passed for r in results}
        all_passed = all(r.passed for r in results)

        # Build notes
        notes_parts = []
        for r in results:
            status = "✓" if r.passed else "✗"
            notes_parts.append(f"{status} {r.gate}: {r.message}")

        notes = "\n".join(notes_parts)

        # Determine decision
        if all_passed:
            decision = "approve"
        else:
            failed_gates = [r.gate for r in results if not r.passed]
            if "urls_verified" in failed_gates and len(failed_gates) == 1:
                # Only URL check failed - might be temporary
                decision = "request_changes"
            else:
                decision = "reject"

        review_result = ReviewResult(
            proposal_id=proposal_id,
            decision=decision,
            validation_results=validation_results,
            notes=notes,
            auto_approved=all_passed
        )

        # Submit review
        if auto_submit:
            try:
                self._api_post(f"/editorial/proposals/{proposal_id}/review", {
                    "decision": decision,
                    "notes": notes,
                    "validation_results": validation_results
                })
            except Exception as e:
                review_result.notes += f"\n\nFailed to submit review: {e}"

        return review_result

    def review_pending(
        self,
        limit: int = 100,
        auto_approve: bool = False,
        workers: int = 5
    ) -> list[ReviewResult]:
        """
        Review all pending proposals.

        Args:
            limit: Maximum number of proposals to review
            auto_approve: If True, auto-approve proposals that pass all gates
            workers: Number of parallel workers for URL checks

        Returns:
            List of review results
        """
        # Fetch pending proposals
        response = self._api_get(f"/editorial/proposals?status=pending_review&limit={limit}")
        proposals = response.get("items", [])

        print(f"Found {len(proposals)} pending proposals to review")

        results = []
        approved = 0
        rejected = 0

        for proposal in proposals:
            proposal_id = proposal["id"]
            entity_name = proposal.get("entity", {}).get("name", "Unknown")

            print(f"  Reviewing: {entity_name}...", end=" ")

            result = self.review_proposal(proposal_id, auto_submit=True)
            results.append(result)

            if result.decision == "approve":
                approved += 1
                print("✓ approved")

                # Auto-publish if requested
                if auto_approve:
                    try:
                        self._api_post(f"/editorial/proposals/{proposal_id}/publish", {})
                        print("    → published")
                    except Exception as e:
                        print(f"    → publish failed: {e}")

            elif result.decision == "reject":
                rejected += 1
                print("✗ rejected")

            else:
                print(f"⚠ {result.decision}")

        print(f"\nReview complete: {approved} approved, {rejected} rejected, {len(results) - approved - rejected} other")
        return results


# CLI
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Editorial Reviewer Agent")
    parser.add_argument("--proposal-id", help="Review specific proposal")
    parser.add_argument("--review-pending", action="store_true", help="Review all pending proposals")
    parser.add_argument("--auto-publish", action="store_true", help="Auto-publish approved proposals")
    parser.add_argument("--limit", type=int, default=100, help="Max proposals to review")
    parser.add_argument("--api-base", default=DEFAULT_API_BASE, help="API base URL")
    parser.add_argument("--agent-key", default=DEFAULT_REVIEWER_KEY, help="Reviewer API key")

    args = parser.parse_args()

    reviewer = EditorialReviewer(
        api_base=args.api_base,
        agent_key=args.agent_key
    )

    if args.proposal_id:
        print(f"Reviewing proposal {args.proposal_id}...")
        result = reviewer.review_proposal(args.proposal_id)
        print(f"\nDecision: {result.decision}")
        print(f"\nValidation Results:")
        for gate, passed in result.validation_results.items():
            print(f"  {'✓' if passed else '✗'} {gate}")
        print(f"\nNotes:\n{result.notes}")

    elif args.review_pending:
        print(f"Reviewing pending proposals...")
        results = reviewer.review_pending(
            limit=args.limit,
            auto_approve=args.auto_publish
        )

    else:
        parser.print_help()
