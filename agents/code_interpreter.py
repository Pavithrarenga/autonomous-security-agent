from strands import Agent, tool
from strands.models import BedrockModel
import boto3
import os
import shutil
import tempfile
import subprocess
import json
from datetime import datetime

@tool
def setup_sandbox_environment(repo_path: str, sandbox_path: str) -> str:
    """Copy repository to sandbox environment for safe testing."""
    try:
        if os.path.exists(sandbox_path):
            shutil.rmtree(sandbox_path)
        shutil.copytree(repo_path, sandbox_path)
        return f"Repository copied to sandbox: {sandbox_path}"
    except Exception as e:
        return f"Error setting up sandbox: {str(e)}"

@tool
def apply_fix_to_sandbox(file_path: str, fix_content: str, sandbox_path: str) -> str:
    """Apply proposed fix to file in sandbox environment."""
    try:
        sandbox_file_path = os.path.join(sandbox_path, os.path.basename(file_path))
        
        with open(sandbox_file_path, 'w', encoding='utf-8') as f:
            f.write(fix_content)
        
        return f"Fix applied to sandbox file: {sandbox_file_path}"
    except Exception as e:
        return f"Error applying fix: {str(e)}"

@tool
def update_package_json(sandbox_path: str, package_name: str, new_version: str) -> str:
    """Update a package version in package.json."""
    try:
        package_json_path = os.path.join(sandbox_path, 'package.json')
        
        with open(package_json_path, 'r') as f:
            package_data = json.load(f)
        
        # Update in dependencies
        if 'dependencies' in package_data and package_name in package_data['dependencies']:
            old_version = package_data['dependencies'][package_name]
            package_data['dependencies'][package_name] = new_version
            
            with open(package_json_path, 'w') as f:
                json.dump(package_data, f, indent=2)
            
            return f"Updated {package_name} from {old_version} to {new_version} in package.json"
        else:
            return f"Package {package_name} not found in dependencies"
            
    except Exception as e:
        return f"Error updating package.json: {str(e)}"

@tool
def run_npm_install(sandbox_path: str) -> str:
    """Run npm install in the sandbox."""
    try:
        result = subprocess.run(
            ['npm', 'install'],
            cwd=sandbox_path,
            capture_output=True,
            text=True,
            timeout=300
        )
        
        if result.returncode == 0:
            return f"✅ npm install completed successfully"
        else:
            return f"❌ npm install failed: {result.stderr[:500]}"
            
    except Exception as e:
        return f"Error running npm install: {str(e)}"

@tool
def analyze_and_test_application(sandbox_path: str) -> str:
    """Intelligently analyze application structure and create appropriate tests."""
    try:
        os.chdir(sandbox_path)
        results = []
        
        # 1. Analyze application structure
        app_analysis = analyze_app_structure(sandbox_path)
        results.append(f"App Analysis: {app_analysis}")
        
        # 2. Auto-detect application type and entry points
        app_info = detect_app_type_and_entry_points(sandbox_path)
        results.append(f"Detected: {app_info['type']} app with entry points: {app_info['entry_points']}")
        
        # 3. Run syntax/compilation checks
        syntax_result = check_syntax_and_compilation(app_info['type'])
        results.append(f"Syntax Check: {syntax_result}")
        
        # 4. Test application startup and basic functionality
        startup_result = test_application_startup(app_info)
        results.append(f"Startup Test: {startup_result}")
        
        # 5. Test API endpoints if it's a web app
        if app_info['type'] in ['flask', 'fastapi', 'express', 'node']:
            api_result = test_api_endpoints(app_info)
            results.append(f"API Test: {api_result}")
        
        return f"Comprehensive test results: {'; '.join(results)}"
        
    except Exception as e:
        return f"Error during application testing: {str(e)}"

@tool
def validate_fix_effectiveness(original_vuln_report: str, sandbox_path: str) -> str:
    """Re-run security scan on sandbox to validate fix effectiveness."""
    try:
        # Run Trivy scan on sandbox
        result = subprocess.run(
            ["trivy", "fs", sandbox_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=300
        )
        
        new_scan_results = result.stdout
        
        # Compare with original vulnerabilities
        import re
        cve_pattern = r'CVE-\d{4}-\d{4,7}'
        
        original_cves = set(re.findall(cve_pattern, original_vuln_report))
        new_cves = set(re.findall(cve_pattern, new_scan_results))
        
        fixed_cves = original_cves - new_cves
        remaining_cves = new_cves
        
        return f"Fix validation: {len(fixed_cves)} CVEs fixed, {len(remaining_cves)} remaining. Fixed: {list(fixed_cves)}"
        
    except Exception as e:
        return f"Error validating fix: {str(e)}"
    
def upload_agent_results(session, bucket_name, agent_type, repo_name, results):
    """Upload agent results to S3 with structured key."""
    try:
        s3_client = session.client('s3')
        
        # Create a structured S3 key
        date_str = datetime.utcnow().strftime('%Y/%m/%d')
        timestamp = datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')
        s3_key = f"{agent_type}_results/{date_str}/{repo_name}_{timestamp}.md"
        document=f"""# {agent_type.title()} Agent Results
                **Date:** {datetime.utcnow().isoformat()} UTC
                **Repository**: {repo_name}
                **Agent:** {agent_type.title()} Agent
                ## Results
                {results}
                
                --- End of Report ---
                *Generated by Autonomous Security Agent (ASA)*
                """
                
        
        # Upload the results
        s3_client.put_object(
            Bucket=bucket_name,
            Key=s3_key,
            Body=document.encode('utf-8'),
            ContentType='text/markdown'
        )
        
        s3_url = f"s3://{bucket_name}/{s3_key}"
        print(f"{agent_type.title()} agent results uploaded to {s3_url}")
        return s3_url
    except Exception as e:
        print(f"Error uploading {agent_type} agent results to s3: {e}")
        return f"s3 upload failed: {str(e)}"   


def get_code_interpreter_system_prompt():
    return """
You are an advanced code interpreter agent with sandbox testing capabilities. Your role is to:

1. **Sandbox Setup**: Copy the target repository to a safe sandbox environment
2. **Fix Application**: Apply fixes to the sandbox environment
3. **Testing**: Run the application in sandbox to ensure fixes don't break functionality
4. **Validation**: Re-scan the fixed code to confirm vulnerabilities are resolved
5. **Recommendation**: Provide go/no-go recommendation for applying fixes to production

Your workflow:
1. Setup sandbox environment with repository code using setup_sandbox_environment
2. Apply fix using update_package_json or apply_fix_to_sandbox
3. Run npm install using run_npm_install
4. Run application tests using analyze_and_test_application
5. Run security scan using validate_fix_effectiveness
6. Return comprehensive test results and recommendation (APPROVE/REJECT)

Be thorough but efficient. Focus on critical functionality and security validation.
"""

def create_code_interpreter_agent(session, original_repo_path, original_vuln_report):
    """Create code interpreter agent with sandbox capabilities."""
    
    bedrock_model = BedrockModel(
        model_id="anthropic.claude-3-5-sonnet-20241022-v2:0",
        temperature=0.1,
        top_p=0.8,
        boto_session=session,
    )

    return Agent(
        model=bedrock_model,
        system_prompt=get_code_interpreter_system_prompt(),
        tools=[
            setup_sandbox_environment,
            apply_fix_to_sandbox,
            update_package_json,
            run_npm_install,
            analyze_and_test_application,
            validate_fix_effectiveness
        ],
    )

def analyze_app_structure(repo_path: str) -> str:
    """Analyze repository structure to understand the application."""
    structure_info = []
    
    # Check for common files and directories
    common_files = ['README.md', 'requirements.txt', 'package.json', 'Dockerfile', 'docker-compose.yml']
    found_files = [f for f in common_files if os.path.exists(os.path.join(repo_path, f))]
    structure_info.append(f"Config files: {found_files}")
    
    # Count code files by type
    code_counts = {}
    for root, dirs, files in os.walk(repo_path):
        for file in files:
            ext = os.path.splitext(file)[1]
            if ext in ['.py', '.js', '.ts', '.java', '.go', '.rs', '.cpp', '.c']:
                code_counts[ext] = code_counts.get(ext, 0) + 1
    
    structure_info.append(f"Code files: {code_counts}")
    return "; ".join(structure_info)

def detect_app_type_and_entry_points(repo_path: str) -> dict:
    """Detect application type and find entry points."""
    app_info = {'type': 'unknown', 'entry_points': []}
    
    # Check for Python web frameworks
    if os.path.exists(os.path.join(repo_path, 'app.py')):
        with open(os.path.join(repo_path, 'app.py'), 'r') as f:
            content = f.read()
            if 'Flask' in content:
                app_info['type'] = 'flask'
                app_info['entry_points'] = ['app.py']
            elif 'FastAPI' in content:
                app_info['type'] = 'fastapi'
                app_info['entry_points'] = ['app.py']
            elif 'Django' in content:
                app_info['type'] = 'django'
                app_info['entry_points'] = ['manage.py']
            else:
                app_info['type'] = 'python'
                app_info['entry_points'] = ['app.py']
    
    # Check for Node.js
    elif os.path.exists(os.path.join(repo_path, 'package.json')):
        try:
            with open(os.path.join(repo_path, 'package.json'), 'r') as f:
                package_data = json.loads(f.read())
                app_info['type'] = 'node'
                if 'main' in package_data:
                    app_info['entry_points'] = [package_data['main']]
                elif 'scripts' in package_data and 'start' in package_data['scripts']:
                    app_info['entry_points'] = ['npm start']
        except:
            app_info['type'] = 'node'
            app_info['entry_points'] = ['index.js', 'server.js', 'app.js']
    
    # Check for other Python files
    elif any(f.endswith('.py') for f in os.listdir(repo_path)):
        app_info['type'] = 'python'
        py_files = [f for f in os.listdir(repo_path) if f.endswith('.py')]
        app_info['entry_points'] = py_files[:3]
    
    return app_info

def check_syntax_and_compilation(app_type: str) -> str:
    """Check syntax and compilation for the application."""
    errors = []
    
    if app_type in ['python', 'flask', 'fastapi', 'django']:
        for root, dirs, files in os.walk('.'):
            for file in files:
                if file.endswith('.py'):
                    py_file = os.path.join(root, file)
                    try:
                        result = subprocess.run(['python', '-m', 'py_compile', py_file], 
                                              capture_output=True, text=True)
                        if result.returncode != 0:
                            errors.append(f"{py_file}: {result.stderr[:100]}")
                    except Exception as e:
                        errors.append(f"{py_file}: {str(e)[:100]}")
    elif app_type == 'node':
        for root, dirs, files in os.walk('.'):
            for file in files:
                if file.endswith('.js'):
                    js_file = os.path.join(root, file)
                    try:
                        result = subprocess.run(['node', '--check', js_file], 
                                              capture_output=True, text=True)
                        if result.returncode != 0:
                            errors.append(f"{js_file}: {result.stderr[:100]}")
                    except Exception as e:
                        errors.append(f"{js_file}: {str(e)[:100]}")
    
    return f"Syntax check: {len(errors)} errors found" + (f" - {errors[:3]}" if errors else " - all clean")

def test_application_startup(app_info: dict) -> str:
    """Test if the application can start up properly."""
    startup_results = []
    
    for entry_point in app_info['entry_points']:
        try:
            if app_info['type'] in ['python', 'flask', 'fastapi', 'django']:
                if entry_point.endswith('.py') and os.path.exists(entry_point):
                    result = subprocess.run(['python', '-c', f'import {entry_point[:-3]}'], 
                                          capture_output=True, text=True, timeout=10)
                    startup_results.append(f"{entry_point}: import {'success' if result.returncode == 0 else 'failed'}")
            
            elif app_info['type'] == 'node':
                if entry_point == 'npm start':
                    startup_results.append("npm start: command available")
                elif os.path.exists(entry_point):
                    result = subprocess.run(['node', '--check', entry_point], 
                                          capture_output=True, text=True, timeout=10)
                    startup_results.append(f"{entry_point}: syntax {'valid' if result.returncode == 0 else 'invalid'}")
        
        except subprocess.TimeoutExpired:
            startup_results.append(f"{entry_point}: startup test timed out")
        except Exception as e:
            startup_results.append(f"{entry_point}: {str(e)[:50]}")
    
    return "; ".join(startup_results) if startup_results else "No startup tests performed"

def test_api_endpoints(app_info: dict) -> str:
    """Test API endpoints by analyzing code for route definitions."""
    endpoints_found = []
    
    try:
        for root, dirs, files in os.walk('.'):
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        import re
                        flask_routes = re.findall(r'@app\.route\(["\']([^"\']*)["\'\)]', content)
                        fastapi_routes = re.findall(r'@app\.(get|post|put|delete)\(["\']([^"\']*)["\'\)]', content)
                        
                        if flask_routes:
                            endpoints_found.extend([f"Flask: {route}" for route in flask_routes])
                        if fastapi_routes:
                            endpoints_found.extend([f"FastAPI: {method[1]} ({method[0]})" for method in fastapi_routes])
                
                elif file.endswith('.js'):
                    file_path = os.path.join(root, file)
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        import re
                        express_routes = re.findall(r'app\.(get|post|put|delete)\(["\']([^"\']*)["\']', content)
                        if express_routes:
                            endpoints_found.extend([f"Express: {method[1]} ({method[0]})" for method in express_routes])
        
        return f"Found {len(endpoints_found)} endpoints: {endpoints_found[:5]}" if endpoints_found else "No API endpoints detected"
    
    except Exception as e:
        return f"Endpoint analysis failed: {str(e)}"

def code_interpreter_main(original_repo_path, original_vuln_report):
    """Main function to test proposed fix in sandbox environment."""
    
    session = boto3.Session(region_name='ap-southeast-2')
    
    # Create temporary sandbox directory
    sandbox_path = tempfile.mkdtemp(prefix="security_fix_sandbox_")
    
    try:
        # Create agent
        agent = create_code_interpreter_agent(session, original_repo_path, original_vuln_report)
        
        # Enhanced prompt for intelligent testing
        test_prompt = f"""
        You are a code interpreter validator. I need you to test a proposed security fix in a sandbox environment.
        
        Original repository path: {original_repo_path}
        Sandbox path: {sandbox_path}
        Original vulnerability report: {original_vuln_report}
        
        Analyse the Proposed fix from original_vuln_report and execute the following steps to validate its effectiveness:
        
        Please execute these steps:
        1. Use setup_sandbox_environment to copy the repo to sandbox
        2. Use update_package_json to update the vulnerable dependency as per the proposed fix.
        3. Use run_npm_install to install updated dependencies
        4. Use analyze_and_test_application to test the application
        5. Use validate_fix_effectiveness to verify the CVE is fixed
        6. Provide a recommendation (APPROVE/REJECT) with detailed reasoning
        
        Focus on:
        - Successful dependency update
        - No syntax/compilation errors
        - Application structure intact
        - Analysis for the first found CVE has been resolved
        """
        
        response = agent(test_prompt)
        # Upload results to S3
        bucket_name = 'security-agent-results'
        upload_result = upload_agent_results(session, bucket_name, "code_interpreter_results", original_repo_path, str(response))
        print(f"s3 upload result: {upload_result}")
        
        return {
            "status": "completed",
            "sandbox_path": sandbox_path,
            "test_results": str(response),
            "recommendation": "APPROVE" if "APPROVE" in str(response) else "NEEDS_REVIEW"
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "sandbox_path": sandbox_path
        }