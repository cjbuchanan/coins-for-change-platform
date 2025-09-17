# Development Workflow and Guidelines

This document defines the development workflow, branching strategy, and collaboration guidelines for the Coins for Change platform.

## Git Workflow and Branching Strategy

### Branch Structure
```
main                    # Production-ready code
├── develop            # Integration branch for features
├── feature/CFC-123    # Feature branches (include ticket number)
├── bugfix/CFC-456     # Bug fix branches
├── hotfix/CFC-789     # Critical production fixes
└── release/v1.2.0     # Release preparation branches
```

### Branch Naming Conventions
- **Feature branches**: `feature/CFC-{ticket-number}-{short-description}`
- **Bug fixes**: `bugfix/CFC-{ticket-number}-{short-description}`
- **Hotfixes**: `hotfix/CFC-{ticket-number}-{short-description}`
- **Releases**: `release/v{major}.{minor}.{patch}`

### Commit Message Format
```
type(scope): short description

Longer description if needed

- Bullet points for details
- Reference ticket: CFC-123
- Breaking changes noted here

Co-authored-by: Name <email@example.com>
```

**Commit Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

**Examples:**
```
feat(coins): implement coin reallocation functionality

Add ability for users to move coins between ideas within the same campaign.
Includes validation for campaign boundaries and idea status checks.

- Add CoinReallocationService with business logic
- Implement /coins/reallocate API endpoint
- Add comprehensive test coverage
- Reference ticket: CFC-123

fix(auth): resolve JWT token expiration edge case

Fix issue where tokens were not properly invalidated on logout
when system clock was slightly out of sync.

- Update token blacklist logic
- Add clock skew tolerance
- Reference ticket: CFC-456
```

## Development Process

### Task Execution Workflow
1. **Pick a Task**: Select from the implementation plan (tasks.md)
2. **Create Branch**: Create feature branch from develop
3. **Implement**: Follow coding standards and business rules
4. **Test**: Write and run tests (unit, integration, e2e as appropriate)
5. **Document**: Update documentation and add code comments
6. **Review**: Self-review code and run quality checks
7. **Pull Request**: Create PR with detailed description
8. **Code Review**: Address feedback from team members
9. **Merge**: Merge to develop after approval and CI passes

### Definition of Done
A task is considered complete when:
- [ ] All acceptance criteria are met
- [ ] Code follows established coding standards
- [ ] Unit tests written and passing (minimum 80% coverage)
- [ ] Integration tests written for API endpoints
- [ ] Documentation updated (API docs, README, etc.)
- [ ] Code reviewed and approved by at least one team member
- [ ] All critical PR comments are resolved
- [ ] All CI/CD checks passing
- [ ] No security vulnerabilities introduced
- [ ] Performance impact assessed and acceptable

### Code Review Guidelines

#### What to Look For
1. **Correctness**: Does the code do what it's supposed to do?
2. **Security**: Are there any security vulnerabilities?
3. **Performance**: Are there any obvious performance issues?
4. **Maintainability**: Is the code readable and well-structured?
5. **Testing**: Are there adequate tests?
6. **Standards Compliance**: Does it follow our coding standards?

#### Review Checklist
- [ ] Business logic correctly implements requirements
- [ ] Error handling is comprehensive and appropriate
- [ ] Input validation is thorough
- [ ] Database operations use transactions appropriately
- [ ] API endpoints follow RESTful conventions
- [ ] Security best practices are followed
- [ ] Performance considerations are addressed
- [ ] Code is well-documented and readable
- [ ] Tests cover happy path and edge cases
- [ ] No hardcoded values or secrets

#### Review Comments Guidelines
- Be constructive and specific
- Explain the "why" behind suggestions
- Distinguish between "must fix" and "nice to have"
- Acknowledge good practices and clever solutions
- Use code suggestions for small fixes

## Testing Strategy

### Test Pyramid
```
    /\
   /  \     E2E Tests (Few)
  /____\    - Complete user workflows
 /      \   - Cross-service integration
/__________\ Integration Tests (Some)
            - API endpoint testing
            - Database integration
            - External service mocking

Unit Tests (Many)
- Business logic
- Individual functions
- Edge cases and error conditions
```

### Test Categories and Requirements

#### Unit Tests (Required for all tasks)
- Test individual functions and methods in isolation
- Mock external dependencies
- Cover happy path, edge cases, and error conditions
- Minimum 80% code coverage
- Fast execution (< 1 second per test)

#### Integration Tests (Required for API endpoints)
- Test API endpoints with real database
- Test service interactions
- Test authentication and authorization
- Use test database with cleanup
- Moderate execution time (< 10 seconds per test)

#### End-to-End Tests (Required for major features)
- Test complete user workflows
- Test cross-service functionality
- Use test environment similar to production
- Slower execution acceptable (< 5 minutes total)

### Test Data Management
```python
# Use factories for test data creation
@pytest.fixture
async def test_user():
    user = await UserFactory.create(
        email="test@example.com",
        is_active=True
    )
    yield user
    await cleanup_user(user.id)

# Use realistic test data
class CampaignFactory:
    @staticmethod
    async def create(**kwargs):
        defaults = {
            "title": "Test Campaign",
            "description": "A test campaign for unit testing",
            "campaign_type": CampaignType.OPEN,
            "status": CampaignStatus.DRAFT
        }
        defaults.update(kwargs)
        return await create_campaign(defaults)
```

## Environment Management

### Environment Types
1. **Development**: Local development environment
2. **Testing**: Automated testing environment
3. **Staging**: Pre-production testing
4. **Production**: Live system

### Configuration Management
```python
# Use environment-specific configuration
class Settings(BaseSettings):
    database_url: str
    redis_url: str
    opensearch_url: str
    jwt_secret: str
    environment: str = "development"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

# Environment-specific overrides
class DevelopmentSettings(Settings):
    debug: bool = True
    log_level: str = "DEBUG"

class ProductionSettings(Settings):
    debug: bool = False
    log_level: str = "INFO"
```

### Local Development Setup
```bash
# 1. Clone repository
git clone <repository-url>
cd coins-for-change-platform

# 2. Set up Python environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements-dev.txt

# 3. Set up pre-commit hooks
pre-commit install

# 4. Copy environment template
cp .env.example .env
# Edit .env with local configuration

# 5. Start local services
docker-compose up -d postgres opensearch redis

# 6. Run database migrations
alembic upgrade head

# 7. Seed test data (optional)
python scripts/seed_test_data.py

# 8. Run tests
pytest

# 9. Start development server
uvicorn main:app --reload
```

## Quality Assurance

### Automated Quality Checks
All code must pass these automated checks:
- **Linting**: flake8, mypy for type checking
- **Formatting**: black, isort for consistent formatting
- **Security**: bandit for security vulnerability scanning
- **Dependencies**: safety for known security vulnerabilities
- **Tests**: pytest with coverage reporting
- **Documentation**: Ensure docstrings are present and valid

### Pre-commit Hooks
```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    rev: 22.3.0
    hooks:
      - id: black
        language_version: python3.11

  - repo: https://github.com/pycqa/isort
    rev: 5.10.1
    hooks:
      - id: isort

  - repo: https://github.com/pycqa/flake8
    rev: 4.0.1
    hooks:
      - id: flake8

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v0.950
    hooks:
      - id: mypy

  - repo: https://github.com/PyCQA/bandit
    rev: 1.7.4
    hooks:
      - id: bandit
        args: ["-r", "src/"]
```

### Continuous Integration Pipeline
```yaml
# .github/workflows/ci.yml
name: CI Pipeline

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r requirements-dev.txt
      
      - name: Run linting
        run: |
          flake8 src/
          mypy src/
          bandit -r src/
      
      - name: Run tests
        run: |
          pytest --cov=src --cov-report=xml
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

## Documentation Standards

### Code Documentation
- All public functions and classes must have docstrings
- Use Google-style docstrings
- Include type hints for all parameters and return values
- Document exceptions that can be raised

### API Documentation
- FastAPI automatically generates OpenAPI documentation
- Provide detailed descriptions for all endpoints
- Include example requests and responses
- Document all possible error codes

### Architecture Documentation
- Keep architecture diagrams up to date
- Document major design decisions and rationale
- Maintain deployment and operational documentation
- Update README files for each service

## Performance Guidelines

### Database Performance
- Use database indexes appropriately
- Implement query optimization
- Use connection pooling
- Monitor slow queries and optimize

### API Performance
- Implement response caching where appropriate
- Use pagination for large result sets
- Implement rate limiting
- Monitor response times and optimize slow endpoints

### Monitoring and Alerting
- Set up performance monitoring
- Create alerts for critical metrics
- Monitor resource usage
- Track business metrics

## Security Guidelines

### Secure Development Practices
- Never commit secrets to version control
- Use environment variables for configuration
- Implement proper input validation
- Use parameterized queries to prevent SQL injection
- Implement proper authentication and authorization
- Log security events for audit purposes

### Dependency Management
- Regularly update dependencies
- Scan for known vulnerabilities
- Use lock files for reproducible builds
- Review new dependencies before adding

### Data Protection
- Encrypt sensitive data at rest and in transit
- Implement proper access controls
- Follow data retention policies
- Ensure GDPR compliance for user data

## Troubleshooting and Debugging

### Common Issues and Solutions
1. **Database Connection Issues**
   - Check connection string format
   - Verify database is running
   - Check network connectivity
   - Review connection pool settings

2. **Authentication Problems**
   - Verify JWT secret configuration
   - Check token expiration settings
   - Review user permissions
   - Check for clock synchronization issues

3. **Performance Issues**
   - Profile slow endpoints
   - Check database query performance
   - Review caching effectiveness
   - Monitor resource usage

### Debugging Tools and Techniques
- Use structured logging with correlation IDs
- Implement health check endpoints
- Use distributed tracing for complex workflows
- Set up proper monitoring and alerting
- Use debugger and profiling tools during development