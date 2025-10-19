from bedrock_agentcore import BedrockAgentCoreApp
from agents.scanner import scanner_main
from agents.risk_assessor import risk_assessor_main
from agents.solution import solution_main
import urllib.request
import zipfile
import tempfile
import shutil
import os
import boto3

app = BedrockAgentCoreApp()

@app.entrypoint
def app_entrypoint(payload):
    """Process a GitHub repository for vulnerabilities"""
    
    temp_dir = None
    
    try:
        # Extract URL from whatever format it comes in
        if isinstance(payload, dict):
            repo_url = payload.get('prompt') or payload.get('url') or payload.get('repo_url')
        else:
            repo_url = payload
        
        repo_url = str(repo_url).strip()
        print(f"Processing: {repo_url}")
        
        # Build download URL
        zip_url = repo_url.replace('.git', '').rstrip('/') + '/archive/refs/heads/main.zip'
        
        # Setup temp directory
        temp_dir = tempfile.mkdtemp(dir='/tmp')
        zip_path = os.path.join(temp_dir, 'repo.zip')
        
        # Download
        print("Downloading...")
        urllib.request.urlretrieve(zip_url, zip_path)
        print(f"Downloaded: {os.path.getsize(zip_path)} bytes")
        
        # Extract
        print("Extracting...")
        with zipfile.ZipFile(zip_path, 'r') as z:
            z.extractall(temp_dir)
        
        # Find repo directory
        dirs = [d for d in os.listdir(temp_dir) if os.path.isdir(os.path.join(temp_dir, d))]
        repo_dir = os.path.join(temp_dir, dirs[0])
        print(f"Repo at: {repo_dir}")
        
        # Run analysis
        print("Scanning...")
        vuln_report = scanner_main(repo_dir)
        
        print("Assessing risks...")
        risk_assessment = risk_assessor_main(vuln_report, repo_dir)
        
        print("Generating solutions...")
        solution_main(risk_assessment, repo_dir)
        print("Compressing repo directory...")
        repo_name = repo_url.rstrip('/').split('/')[-1].replace('.git', '')
        print(f"Repo name: {repo_name}")
        s3_client = boto3.client('s3')
        s3_bucket_name = "fixed-repo"
        s3_arn = f"arn:aws:s3:::{s3_bucket_name}"
        compressed_zip_path = os.path.join(temp_dir, f'{repo_name}_compressed.zip')
        shutil.make_archive(base_name=compressed_zip_path.replace('.zip', ''), format='zip', root_dir=repo_dir)
        # Upload to S3
        s3_key = f"{repo_name}/repo_scanned.zip"
        
        print(f"Uploading to S3: s3://{s3_bucket_name}/{s3_key}")
        s3_client.upload_file(
            compressed_zip_path,
            s3_bucket_name,
            s3_key
        )
        print("Upload successful!")

        print("Done!")
        return {"status": "success"}
        
    except Exception as e:
        print(f"Error: {e}")
        raise
    finally:
        if temp_dir:
            shutil.rmtree(temp_dir, ignore_errors=True)

if __name__ == "__main__":
    app.run()