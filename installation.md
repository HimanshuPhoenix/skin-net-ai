### Step 1: Enable APIs & Set Permissions
Run these commands in your terminal:
```bash
# Enable required APIs
gcloud services enable aiplatform.googleapis.com run.googleapis.com

# Grant Vertex AI User role to your Service Account
gcloud projects add-iam-policy-binding skin-net  --member="serviceAccount:skin-net-ai@skin-net.iam.gserviceaccount.com"  --role="roles/aiplatform.user"
```

### Step 2: Create Your MySQL Tables
Connect to your MySQL database and create the foundational tables for your parents' application. Here is a starter schema you can execute:

```sql
CREATE TABLE __#####__ (
    
);
```

### Step 3: Configure the Environment Variables
In your VS Code project directory, create a `.env` file to hold your project configuration. 

```env
PROJECT_ID=project_id
SA_NAME=<service account name>
SERVICE_ACCOUNT=<service account name>@<project-id>.iam.gserviceaccount.com
MODEL="gemini-3.0-flash" # Or gemini-2.5-flash
```

### Step 4: Configure the MCP Toolbox for Databases
To allow your AI agent to query your MySQL database without writing boilerplate connection code, you will use the open-source MCP Toolbox.

1. Download the MCP Toolbox binary for your operating system.

Test that the toolbox works by running it locally with the UI flag:
```bash
./toolbox --tools-file "tools.yaml" --ui
```
You can access the Toolbox UI at `http://127.0.0.1:5000/ui` to manually test the SQL tool.

### Step 5: Initialize the ADK Agent
With the database exposed via MCP, let's create the Python agent.

1. Install the required ADK and Toolbox core packages:
```bash
# pip install requirements.txt
```
### Step 6. Set Your Project ID
Set your active Google Cloud project so the CLI knows where to deploy the resources. Replace `your-project-id` with your actual Project ID:
```bash
gcloud config set project your-project-id
```

### Step 7. Enable Required Google Cloud APIs
To use Cloud Run, Artifact Registry, and Cloud Build, you must enable their respective APIs in your Google Cloud project. Run the following command in your terminal:
```bash
gcloud services enable run.googleapis.com artifactregistry.googleapis.com cloudbuild.googleapis.com aiplatform.googleapis.com compute.googleapis.com
```
When this finishes, you should see a message indicating the operation finished successfully.

### Step 8. Create and Configure a Service Account
You need to create a dedicated service account for your Cloud Run service so it operates with specific permissions rather than broad default access. Run this command to create the account:
```bash
gcloud iam service-accounts create skin-net-ai --display-name="Service Account for SKIn Net"
```
Next, grant this new service account the "Vertex AI User" role, which gives it permission to call Google's Gemini models in the cloud:
```bash
gcloud projects add-iam-policy-binding <your-project-id> --member="serviceAccount:skin-net-ai@<your-project-id>.iam.gserviceaccount.com" --role="roles/aiplatform.user"

```
gcloud services enable aiplatform.googleapis.com apikeys.googleapis.com mapstools.googleapis.com