# Revive AI Execution Plan

> Legend: `P0` = critical path, `P1` = high priority, `P2` = nice to have. Tags: `Sequential` (must follow order), `Parallel` (can run concurrently with other Parallel tasks in same phase).

## Phase 0 – Environment & Access
- [ ] `P0 | Sequential` Confirm Bedrock model access and note `BEDROCK_MODEL_ID`.
- [ ] `P0 | Sequential` Provision S3 buckets (`revive-ai-data`, `revive-ai-frontend`) with correct policies and versioning.
- [ ] `P0 | Parallel` Create IAM roles/policies for API handler, worker, and Step Functions state machine (scoped S3 + Bedrock + States permissions).

## Phase 1 – Backend Core (Day 1-2)
- [ ] `P0 | Sequential` Scaffold shared Python project structure (common utils, Bedrock client, schema validation).
- [ ] `P0 | Sequential` Implement customer worker Lambda: ingest payload, run both agents via shared async Bedrock client, write `customers/{customer_id}.json`, update `status.json`.
- [ ] `P0 | Parallel` Draft Step Functions definition (PrepareJob → Map → FinalizeJob) reusing API handler entrypoints for Prepare/Finalize.
- [ ] `P0 | Parallel` Write PrepareJob handler logic: initialize `status.json` with counters, timestamps, and execution ARN placeholder.
- [ ] `P0 | Parallel` Write FinalizeJob handler logic: aggregate `customers/*.json` into rolled-up `customers.json`, `analyses.json`, `campaigns.json`, and mark status complete.
- [ ] `P1 | Parallel` Add unit/integration harness to replay sample customers locally (optional but helpful for prompt tuning).

## Phase 2 – API & Integration (Day 3)
- [ ] `P0 | Sequential` Implement API Gateway Lambda handler routes (`/upload`, `/process`, `/results`, `/demo`).
- [ ] `P0 | Sequential` Integrate `/process` with `StartExecution` call and include returned ARN in response payload.
- [ ] `P0 | Sequential` Ensure `/results` reads `status.json`, merges finished customer files, and surfaces progress + failures.
- [ ] `P1 | Parallel` Create helper script to upload demo CSV and trigger `/process` end-to-end for smoke testing.

## Phase 3 – Frontend (Day 3-4)
- [ ] `P0 | Sequential` Build upload view with CSV validation and `/process` call storing `execution_arn`.
- [ ] `P0 | Sequential` Build processing view with polling every 3 seconds, displaying `completed/total`, `failures`, ETA, and timeout handling.
- [ ] `P0 | Sequential` Build results grid with status badges (success/failed/pending) and detail modal wired to aggregated JSON.
- [ ] `P1 | Parallel` Finish styling cleanup (responsive layout, Tailwind utility classes).

## Phase 4 – Data & Demo Prep (Day 4-5)
- [ ] `P0 | Sequential` Generate/verify 50-customer demo CSV covering category/tier distribution.
- [ ] `P0 | Sequential` Run full Step Function execution with demo CSV; verify duration <60 s and status accuracy.
- [ ] `P0 | Sequential` Store successful run output as `demo_results.json` for `/demo` endpoint.
- [ ] `P1 | Parallel` Capture CloudWatch log snippets and Step Functions screenshots for presentation backups.

## Phase 5 – Validation & Polish (Day 5)
- [ ] `P0 | Sequential` Execute testing checklist (multi-browser UI, throttled network, 10+ end-to-end runs).
- [ ] `P0 | Sequential` Confirm `/demo` and `/process` flows work after cold start (morning-of warm-up).
- [ ] `P0 | Parallel` Prep presentation script, Q&A, and fallback assets (video/screenshots).
- [ ] `P1 | Parallel` Review security posture: bucket policies locked down, sensitive env variables only in Lambda config/Secrets Manager.

## Phase 6 – Optional Enhancements (Day 6 buffer)
- [ ] `P2 | Parallel` Add real-time progress websocket or SSE channel (if time allows).
- [ ] `P2 | Parallel` Add PDF export or sharable download of campaigns.
- [ ] `P2 | Parallel` Implement advanced analytics/visualizations for churn insights.

## Final Submission
- [ ] `P0 | Sequential` Update README with setup/run instructions and architecture summary.
- [ ] `P0 | Sequential` Record final demo video highlighting Step Functions orchestration and live UI.
- [ ] `P0 | Sequential` Submit Devpost entry with repo link, video, and supporting materials.
