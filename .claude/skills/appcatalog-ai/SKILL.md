---
name: appcatalog-ai
description: AppCatalog AI documentation pipeline patterns. Use when building GitHub webhook processing, AI-powered document updates, SemVerDoc versioning, code-to-doc mapping, or hash-chained audit trails. This is the crown jewel differentiator of ProjeX Suite.
allowed-tools: Read, Write, Edit, Bash, Grep, Glob
---

# AppCatalog AI Documentation Pipeline

## Architecture Overview

```
GitHub PR Merge → Webhook → AppCatalog Worker → ERA AI → Draft Update → PO Review → Version Created
```

## GitHub Webhook Handler

```python
# appcatalog-api/app/api/webhooks.py
from fastapi import APIRouter, Request, HTTPException
import hmac, hashlib

router = APIRouter()

@router.post("/catalog/webhooks/github")
async def github_webhook(request: Request):
    # 1. Verify webhook signature
    signature = request.headers.get("X-Hub-Signature-256", "")
    body = await request.body()
    expected = "sha256=" + hmac.new(
        WEBHOOK_SECRET.encode(), body, hashlib.sha256
    ).hexdigest()
    if not hmac.compare_digest(signature, expected):
        raise HTTPException(403, "Invalid signature")
    
    # 2. Parse event
    event = request.headers.get("X-GitHub-Event")
    payload = await request.json()
    
    # 3. Only process merged PRs
    if event == "pull_request" and payload.get("action") == "closed" and payload["pull_request"]["merged"]:
        await process_merged_pr(payload)
    
    return {"status": "ok"}
```

## Code-to-Doc Mapping

```python
# code_ownership_map in catalog_documents table (JSONB)
# Maps file patterns to document sections
{
    "src/api/v1/invoices.py": {"doc": "tech_spec", "section": "4.3 Invoice API"},
    "src/api/v1/auth.py": {"doc": "tech_spec", "section": "5.1 Authentication"},
    "src/models/work_item.py": {"doc": "data_dict", "section": "2.2 Work Items"},
    "src/services/budget_service.py": {"doc": "fsd", "section": "UC-018 Budget"},
    "requirements.txt": {"doc": "tech_spec", "section": "1.0 Tech Stack"},
}
```

## AI Doc Update Flow

```python
async def process_merged_pr(payload):
    pr = payload["pull_request"]
    repo_url = payload["repository"]["html_url"]
    
    # 1. Fetch diff via GitHub Compare API
    diff = await github_client.get_compare(
        repo_url, pr["base"]["sha"], pr["merge_commit_sha"]
    )
    
    # 2. Parse conventional commits for change classification
    commits = await github_client.get_pr_commits(pr["number"])
    changes = classify_changes(commits)  # feat/fix/refactor/docs
    
    # 3. Map changed files to doc sections
    affected_docs = map_files_to_docs(diff.changed_files, code_ownership_map)
    
    # 4. For each affected doc section
    for doc_ref in affected_docs:
        current_content = await get_doc_section(doc_ref)
        
        # 5. Send to ERA AI
        updated_content = await era_ai.generate_doc_update(
            current_section=current_content,
            code_diff=diff.patch_for_files(doc_ref.files),
            commit_messages=changes,
            instruction="Update this section to reflect code changes. Keep style consistent."
        )
        
        # 6. Determine version bump
        version_bump = determine_bump(changes)
        #   feat: → MINOR, fix: → PATCH, breaking: → MAJOR
        
        # 7. Create draft version
        await create_draft_version(
            document_id=doc_ref.document_id,
            content=updated_content,
            change_type=version_bump,
            source="ai_generated",
            source_ref=pr["html_url"],
        )
        
        # 8. Create review task for PO
        await create_review_task(doc_ref, pr, version_bump)
        
        # 9. Notify via WA-Hub (optional)
        await notify_po_via_wa(doc_ref, pr)
```

## SemVerDoc Version Determination

```python
def determine_bump(changes: list[ConventionalCommit]) -> str:
    has_breaking = any(c.breaking for c in changes)
    has_feat = any(c.type == "feat" for c in changes)
    
    if has_breaking:
        return "major"   # MAJOR: breaking changes, restructure
    elif has_feat:
        return "minor"   # MINOR: new feature, new section
    else:
        return "patch"   # PATCH: fix, refactor, docs update
```

## Hash-Chained Audit Trail

```python
import hashlib, json

def create_audit_entry(prev_hash: str, actor_id, action, resource_id, before, after):
    payload = {
        "actor_id": str(actor_id),
        "action": action,
        "resource_id": str(resource_id),
        "before_hash": hashlib.sha256(json.dumps(before, sort_keys=True).encode()).hexdigest() if before else None,
        "after_hash": hashlib.sha256(json.dumps(after, sort_keys=True).encode()).hexdigest() if after else None,
    }
    canonical = json.dumps(payload, sort_keys=True) + (prev_hash or "GENESIS")
    entry_hash = hashlib.sha256(canonical.encode()).hexdigest()
    
    return AuditEvent(
        prev_hash=prev_hash,
        entry_hash=entry_hash,
        actor_id=actor_id,
        action=action,
        resource_id=resource_id,
        before_state=before,
        after_state=after,
    )
```

## CRITICAL RULES
- ALWAYS verify GitHub webhook signatures before processing
- ALWAYS require human review for MINOR and MAJOR version bumps
- PATCH-level auto-apply is acceptable (typo fixes, formatting)
- NEVER let AI modify documents without creating a version entry
- ALWAYS maintain hash-chain integrity — never modify existing audit entries
- ALWAYS map code changes to specific doc sections via code_ownership_map
- ALWAYS include source_ref (PR URL) in version metadata for traceability
