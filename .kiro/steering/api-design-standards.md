# API Design Standards

This document defines the API design standards and conventions for the Coins for Change platform.

## RESTful API Principles

### Resource Naming Conventions
- Use **nouns** for resource names, not verbs
- Use **plural nouns** for collections: `/campaigns`, `/ideas`, `/users`
- Use **kebab-case** for multi-word resources: `/campaign-members`, `/coin-allocations`
- Use **nested resources** to show relationships: `/campaigns/{id}/ideas`, `/campaigns/{id}/members`

### HTTP Methods and Their Usage
```
GET     /campaigns              # List all campaigns
GET     /campaigns/{id}         # Get specific campaign
POST    /campaigns              # Create new campaign
PUT     /campaigns/{id}         # Update entire campaign
PATCH   /campaigns/{id}         # Partial update campaign
DELETE  /campaigns/{id}         # Delete campaign

GET     /campaigns/{id}/ideas   # List ideas in campaign
POST    /campaigns/{id}/ideas   # Create idea in campaign
GET     /ideas/{id}             # Get specific idea (global resource)
PUT     /ideas/{id}             # Update idea
DELETE  /ideas/{id}             # Delete idea
```

### URL Structure Guidelines
```
# Good examples
GET /campaigns/{campaign_id}/ideas?status=competing&page=1&size=20
POST /campaigns/{campaign_id}/coins/allocate
GET /users/{user_id}/notifications?unread=true

# Avoid these patterns
GET /getCampaignIdeas          # Don't use verbs
GET /campaign_ideas            # Don't use underscores
GET /campaigns/ideas           # Missing campaign context
POST /allocateCoins            # Don't use verbs in URLs
```

## Request and Response Standards

### Request Body Format
```python
# Use Pydantic models for all request bodies
class CampaignCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=255, description="Campaign title")
    description: str = Field(..., min_length=1, max_length=5000, description="Campaign description")
    campaign_type: CampaignType = Field(..., description="Type of campaign")
    start_date: Optional[datetime] = Field(None, description="Campaign start date")
    end_date: Optional[datetime] = Field(None, description="Campaign end date")
    
    @validator('end_date')
    def validate_end_date(cls, v, values):
        if v and values.get('start_date') and v <= values['start_date']:
            raise ValueError('End date must be after start date')
        return v

# Example request
POST /campaigns
Content-Type: application/json

{
  "title": "Q1 Product Features",
  "description": "Prioritize features for Q1 development",
  "campaign_type": "mediated",
  "start_date": "2024-01-15T00:00:00Z",
  "end_date": "2024-02-15T23:59:59Z"
}
```

### Response Body Format
```python
# Consistent response structure
class CampaignResponse(BaseModel):
    id: UUID
    campaign_id: str
    title: str
    description: str
    campaign_type: CampaignType
    status: CampaignStatus
    start_date: Optional[datetime]
    end_date: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    created_by: UserSummary
    member_count: int
    idea_count: int
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v)
        }

# Example response
HTTP/1.1 201 Created
Content-Type: application/json
Location: /campaigns/550e8400-e29b-41d4-a716-446655440000

{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "campaign_id": "q1-product-features",
  "title": "Q1 Product Features",
  "description": "Prioritize features for Q1 development",
  "campaign_type": "mediated",
  "status": "draft",
  "start_date": "2024-01-15T00:00:00Z",
  "end_date": "2024-02-15T23:59:59Z",
  "created_at": "2024-01-10T10:30:00Z",
  "updated_at": "2024-01-10T10:30:00Z",
  "created_by": {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "name": "John Doe",
    "email": "john.doe@example.com"
  },
  "member_count": 0,
  "idea_count": 0
}
```

### Pagination Standards
```python
# Pagination parameters
class PaginationParams(BaseModel):
    page: int = Field(1, ge=1, description="Page number (1-based)")
    size: int = Field(20, ge=1, le=100, description="Items per page")
    sort: Optional[str] = Field(None, description="Sort field")
    order: Optional[str] = Field("asc", regex="^(asc|desc)$", description="Sort order")

# Paginated response format
class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    pagination: PaginationInfo
    
class PaginationInfo(BaseModel):
    page: int
    size: int
    total_items: int
    total_pages: int
    has_next: bool
    has_previous: bool

# Example paginated response
GET /campaigns?page=2&size=10&sort=created_at&order=desc

{
  "items": [...],
  "pagination": {
    "page": 2,
    "size": 10,
    "total_items": 45,
    "total_pages": 5,
    "has_next": true,
    "has_previous": true
  }
}
```

## Error Handling Standards

### Error Response Format
```python
class ErrorResponse(BaseModel):
    error_code: str = Field(..., description="Machine-readable error code")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    request_id: str = Field(..., description="Unique request identifier")
    
# Standard error codes
class ErrorCodes:
    # Authentication errors (AUTH_xxx)
    AUTHENTICATION_FAILED = "AUTH_001"
    INVALID_TOKEN = "AUTH_002"
    TOKEN_EXPIRED = "AUTH_003"
    
    # Authorization errors (AUTHZ_xxx)
    INSUFFICIENT_PERMISSIONS = "AUTHZ_001"
    RESOURCE_ACCESS_DENIED = "AUTHZ_002"
    
    # Campaign errors (CAMPAIGN_xxx)
    CAMPAIGN_NOT_FOUND = "CAMPAIGN_001"
    CAMPAIGN_INACTIVE = "CAMPAIGN_002"
    CAMPAIGN_ALREADY_ACTIVE = "CAMPAIGN_003"
    
    # Coin errors (COIN_xxx)
    INSUFFICIENT_COINS = "COIN_001"
    COINS_ALREADY_EXPENDED = "COIN_002"
    INVALID_ALLOCATION_AMOUNT = "COIN_003"
    
    # Idea errors (IDEA_xxx)
    IDEA_NOT_FOUND = "IDEA_001"
    IDEA_NOT_COMPETING = "IDEA_002"
    DUPLICATE_IDEA_DETECTED = "IDEA_003"
    
    # Validation errors (VALIDATION_xxx)
    INVALID_INPUT = "VALIDATION_001"
    MISSING_REQUIRED_FIELD = "VALIDATION_002"
    INVALID_FORMAT = "VALIDATION_003"
```

### HTTP Status Code Usage
```python
# Success responses
200 OK              # Successful GET, PUT, PATCH
201 Created         # Successful POST
204 No Content      # Successful DELETE
206 Partial Content # Successful partial response

# Client error responses
400 Bad Request     # Invalid request syntax or validation errors
401 Unauthorized    # Authentication required or failed
403 Forbidden       # Authenticated but insufficient permissions
404 Not Found       # Resource doesn't exist
409 Conflict        # Resource conflict (e.g., duplicate campaign ID)
422 Unprocessable Entity  # Business logic validation failed
429 Too Many Requests     # Rate limit exceeded

# Server error responses
500 Internal Server Error # Unexpected server error
502 Bad Gateway          # Upstream service error
503 Service Unavailable  # Service temporarily unavailable
504 Gateway Timeout      # Upstream service timeout
```

### Error Response Examples
```json
// Validation error
HTTP/1.1 400 Bad Request
{
  "error_code": "VALIDATION_001",
  "message": "Invalid input data",
  "details": {
    "field_errors": {
      "title": ["Title is required"],
      "end_date": ["End date must be after start date"]
    }
  },
  "timestamp": "2024-01-10T10:30:00Z",
  "request_id": "req_123456789"
}

// Business logic error
HTTP/1.1 422 Unprocessable Entity
{
  "error_code": "COIN_001",
  "message": "Insufficient coins for allocation",
  "details": {
    "requested_amount": 50,
    "available_balance": 30,
    "campaign_id": "550e8400-e29b-41d4-a716-446655440000"
  },
  "timestamp": "2024-01-10T10:30:00Z",
  "request_id": "req_123456789"
}

// Authorization error
HTTP/1.1 403 Forbidden
{
  "error_code": "AUTHZ_001",
  "message": "Insufficient permissions to perform this action",
  "details": {
    "required_permission": "campaign:manage",
    "user_permissions": ["campaign:view", "idea:create"]
  },
  "timestamp": "2024-01-10T10:30:00Z",
  "request_id": "req_123456789"
}
```

## Authentication and Authorization

### JWT Token Format
```python
# JWT payload structure
{
  "sub": "550e8400-e29b-41d4-a716-446655440000",  # User ID
  "email": "user@example.com",
  "name": "John Doe",
  "roles": ["campaign_member"],
  "permissions": ["campaign:view", "idea:create", "coin:allocate"],
  "iat": 1641811200,  # Issued at
  "exp": 1641897600,  # Expires at
  "jti": "token_unique_id"  # JWT ID for blacklisting
}

# Authorization header format
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### Permission-Based Authorization
```python
# FastAPI dependency for authorization
async def require_permission(
    permission: str,
    current_user: User = Depends(get_current_user)
) -> User:
    """Require specific permission for endpoint access"""
    if not current_user.has_permission(permission):
        raise HTTPException(
            status_code=403,
            detail={
                "error_code": "AUTHZ_001",
                "message": "Insufficient permissions",
                "details": {"required_permission": permission}
            }
        )
    return current_user

# Usage in endpoints
@router.post("/campaigns")
async def create_campaign(
    campaign_data: CampaignCreateRequest,
    current_user: User = Depends(require_permission("campaign:create"))
):
    # Implementation
```

## Filtering and Searching

### Query Parameter Standards
```python
# Standard query parameters
class CampaignFilters(BaseModel):
    status: Optional[CampaignStatus] = None
    campaign_type: Optional[CampaignType] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    search: Optional[str] = Field(None, min_length=1, max_length=100)
    
# URL examples
GET /campaigns?status=active&campaign_type=open
GET /campaigns?created_after=2024-01-01T00:00:00Z&search=product
GET /ideas?tags=feature,priority&coin_count_min=10&coin_count_max=100
```

### Search Implementation
```python
# Search endpoint design
@router.get("/campaigns/{campaign_id}/ideas/search")
async def search_ideas(
    campaign_id: UUID,
    q: str = Query(..., min_length=1, max_length=100, description="Search query"),
    tags: Optional[List[str]] = Query(None, description="Filter by tags"),
    status: Optional[IdeaStatus] = Query(None, description="Filter by status"),
    coin_count_min: Optional[int] = Query(None, ge=0, description="Minimum coin count"),
    coin_count_max: Optional[int] = Query(None, ge=0, description="Maximum coin count"),
    pagination: PaginationParams = Depends()
):
    """Search ideas within a campaign with filters"""
    # Implementation with OpenSearch
```

## Versioning Strategy

### API Versioning Approach
```python
# Version in URL path (recommended)
/api/v1/campaigns
/api/v2/campaigns

# Version in header (alternative)
Accept: application/vnd.coins-for-change.v1+json

# FastAPI router setup
v1_router = APIRouter(prefix="/api/v1")
v2_router = APIRouter(prefix="/api/v2")

app.include_router(v1_router)
app.include_router(v2_router)
```

### Backward Compatibility
```python
# Maintain backward compatibility
class CampaignResponseV1(BaseModel):
    id: UUID
    title: str
    description: str
    status: str  # String enum for v1

class CampaignResponseV2(BaseModel):
    id: UUID
    title: str
    description: str
    status: CampaignStatus  # Proper enum for v2
    campaign_type: CampaignType  # New field in v2
    
# Deprecation headers
@router.get("/campaigns", deprecated=True)
async def list_campaigns_v1():
    """V1 endpoint - deprecated, use V2"""
    response.headers["Deprecation"] = "true"
    response.headers["Sunset"] = "2024-12-31"
    response.headers["Link"] = '</api/v2/campaigns>; rel="successor-version"'
```

## Rate Limiting and Throttling

### Rate Limit Headers
```python
# Standard rate limit headers
X-RateLimit-Limit: 100        # Requests allowed per window
X-RateLimit-Remaining: 87     # Requests remaining in window
X-RateLimit-Reset: 1641811800 # Unix timestamp when window resets
X-RateLimit-Window: 3600      # Window size in seconds

# Rate limit exceeded response
HTTP/1.1 429 Too Many Requests
Retry-After: 3600

{
  "error_code": "RATE_LIMIT_001",
  "message": "Rate limit exceeded",
  "details": {
    "limit": 100,
    "window": 3600,
    "retry_after": 3600
  },
  "timestamp": "2024-01-10T10:30:00Z",
  "request_id": "req_123456789"
}
```

### Rate Limiting Implementation
```python
# Different limits for different endpoints
RATE_LIMITS = {
    "auth": "5/minute",           # Authentication endpoints
    "campaigns": "100/hour",      # Campaign operations
    "ideas": "200/hour",          # Idea operations
    "coins": "500/hour",          # Coin operations (higher frequency)
    "search": "1000/hour",        # Search operations
}

# Rate limiting decorator
@rate_limit("campaigns")
@router.post("/campaigns")
async def create_campaign():
    # Implementation
```

## Documentation Standards

### OpenAPI Documentation
```python
# Comprehensive endpoint documentation
@router.post(
    "/campaigns/{campaign_id}/ideas",
    response_model=IdeaResponse,
    status_code=201,
    summary="Submit new idea to campaign",
    description="Submit a new idea to the specified campaign. Ideas may require approval in mediated campaigns.",
    responses={
        201: {"description": "Idea created successfully"},
        400: {"description": "Invalid input data"},
        403: {"description": "Not authorized to submit ideas to this campaign"},
        404: {"description": "Campaign not found"},
        422: {"description": "Business logic validation failed"}
    },
    tags=["Ideas"]
)
async def submit_idea(
    campaign_id: UUID = Path(..., description="Campaign ID"),
    idea_data: IdeaCreateRequest = Body(..., description="Idea data"),
    current_user: User = Depends(get_current_user)
) -> IdeaResponse:
    """
    Submit a new idea to a campaign.
    
    This endpoint allows campaign members to submit new ideas for consideration.
    In mediated campaigns, ideas will be queued for approval by campaign managers.
    
    **Business Rules:**
    - User must be a member of the campaign
    - Campaign must be in active status
    - Idea title and description are required
    - Tags must be from the campaign's approved tag list
    
    **Example Request:**
    ```json
    {
      "title": "Mobile App Dark Mode",
      "description": "Add dark mode support to improve user experience",
      "tag_ids": ["550e8400-e29b-41d4-a716-446655440001"]
    }
    ```
    """
```

### API Examples and Tutorials
```markdown
# API Usage Examples

## Authentication Flow
1. Register or login to get JWT token
2. Include token in Authorization header for all requests
3. Refresh token before expiration

## Campaign Workflow
1. Create campaign (admin/manager only)
2. Configure campaign settings and policies
3. Invite members to campaign
4. Activate campaign to allow idea submission
5. Monitor participation and analytics

## Idea Submission and Coin Allocation
1. Submit idea to active campaign
2. Wait for approval (if mediated campaign)
3. Allocate coins to prioritize ideas
4. Reallocate coins as needed (if policy allows)
5. Track idea progress through lifecycle
```

## Performance Considerations

### Response Time Guidelines
- **Authentication**: < 200ms
- **Simple queries**: < 500ms
- **Complex queries**: < 2s
- **Search operations**: < 1s
- **Bulk operations**: < 5s

### Caching Strategy
```python
# Cache frequently accessed data
@cache(expire=300)  # 5 minutes
async def get_campaign_summary(campaign_id: UUID):
    # Expensive calculation
    
# Cache headers for client-side caching
@router.get("/campaigns/{campaign_id}")
async def get_campaign(campaign_id: UUID):
    response.headers["Cache-Control"] = "public, max-age=300"
    response.headers["ETag"] = f'"{campaign.updated_at.timestamp()}"'
```

### Bulk Operations
```python
# Bulk operations for efficiency
@router.post("/campaigns/{campaign_id}/coins/bulk-allocate")
async def bulk_allocate_coins(
    campaign_id: UUID,
    allocations: List[CoinAllocationRequest] = Body(..., max_items=100)
):
    """Allocate coins to multiple ideas in a single transaction"""
    # Process all allocations atomically
```