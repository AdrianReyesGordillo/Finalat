# Infrastructure Configuration

This directory contains deployment configuration for the Finalat platform on AWS.

## Directory Structure

```
infrastructure/
├── cloudformation/
│   ├── frontend-hosting.yml    # S3 + CloudFront for SPA hosting
│   └── database.yml            # RDS PostgreSQL 15 instance
├── nginx/
│   └── finalat-backend.conf    # Nginx reverse proxy configuration
├── scripts/
│   └── deploy-migrations.sh    # Alembic migration deployment script
├── systemd/
│   └── finalat-backend.service # Systemd service unit for uvicorn
└── README.md                   # This file
```

---

## Database: RDS PostgreSQL 15

The database is hosted on AWS RDS PostgreSQL 15 with encryption at rest and restricted network access.

### Architecture

- **RDS Instance**: PostgreSQL 15 on db.t3.micro (dev) or db.t3.small (production)
- **Storage**: 20GB gp3, auto-scaling up to 100GB
- **Encryption at rest**: AES-256 via AWS RDS storage encryption
- **SSL/TLS**: Forced for all connections (`rds.force_ssl = 1`)
- **Multi-AZ**: Disabled (cost savings for MVP)
- **Security Group**: Inbound only from EC2 application security group on port 5432

### Backup Configuration

| Setting | Value |
|---------|-------|
| Automated backups | Enabled |
| Retention period | 7 days |
| Backup window | 03:00–04:00 UTC |
| Snapshot on delete | Yes (DeletionPolicy: Snapshot) |
| Copy tags to snapshots | Yes |

### Connection String Format

The application connects using SQLAlchemy's async driver:

```
postgresql+asyncpg://user:password@host:5432/finalat
```

With SSL (production):

```
postgresql+asyncpg://user:password@host:5432/finalat?ssl=require
```

Set the `DATABASE_URL` environment variable with the full connection string.

### Deploying the Database Infrastructure

1. Deploy the CloudFormation stack:

```bash
aws cloudformation deploy \
  --template-file infrastructure/cloudformation/database.yml \
  --stack-name finalat-database \
  --region us-east-1 \
  --parameter-overrides \
    Environment=dev \
    DBName=finalat \
    DBMasterUsername=finalat_admin \
    "DBMasterPassword=<your-secure-password>" \
    EC2SecurityGroupId=<ec2-sg-id> \
    VpcId=<vpc-id> \
    "SubnetIds=<subnet-1>,<subnet-2>"
```

2. Get the outputs (endpoint and connection string format):

```bash
aws cloudformation describe-stacks \
  --stack-name finalat-database \
  --query "Stacks[0].Outputs"
```

3. Set the `DATABASE_URL` in the `.env` file or GitHub Secrets using the endpoint from outputs.

### Running Migrations

Use the deployment script to manage database migrations:

```bash
# Run pending migrations (used during deployment)
./infrastructure/scripts/deploy-migrations.sh

# Check migration status without applying
./infrastructure/scripts/deploy-migrations.sh --check

# Rollback to a specific revision
./infrastructure/scripts/deploy-migrations.sh --rollback <revision-id>
```

Required environment variables:
- `DATABASE_URL` — Full PostgreSQL connection string

The script:
- Waits for database connectivity (retries up to 5 times)
- Shows current and pending migration status
- Applies migrations with `alembic upgrade head`
- Logs pre/post-migration revisions for rollback reference
- Exits with error code on failure (halts CI/CD pipeline)

### Required GitHub Secrets (Database)

| Secret | Description |
|--------|-------------|
| `DATABASE_URL` | Full PostgreSQL connection string with credentials |

---

## EC2 Instance Setup

### Prerequisites

- Ubuntu 22.04 LTS on EC2 t2.micro (Free Tier eligible)
- Python 3.13 installed
- Nginx installed
- Certbot installed (for SSL certificates)
- PostgreSQL client libraries (`libpq-dev`)

### Initial Server Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y python3.13 python3.13-venv python3-pip nginx certbot python3-certbot-nginx libpq-dev git

# Clone repository
cd /home/ubuntu
git clone <repository-url> Finalat

# Create virtual environment
cd Finalat
python3.13 -m venv venv
source venv/bin/activate

# Install Python dependencies
cd backend
pip install -r requirements.txt

# Create environment file
cp .env.example .env
# Edit .env with production values (see Environment Variables below)
```

### Install Systemd Service

```bash
# Copy service file
sudo cp /home/ubuntu/Finalat/infrastructure/systemd/finalat-backend.service /etc/systemd/system/

# Reload systemd and enable service
sudo systemctl daemon-reload
sudo systemctl enable finalat-backend
sudo systemctl start finalat-backend

# Check status
sudo systemctl status finalat-backend
journalctl -u finalat-backend -f
```

### Install Nginx Configuration

```bash
# Copy nginx config
sudo cp /home/ubuntu/Finalat/infrastructure/nginx/finalat-backend.conf /etc/nginx/sites-available/finalat-backend

# Enable site
sudo ln -s /etc/nginx/sites-available/finalat-backend /etc/nginx/sites-enabled/

# Remove default site
sudo rm -f /etc/nginx/sites-enabled/default

# Test configuration
sudo nginx -t

# Obtain SSL certificate (first time)
sudo certbot --nginx -d api.finalat.com

# Reload nginx
sudo systemctl reload nginx
```

### Security Group Configuration

**EC2 Security Group (inbound rules):**

| Port | Protocol | Source | Description |
|------|----------|--------|-------------|
| 443 | TCP | 0.0.0.0/0 | HTTPS traffic |
| 22 | TCP | <your-ip>/32 | SSH (restricted to your IP) |

**RDS Security Group (inbound rules):**

| Port | Protocol | Source | Description |
|------|----------|--------|-------------|
| 5432 | TCP | EC2 Security Group | PostgreSQL from app server |

## Environment Variables

The following environment variables must be configured in `/home/ubuntu/Finalat/.env` on the EC2 instance, and as GitHub Secrets for the CI/CD pipeline.

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string (SSL) | `postgresql+asyncpg://user:pass@rds-host:5432/finalat?ssl=require` |
| `FERNET_KEY` | AES-256 encryption key (Fernet) | Generated via `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"` |
| `FIREBASE_PROJECT_ID` | Firebase project identifier | `finalat-prod` |
| `FIREBASE_WEB_API_KEY` | Firebase Web API key | `AIza...` |
| `AWS_REGION` | AWS region for services | `us-east-1` |
| `AWS_ACCESS_KEY_ID` | AWS IAM access key | `AKIA...` |
| `AWS_SECRET_ACCESS_KEY` | AWS IAM secret key | `wJalr...` |
| `BEDROCK_MODEL_ID` | Amazon Bedrock model ID | `anthropic.claude-3-sonnet-20240229-v1:0` |
| `CORS_ORIGINS` | Allowed CORS origins (CloudFront URL) | `https://d1234567.cloudfront.net` |
| `APP_ENV` | Application environment | `production` |
| `DEBUG` | Debug mode (false in production) | `false` |

### GitHub Secrets (for CI/CD)

The following secrets must be configured in the GitHub repository settings:

| Secret | Description |
|--------|-------------|
| `EC2_HOST` | EC2 instance public IP or hostname |
| `EC2_USER` | SSH username (typically `ubuntu`) |
| `EC2_SSH_KEY` | Private SSH key for EC2 access |
| `FERNET_KEY` | Same Fernet key used on the server |
| `FIREBASE_PROJECT_ID` | Firebase project ID (for tests) |
| `AWS_ACCESS_KEY_ID` | AWS credentials (for S3/CloudFront deploy) |
| `AWS_SECRET_ACCESS_KEY` | AWS secret key |
| `AWS_REGION` | AWS region |

### Generate Fernet Key

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

## Deployment Flow

The backend deployment is automated via GitHub Actions (`.github/workflows/deploy-backend.yml`):

1. **Push to `main`** triggers the workflow
2. **Test job**: Runs linting and unit tests against a PostgreSQL service container
3. **Deploy job** (only if tests pass): SSHs into EC2 and executes:
   - `git pull` latest code
   - Install/update Python dependencies
   - Run Alembic database migrations
   - Restart the systemd service
   - Verify the service is active

## Monitoring & Logs

```bash
# View backend logs
journalctl -u finalat-backend -f

# View nginx access logs
tail -f /var/log/nginx/access.log

# View nginx error logs
tail -f /var/log/nginx/error.log

# Check service status
sudo systemctl status finalat-backend

# Check nginx status
sudo systemctl status nginx
```

## SSL Certificate Renewal

Certbot auto-renewal is typically configured via a systemd timer or cron:

```bash
# Test renewal
sudo certbot renew --dry-run

# Certbot auto-renewal timer should already be active
sudo systemctl status certbot.timer
```
