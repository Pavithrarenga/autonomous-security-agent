# Autonomous Security Agent

## Contents
- [Project Inspiration](https://github.com/Pavithrarenga/autonomous-security-agent/blob/main/README.md#project-inspiration)
- [What It Does](https://github.com/Pavithrarenga/autonomous-security-agent/blob/main/README.md#what-it-does)
- [How We Built It](https://github.com/Pavithrarenga/autonomous-security-agent/blob/main/README.md#how-we-built-it)
- [How To Run](https://github.com/Pavithrarenga/autonomous-security-agent/blob/main/README.md#how-to-run)
- [Challenges We Ran Into](https://github.com/Pavithrarenga/autonomous-security-agent/blob/main/README.md#challenges-we-ran-into)
- [Accomplishments We’re Proud Of](https://github.com/Pavithrarenga/autonomous-security-agent/blob/main/README.md#accomplishments-were-proud-of)
- [What We Learned](https://github.com/Pavithrarenga/autonomous-security-agent/blob/main/README.md#what-we-learned)
- [What’s Next for Autonomous Security Agent](https://github.com/Pavithrarenga/autonomous-security-agent/blob/main/README.md#whats-next-for-autonomous-security-agent)

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

## How to Run

## Prerequisites
- AWS CLI configured
- SAM CLI installed (`pip install aws-sam-cli`)
- Docker installed (for SAM build)

## Deployment Steps

1. **Install SAM CLI** (if not installed):
   ```bash
   pip install aws-sam-cli
   ```

2. **Deploy using SAM**:
   ```bash
   sam build --template-file deploy.yaml --use-container
   sam deploy --template-file deploy.yaml --guided
   ```

3. **Follow the prompts**:
   - Stack name: `asa-stack`
   - AWS Region: Choose your preferred region
   - Confirm changes before deploy: Y
   - Allow SAM to create IAM roles: Y
   - Save parameters to samconfig.toml: Y

## API Usage

After deployment, you'll get an API endpoint URL. Use it like this:

```bash
curl -X POST https://YOUR_API_ID.execute-api.YOUR_REGION.amazonaws.com/Prod/scan \
  -H "Content-Type: application/json" \
  -d '{"repo_url": "https://github.com/username/repo"}'
```

## Test the API

Update `test_api.py` with your actual API URL and run:
```bash
python test_api.py
```

## Architecture

- **Lambda Function**: Wraps your agent entrypoint
- **API Gateway**: Provides HTTPS endpoint
- **S3 Bucket**: Stores processed repositories (fixed-repo)
- **IAM Roles**: Permissions for Bedrock and S3 access
