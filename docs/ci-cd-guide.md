# CI/CD Guide

This guide provides an overview of the continuous integration and continuous delivery (CI/CD) setup for the Apple Health Monitor project.

## Overview

Our CI/CD pipeline uses GitHub Actions to automate testing, building, security scanning, and deployment processes. The pipeline ensures code quality, security, and reliable releases.

## Workflows

### 1. CI Workflow (`ci.yml`)

**Triggers**: Push to main/develop, Pull requests, Manual dispatch

**Jobs**:
- **Lint**: Code style and quality checks (flake8, black, isort, mypy)
- **Test**: Multi-platform testing matrix
  - OS: Ubuntu, Windows, macOS
  - Python: 3.9, 3.10, 3.11, 3.12
  - Includes coverage reporting to Codecov
- **Build**: Creates platform-specific executables

### 2. Security Workflow (`security.yml`)

**Triggers**: Push to main/develop, Pull requests, Weekly schedule

**Jobs**:
- **CodeQL**: Static analysis for security vulnerabilities
- **Dependency Check**: Scans for vulnerable dependencies
- **Secret Scanning**: Detects accidentally committed secrets
- **License Check**: Ensures license compliance

### 3. Docker Workflow (`docker.yml`)

**Triggers**: Push to main, Version tags, Pull requests

**Features**:
- Multi-platform builds (amd64, arm64)
- GitHub Container Registry publication
- Vulnerability scanning with Trivy
- Semantic versioning tags

### 4. Release Workflow (`release.yml`)

**Triggers**: Version tags (v*), Manual dispatch

**Process**:
1. Builds executables for all platforms
2. Generates changelog from commits
3. Creates GitHub release with artifacts
4. Supports pre-releases (alpha/beta)

### 5. Documentation Workflow (`docs.yml`)

**Triggers**: Documentation changes, Manual dispatch

**Features**:
- Builds MkDocs documentation
- Deploys to GitHub Pages
- Strict mode for link validation

## Pre-commit Hooks

Install pre-commit hooks locally:

```bash
pip install pre-commit
pre-commit install
```

Hooks include:
- Code formatting (black, isort)
- Linting (flake8, pylint, mypy)
- Security checks (bandit, safety)
- Commit message validation
- Unit test execution

## Dependabot

Automated dependency updates are configured for:
- Python packages (weekly)
- GitHub Actions (weekly)
- Docker base images (weekly)

Updates are grouped by type (development/production) and include automatic PR creation.

## Branch Protection

Recommended branch protection rules for `main`:

- Require pull request reviews
- Dismiss stale reviews on new commits
- Require status checks:
  - CI / Lint
  - CI / Test (all matrix combinations)
  - Security / CodeQL
- Require branches to be up to date
- Include administrators

## Secrets Management

Required repository secrets:
- `CODECOV_TOKEN`: For coverage reporting
- `GITHUB_TOKEN`: Automatically provided by GitHub

Optional secrets:
- `DOCKER_USERNAME`: For Docker Hub publishing
- `DOCKER_PASSWORD`: For Docker Hub authentication

## Local Development

### Running CI Checks Locally

```bash
# Run linting
flake8 src tests
black --check src tests
isort --check-only src tests
mypy src

# Run tests
pytest tests/ -v --cov=src

# Build Docker image
docker build -t apple-health-monitor .

# Run with docker-compose
docker-compose up test
```

### Testing Workflows Locally

Use [act](https://github.com/nektos/act) to test GitHub Actions locally:

```bash
# Test CI workflow
act -W .github/workflows/ci.yml

# Test specific job
act -W .github/workflows/ci.yml -j lint
```

## Monitoring

- **GitHub Actions**: View workflow runs in the Actions tab
- **Codecov**: Coverage reports at codecov.io
- **Security**: Alerts in the Security tab
- **Dependencies**: Dependabot alerts and PRs

## Best Practices

1. **Commit Messages**: Use conventional commits format
   ```
   type(scope): description
   
   feat(ui): add dark mode toggle
   fix(analytics): correct monthly calculation
   ```

2. **Pull Requests**:
   - Keep PRs focused and small
   - Include tests for new features
   - Update documentation as needed
   - Ensure all checks pass

3. **Releases**:
   - Use semantic versioning (v1.2.3)
   - Tag releases on main branch
   - Include changelog in release notes
   - Test pre-releases before stable

## Troubleshooting

### Common Issues

1. **Qt Platform Plugin Error**:
   - Solution: Set `QT_QPA_PLATFORM=offscreen` in environment

2. **Coverage Upload Fails**:
   - Check CODECOV_TOKEN is set
   - Verify coverage.xml is generated

3. **Docker Build Fails**:
   - Ensure Dockerfile syntax is correct
   - Check base image availability

### Debug Tips

- Add `--debug` flag to pytest for verbose output
- Use workflow debug logging: Set secret `ACTIONS_STEP_DEBUG=true`
- Check workflow syntax: `yamllint .github/workflows/*.yml`

## Contributing

When contributing to CI/CD:

1. Test changes locally first
2. Update this documentation
3. Consider backward compatibility
4. Add appropriate error handling
5. Follow security best practices

For questions or issues, please open a GitHub issue or discussion.