# Autonomous Security Agent
The Autonomous Security Agent is a language-agnostic solution that can be seamlessly integrated into your application to autonomously identify and fix security vulnerabilities.
## Contents
- [Project Inspiration](https://github.com/Pavithrarenga/autonomous-security-agent/blob/main/README.md#project-inspiration)
- [What It Does](https://github.com/Pavithrarenga/autonomous-security-agent/blob/main/README.md#what-it-does)
- [How We Built It](https://github.com/Pavithrarenga/autonomous-security-agent/blob/main/README.md#how-we-built-it)
- [Architecture](https://github.com/Pavithrarenga/autonomous-security-agent/blob/main/README.md#architecture)
- [How To Run](https://github.com/Pavithrarenga/autonomous-security-agent/blob/main/README.md#how-to-run)
- [Challenges We Ran Into](https://github.com/Pavithrarenga/autonomous-security-agent/blob/main/README.md#challenges-we-ran-into)
- [Accomplishments We’re Proud Of](https://github.com/Pavithrarenga/autonomous-security-agent/blob/main/README.md#accomplishments-were-proud-of)
- [What We Learned](https://github.com/Pavithrarenga/autonomous-security-agent/blob/main/README.md#what-we-learned)
- [What’s Next for Autonomous Security Agent](https://github.com/Pavithrarenga/autonomous-security-agent/blob/main/README.md#whats-next-for-autonomous-security-agent)
- [Contributing](https://github.com/Pavithrarenga/autonomous-security-agent/blob/main/README.md#contributing)

## Project Inspiration
Developers often struggle to identify and remediate security issues in their code - especially when they lack a dedicated security team or deep security expertise. As software engineers, we’ve personally experienced this challenge. The common joke that “developers don’t care about security” isn’t entirely unfounded - most of us are focused on building products that _work_, often without enough bandwidth to ensure they’re _secure_.

We wanted to change that by creating a tool that acts as a reliable “security partner” for developers - an end-to-end autonomous agent that continuously watches over the codebase and proactively detects and fixes vulnerabilities and security issues. This project is our attempt to make that vision a reality.

By automating vulnerability detection and remediation, the Autonomous Security Agent dramatically reduces developer workload, shortens remediation cycles, and eliminates the need for expensive manual security audits - saving organisations thousands of dollars in potential breach costs and productivity loss.

## What It Does
Given a public GitHub repository, the **Autonomous Security Agent** uses four specialised agents built upon the **Claude 3.5** foundation model provided by AWS Bedrock - enhanced with **Trivy** for vulnerability scanning and **Tavily Search** for web intelligence.

The system:
*   Scans the repository for security issues and vulnerabilities.
*   Automatically identifies and prioritises vulnerabilities (with CVE references).
*   Proposes fixes for the issues it finds, and validates the fix by analysing and executing the fixed code in a secure sandboxed environment to ensure validity and credibility.
*   Once a fix is finalised, deploys the solution directly to the code.
*   Generates detailed vulnerability and remediation reports based on data from the NVD as a GitHub issue, and the patched code as a pull request.

## How We Built It
While one of our team members had prior AWS experience, **Amazon Bedrock** and **AgentCore** were new territories. After attending a workshop on Bedrock and agentic workflows, we began development using **Strands** as our agentic framework.

1. **Scanner Agent:** Our first milestone was building an agent capable of accessing a target GitHub repository, analysing it with an LLM, and supplementing results with a **Trivy** scan. The combined insights produced a comprehensive list of vulnerabilities with associated CVEs.
    
2.  **Risk Assessor Agent:** Next, we developed a risk assessor agent integrated with Tavily Web Search API, that gathers CVE details from the **NVD website** and produces structured vulnerability reports contextualised for the target application.

3. **Code Interpreter Agent:** This agent takes the suggestions for vulnerability fixes made by the risk assessor agent and validates its credibility by executing the fixed code in a sandboxed environment. It then returns a decision on whether the fix can be safely and reliably applied to the repository.
  
4.  **Solution Agent:** Finally, we created an agent that automatically patches vulnerabilities in the corresponding code files with fixes approved by the code interpreter agent, leveraging insights from the assessment stage. It also has persistent memory capabilities to learn from the fixes it made previously and decide what it needs to do next, and can be enhanced as part of future work to bring the human user in for conversational capabilities.

At every step, the agents send their results to a S3 bucket for auditing purposes, and the app also provides this information in a GitHub issue it raises on the target application. The code changes are also suggested via a pull request.  

We then orchestrated all four agents through a central application layer deployed via **AWS Bedrock AgentCore Runtime**, exposing it through a **Lambda function** and **API Gateway** for easy invocation.

## Architecture

## How to Run

### Prerequisites
- AWS CLI configured with your AWS account with appropriate permissions
- SAM CLI installed (`pip install aws-sam-cli`)
- Docker installed (for SAM build)
- Python 3.12+ and `uv` package manager
- GitHub Personal Access Token (PAT) with permissions to create issues and pull requests on any public repo (Generate at: [https://github.com/settings/tokens](https://github.com/settings/tokens))
- Tavily Search API key (Sign up at: [https://tavily.com](https://tavily.com) - First 1000 credits are free)

### AWS Permissions Required

Your AWS credentials need the following permissions:

-   Bedrock Agentcore full access
-   Lambda create/update functions
-   API Gateway create/manage APIs
-   IAM role creation
-   CloudFormation stack operations
-   S3 full access

### Deployment Steps

#### Part 1: Deploy Agents to AWS Bedrock Agentcore

##### Step 1: Setup Virtual Environment
```bash
# Create and activate virtual environment
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

##### Step 2: Install Dependencies

```bash
uv pip install -r requirements.txt
```

##### Step 3: Configure Environment Variables

Create a `.env` file with your credentials:

```bash
GITHUB_TOKEN=your_github_pat_here
TAVILY_API_KEY=your_tavily_key_here
```

#### Step 4: Configure Orchestration Agent

```bash
agentcore configure --entrypoint app.py --non-interactive
```
This creates:

-   `.bedrock_agentcore/app/` directory with a `Dockerfile`
-   `.bedrock_agentcore.yaml` configuration file

##### Step 5: Modify Dockerfile

The generated Dockerfile needs additional system dependencies for security scanning and git operations.

**Add the following to `.bedrock_agentcore/app/Dockerfile`:**
```dockerfile
# Install system dependencies: trivy (security scanner), git, and Node.js
RUN apt-get update && \
    apt-get install -y wget curl apt-transport-https gnupg lsb-release ca-certificates git && \
    # Install Trivy security scanner
    wget -qO - https://aquasecurity.github.io/trivy-repo/deb/public.key | gpg --dearmor -o /usr/share/keyrings/trivy.gpg && \
    echo "deb [signed-by=/usr/share/keyrings/trivy.gpg] https://aquasecurity.github.io/trivy-repo/deb $(lsb_release -sc) main" | tee /etc/apt/sources.list.d/trivy.list && \
    apt-get update && \
    apt-get install -y trivy && \
    # Install Node.js 20.x
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs && \
    # Cleanup
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*
```
##### Step 6: Deploy to Bedrock Agentcore
```bash
agentcore launch
```
This will:

-   Build the Docker container
-   Push to AWS ECR
-   Deploy our orchestrator agent to Bedrock Agentcore Runtime

##### Step 7: Test the Agent
Test in the Bedrock Agentcore sandbox with this input:

```json
{
  "prompt": "https://github.com/Pavithrarenga/target-app.git"
}
```

#### Part 2: Deploy Lambda + API Gateway (Entrypoint)

##### Install SAM CLI (if not installed):
   ```bash
   pip install aws-sam-cli
   ```

##### Step 1: Build with SAM

```bash
sam build --template-file deploy.yaml --use-container
```
##### Step 2: Deploy with SAM
```bash
sam deploy --template-file deploy.yaml --guided
```

##### Step 3: Configuration Prompts
Answer the deployment prompts:

-   **Stack name**: `asa-stack` (or your preferred name)
-   **AWS Region**: Your preferred region (e.g., `us-east-1`)
-   **Confirm changes before deploy**: `Y`
-   **Allow SAM CLI IAM role creation**: `Y`
-   **Save arguments to samconfig.toml**: `Y`

The deployment will output your API Gateway endpoint URL.

### Usage

#### Invoke the Security Agent

After deployment, you'll get an API endpoint URL such that we can invoke our main entrypoint agent using:
```bash
curl -X POST https://YOUR_API_ID.execute-api.YOUR_REGION.amazonaws.com/test/invoke \
  -H "Content-Type: application/json" \
  -d '{"input": "https://github.com/username/repository"}'
```
### Example Results
-   **GitHub Issue**: [https://github.com/Pavithrarenga/target-app/issues/2](https://github.com/Pavithrarenga/target-app/issues/2)
-   **GitHub Pull Request**: [https://github.com/Pavithrarenga/target-app/pull/3](https://github.com/Pavithrarenga/target-app/pull/3)

### Logs and Debugging

**View Lambda logs:**

```bash
sam logs -n InvokeLambdaFunction --stack-name asa-stack --tail
```

**View Bedrock Agentcore logs:**

-   Check CloudWatch Logs in AWS Console
-   Log group: `/aws/bedrock/agentcore/<agent-id>`


### Cleanup
To remove all deployed resources:
```bash
# Delete SAM stack
sam delete --stack-name asa-stack

# Delete Bedrock Agentcore agent
agentcore delete --agent-id <your-agent-id>

# Destroy agent
agentcore destroy
```

## Challenges We Ran Into
Our primary challenge was understanding how to effectively integrate the **Strands** framework with **Bedrock AgentCore** for agent deployment. With limited prior exposure, there was a steep learning curve. However, leveraging AWS strands-agents documentation and assistance from **Amazon Q**, we successfully overcame these challenges and built fully functional agents.

## Accomplishments We’re Proud Of
Our proudest achievement is that the **Autonomous Security Agent** doesn’t just _detect_ vulnerabilities - it also _validates_ and _fixes_ them autonomously. This leap beyond traditional vulnerability scanning demonstrates the power and potential of agentic workflows for real-world DevSecOps.

## What We Learned
We gained hands-on experience in:
*   Designing multi-agent systems using **strands-agents** built on our choice of foundation models, to develop a language and model-agnostic solution.
*   Integrating **LLMs** with traditional security tools like **Trivy** and web intelligence tools such as **Tavily** to enhance their capabilities.
*   Building and orchestrating agentic workflows on **AWS Bedrock** and **AWS Bedrock AgentCore** services.
*   Managing scalability, cost, and performance while maintaining system security.
    
## What’s Next for Autonomous Security Agent
1. Using fine-tuned LLMs to find and patch security issues and vulnerabilities more effectively.
2. Maintaining a full conversation with the user as it goes about fixing the issues it finds, giving the user the power to decide what needs to be done with minimal effort.
3. Fully integrating with the CI/CD pipeline of an application that is already live to provide continuous monitoring in its truest sense.

## Contributing
Contributions are welcome! Please open an issue or pull request.
