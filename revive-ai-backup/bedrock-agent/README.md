# Bedrock Agent Implementation

## Architecture

This implementation adds Amazon Bedrock Agents to meet hackathon requirements.

### Agent Structure

**Main Agent:** Customer Win-back Agent
- **Primitives (Action Groups):**
  1. `analyzeCustomerChurn` - Analyze why customer churned
  2. `generateWinbackCampaign` - Create personalized email campaign
  3. `retrieveCustomerData` - Get customer info from S3
  4. `saveCampaignResults` - Store results to S3

### Requirements Met

✅ AgentCore: Uses bedrock-agent-runtime
✅ Primitives: 4 action groups
✅ Reasoning LLMs: Claude 3.5 Haiku
✅ Autonomous: Agent decides tool usage
✅ Tool Integration: S3, Lambdas
