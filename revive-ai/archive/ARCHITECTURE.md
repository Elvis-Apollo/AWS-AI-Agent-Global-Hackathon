# Revive AI - Technical Architecture

## System Overview

Revive AI is a serverless multi-agent AI system built entirely on AWS services. It orchestrates two specialized AI agents to analyze customer churn and generate personalized win-back campaigns at scale.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                          USER INTERACTION                        │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                    ┌───────────▼───────────┐
                    │   Web Frontend        │
                    │   (React SPA)         │
                    │   S3 Static Hosting   │
                    └───────────┬───────────┘
                                │
                    ┌───────────▼───────────┐
                    │   API Gateway (REST)  │
                    │   /upload  /process   │
                    │   /results /demo      │
                    └───────────┬───────────┘
                                │
                    ┌───────────▼──────────────────────┐
                    │   Lambda: API Handler            │
                    │   - CSV validation               │
                    │   - Step Functions orchestration │
                    │   - Results aggregation          │
                    └──────────┬─────────┬─────────────┘
                               │         │
                    ┌──────────▼─┐   ┌──▼────────────┐
                    │  S3 Bucket │   │ Step Functions│
                    │  (Data)    │   │ State Machine │
                    │            │   │               │
                    │  uploads/  │   │ PrepareJob    │
                    │  results/  │   │      ↓        │
                    │  demo/     │   │ Map (x8)      │
                    └────────────┘   │      ↓        │
                                     │ FinalizeJob   │
                                     └───────┬───────┘
                                             │
                              ┌──────────────▼──────────────┐
                              │ Lambda: Customer Worker     │
                              │ (Parallel: 8 concurrent)    │
                              │                             │
                              │  ┌───────────────────────┐  │
                              │  │ Bedrock Agent 1       │  │
                              │  │ (Churn Analysis)      │  │
                              │  │ - Categorize reason   │  │
                              │  │ - Confidence score    │  │
                              │  │ - Generate insights   │  │
                              │  └──────────┬────────────┘  │
                              │             │               │
                              │  ┌──────────▼────────────┐  │
                              │  │ Bedrock Agent 2       │  │
                              │  │ (Campaign Generation) │  │
                              │  │ - 3 personalized      │  │
                              │  │   emails per customer │  │
                              │  │ - Category-specific   │  │
                              │  └───────────────────────┘  │
                              └──────────────┬──────────────┘
                                             │
                                  ┌──────────▼──────────┐
                                  │  S3 Results         │
                                  │  - status.json      │
                                  │  - customers/*.json │
                                  │  - aggregated files │
                                  └─────────────────────┘
```

## Data Flow

### 1. Upload Phase

```
User → Upload CSV
  ↓
API Gateway → POST /upload
  ↓
Lambda API Handler
  ├─ Parse CSV
  ├─ Validate each customer record
  └─ Store to S3: uploads/{upload_id}.csv & .json
  ↓
Return: {upload_id, customer_count}
```

### 2. Processing Phase

```
User → Start Processing
  ↓
API Gateway → POST /process
  ↓
Lambda API Handler
  ├─ Read customers from S3
  └─ Start Step Functions execution
      ↓
Step Functions: PrepareJob
  └─ Initialize status.json in S3
      ↓
Step Functions: Map State (MaxConcurrency=8)
  ├─ Invoke Customer Worker Lambda per customer
  │   ├─ Agent 1: Analyze churn → analysis.json
  │   ├─ Agent 2: Generate campaign → campaign.json
  │   ├─ Save results/{upload_id}/customers/{customer_id}.json
  │   └─ Update status.json (increment counters)
  └─ Parallel processing of 8 customers at a time
      ↓
Step Functions: FinalizeJob
  ├─ Aggregate all customer results
  ├─ Create customers.json, analyses.json, campaigns.json
  └─ Mark status.json as "complete"
```

### 3. Results Phase

```
Frontend → Poll GET /results?upload_id={id} every 3s
  ↓
Lambda API Handler
  ├─ Read status.json
  ├─ If processing: return progress metrics
  └─ If complete: return all campaigns
      ↓
Frontend → Display results
```

## Component Details

### Lambda Functions

#### 1. API Handler (revive-ai-api-handler)

**Purpose:** Handle all API requests and orchestration tasks

**Runtime:** Python 3.11
**Memory:** 512 MB
**Timeout:** 30 seconds

**Routes:**
- `POST /upload` - CSV upload and validation
- `POST /process` - Start Step Functions execution
- `GET /results` - Fetch processing status and results
- `POST /demo` - Return pre-generated demo data

**Step Functions Tasks:**
- `prepare_job` - Initialize status.json
- `finalize_job` - Aggregate results

**Environment Variables:**
- `DATA_BUCKET` - S3 bucket for data storage
- `FRONTEND_BUCKET` - S3 bucket for frontend assets
- `STATE_MACHINE_ARN` - Step Functions ARN

#### 2. Customer Worker (revive-ai-customer-worker)

**Purpose:** Process single customer through both AI agents

**Runtime:** Python 3.11
**Memory:** 1024 MB
**Timeout:** 60 seconds

**Process:**
1. Receive customer payload from Step Functions
2. Invoke Churn Analysis Agent (Bedrock)
3. Invoke Campaign Generation Agent (Bedrock)
4. Save results to S3
5. Update status counters

**Environment Variables:**
- `DATA_BUCKET` - S3 bucket for data storage
- `BEDROCK_MODEL_ID` - Model identifier (claude-3.5-sonnet)

### Step Functions State Machine

**Type:** Standard Workflow
**Target Runtime:** <60 seconds for 50 customers

**States:**

1. **PrepareJob** (Task)
   - Invoke API Handler Lambda
   - Initialize status.json with metadata

2. **ProcessCustomers** (Map)
   - Iterate over customers array
   - MaxConcurrency: 8 (balance speed vs rate limits)
   - Retry: 2 attempts with exponential backoff
   - Catch: Record failures but continue processing

3. **FinalizeJob** (Task)
   - Invoke API Handler Lambda
   - Aggregate all results
   - Mark processing complete

### AI Agents (Bedrock)

#### Agent 1: Churn Analysis

**Model:** Claude Sonnet 4.5
**Temperature:** 0.3 (analytical)
**Max Tokens:** 1024

**Input:**
- Customer profile (company, tier, MRR)
- Churn date
- Cancellation reason

**Output:**
```json
{
  "category": "pricing|features|onboarding|competition|business_closure|unclear",
  "confidence": 85,
  "insights": ["insight1", "insight2", "insight3"],
  "recommendation": "tactical approach"
}
```

**Processing Time:** <3 seconds

#### Agent 2: Campaign Generation

**Model:** Claude Sonnet 4.5
**Temperature:** 0.7 (creative)
**Max Tokens:** 2048

**Input:**
- Customer profile
- Churn analysis results
- Category-specific guidance

**Output:**
```json
{
  "emails": [
    {
      "number": 1,
      "subject": "...",
      "body": "...",
      "cta": "..."
    },
    // Email 2 and 3
  ]
}
```

**Processing Time:** <5 seconds

### Storage Layer (S3)

#### Data Bucket Structure

```
revive-ai-data/
├── uploads/
│   ├── {upload_id}.csv      # Original CSV
│   └── {upload_id}.json     # Parsed customers array
├── results/
│   └── {upload_id}/
│       ├── status.json      # Processing status
│       ├── customers/
│       │   ├── c001.json    # Per-customer results
│       │   ├── c002.json
│       │   └── ...
│       ├── customers.json   # Aggregated customers
│       ├── analyses.json    # All analyses
│       └── campaigns.json   # All campaigns
└── demo/
    ├── demo_50_customers.csv
    └── demo_results.json
```

#### Frontend Bucket Structure

```
revive-ai-frontend/
└── web/
    └── index.html
```

## Scalability Considerations

### Concurrency Control

**Step Functions Map State:** MaxConcurrency = 8
- Balances processing speed with Bedrock rate limits
- Prevents throttling errors
- Can be adjusted based on account quotas

### Performance Optimizations

1. **Parallel Processing**
   - 8 customers processed simultaneously
   - 50 customers complete in ~35-45 seconds

2. **Bedrock Optimization**
   - Reuse client session per Lambda invocation
   - Minimal prompt tokens (<2000)
   - Right-sized max_tokens parameter

3. **S3 Access Patterns**
   - Individual customer files for incremental updates
   - Aggregated files for final results
   - Status file for real-time progress

### Error Handling

1. **Lambda Level**
   - Try/catch around Bedrock calls
   - Validation of AI outputs
   - Logging to CloudWatch

2. **Step Functions Level**
   - Retry policy: 2 attempts, 2x backoff
   - Catch block for graceful failures
   - Continue processing on individual failures

3. **API Level**
   - Input validation
   - Proper HTTP status codes
   - Error messages with details

## Security Architecture

### IAM Roles

**Lambda Execution Role:**
- S3: GetObject, PutObject on data/frontend buckets
- Bedrock: InvokeModel
- Step Functions: StartExecution, DescribeExecution
- CloudWatch: Logs permissions

**Step Functions Execution Role:**
- Lambda: InvokeFunction on both functions
- CloudWatch: Logs and X-Ray tracing

### Data Security

- S3 data bucket: Private (no public access)
- S3 frontend bucket: Public read-only
- API Gateway: CORS enabled
- No credentials in frontend code
- Bedrock calls logged (sanitized)

## Monitoring & Observability

### CloudWatch Logs

- Lambda function logs
- Step Functions execution history
- API Gateway access logs

### Metrics

- Lambda duration and errors
- Step Functions execution success rate
- Bedrock invocation count
- S3 storage usage

### Key Observability Points

1. **Processing Time**
   - Per-customer processing duration
   - Overall execution time
   - Bedrock API latency

2. **Success Rates**
   - Customer processing success rate
   - Agent output validation pass rate
   - Step Functions completion rate

3. **Resource Usage**
   - Lambda memory utilization
   - S3 storage growth
   - API request volume

## Cost Optimization

### Cost Breakdown (per 1000 customers)

- **Bedrock:** ~$0.15 (Claude invocations)
- **Lambda:** ~$0.02 (compute time)
- **Step Functions:** ~$0.05 (state transitions)
- **S3:** <$0.01 (storage + requests)
- **API Gateway:** ~$0.01 (API calls)

**Total:** ~$0.24 per 1000 customers

### Optimization Strategies

1. Use Standard Step Functions (cheaper than Express)
2. Right-size Lambda memory allocations
3. Minimize Bedrock max_tokens
4. S3 lifecycle policies for old data
5. CloudWatch log retention policies

## Deployment Architecture

### Multi-Region Considerations

Currently single-region (us-east-1) for:
- Bedrock model availability
- Simplified networking
- Cost optimization

**Future:** Can expand to multi-region with:
- CloudFront for frontend distribution
- Regional S3 buckets with replication
- Regional Lambda deployments
- Cross-region Step Functions

### CI/CD Pipeline (Recommended)

```
GitHub → GitHub Actions
  ↓
Build & Test
  ↓
Package Lambda functions
  ↓
Upload to S3 artifact bucket
  ↓
CloudFormation / Terraform
  ↓
Deploy to AWS
  ↓
Integration Tests
  ↓
Production Release
```

## Testing Strategy

### Unit Tests
- Shared module validation
- Schema validation logic
- S3 helper functions

### Integration Tests
- Lambda functions with mocked Bedrock
- Step Functions with test customers
- End-to-end API tests

### Load Tests
- 100 customers processing
- Concurrent API requests
- Bedrock rate limit testing

## Future Enhancements

1. **Real-time Updates:** WebSocket for live progress
2. **Advanced Analytics:** Campaign performance tracking
3. **A/B Testing:** Multiple campaign variants
4. **Email Integration:** Direct sending via SES
5. **Custom Models:** Fine-tuned Bedrock models
6. **Multi-tenancy:** Support multiple companies
7. **Advanced Scheduling:** Optimal send times per customer
8. **Feedback Loop:** Track campaign success and retrain

---

**Last Updated:** 2025-10-08
**Version:** 1.0
**Status:** Production-Ready
