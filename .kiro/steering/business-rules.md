# Business Rules and Domain Logic

This document defines the core business rules and domain logic for the Coins for Change platform.

## Campaign Business Rules

### Campaign Lifecycle
1. **Campaign States**: draft → active → completed → archived
2. **State Transitions**:
   - Only system admins can create campaigns (initial state: draft)
   - Only campaign managers can activate campaigns (draft → active)
   - Only campaign managers can complete campaigns (active → completed)
   - Only system admins can archive campaigns (completed → archived)
3. **State Restrictions**:
   - Ideas can only be submitted to active campaigns
   - Coins can only be allocated in active campaigns
   - Campaign settings cannot be modified once active (except by admins)

### Campaign Types
1. **Open Campaigns**: Anyone can join and submit ideas immediately
2. **Mediated Campaigns**: Ideas require approval before becoming visible/competing
3. **Closed Campaigns**: Only invited members can participate

### Campaign Membership
1. **Roles**: campaign_manager, campaign_member
2. **Permissions**:
   - **Campaign Managers**: Can invite members, approve ideas, configure settings, accept ideas
   - **Campaign Members**: Can submit ideas, allocate coins, view campaign content
3. **Invitation Rules**:
   - Only campaign managers can invite new members
   - Invitations expire after 7 days
   - Users can be members of multiple campaigns simultaneously

## Coin Economy Rules

### Coin Allocation Principles
1. **Campaign Isolation**: Coins are strictly campaign-specific and cannot cross campaign boundaries
2. **Conservation**: Total allocated coins in a campaign never exceed total distributed coins
3. **Non-Negative Balances**: User coin balances cannot go negative
4. **Atomic Operations**: All coin operations must be atomic (all succeed or all fail)

### Coin Lifecycle
1. **Initial Distribution**: All campaign members receive initial coin allocation when campaign becomes active
2. **Event Rewards**: Users can earn bonus coins for specific actions (configurable per campaign)
3. **Allocation**: Users can allocate coins to ideas in competing status
4. **Reallocation**: Users can move coins between ideas (if policy allows and ideas not accepted)
5. **Expiration**: Coins become expended when ideas are accepted (cannot be reallocated)
6. **Recycling**: Coins return to user balance when ideas are withdrawn (if policy allows)

### Coin Policies (Configurable per Campaign)
```python
class CoinPolicy:
    initial_allocation: int = 100          # Coins given to each member
    idea_submission_reward: int = 0        # Bonus coins for submitting ideas
    allow_reallocation: bool = True        # Can users move coins between ideas
    allow_recycling: bool = True           # Do coins return when ideas withdrawn
    max_allocation_per_idea: int = None    # Optional limit per idea
    min_allocation_amount: int = 1         # Minimum coins per allocation
```

### Coin Operation Rules
1. **Allocation Requirements**:
   - User must have sufficient available coins
   - Idea must be in "competing" status
   - Campaign must be active
   - Amount must be positive and within policy limits
2. **Reallocation Requirements**:
   - Original idea must not be accepted (coins not expended)
   - Target idea must be in competing status
   - Reallocation policy must be enabled
   - Same campaign boundary restrictions apply
3. **Expiration Triggers**:
   - When idea status changes to "accepted"
   - All coins allocated to that idea become expended
   - Users cannot reallocate expended coins

## Idea Management Rules

### Idea Lifecycle
1. **Idea States**: pending → competing → accepted → in_progress → complete
2. **State Transitions**:
   - **pending → competing**: Campaign manager approval (required for mediated campaigns)
   - **competing → accepted**: Campaign manager decision (coins become expended)
   - **accepted → in_progress**: Campaign manager marks implementation started
   - **in_progress → complete**: Campaign manager marks implementation finished
3. **Coin Interaction**:
   - Coins can only be allocated to ideas in "competing" status
   - Once idea is "accepted", all associated coins are expended
   - Ideas in other states cannot receive coin allocations

### Idea Submission Rules
1. **Required Fields**: title, description
2. **Validation Rules**:
   - Title: 1-255 characters, no HTML tags
   - Description: 1-5000 characters, rich text allowed
   - Tags: Must be from campaign's approved tag list
3. **Duplicate Detection**:
   - System performs fuzzy matching on title and description
   - Shows similar ideas with similarity scores
   - Users can proceed despite similarities (with warning)
   - Campaign managers can merge duplicate ideas

### Idea Modification Rules
1. **Who Can Modify**:
   - Idea submitter: Can edit title, description, tags (before acceptance)
   - Campaign managers: Can edit any field, change status
2. **Modification Restrictions**:
   - Cannot modify accepted ideas (except status transitions)
   - Major changes trigger notifications to coin supporters
   - Version history maintained for audit trail

## Tag Management Rules

### Tag Hierarchy
1. **Tag Types**: category, feature, priority, platform
2. **Hierarchical Structure**: Optional parent-child relationships
3. **Campaign Scope**: Tags are campaign-specific
4. **Tag Lifecycle**: active → retired (soft delete, preserve history)

### Tag Application Rules
1. **Assignment**: Ideas can have multiple tags
2. **Validation**: All tags must belong to the same campaign
3. **Permalink Integration**: External platforms can pre-assign tags via context
4. **Search Integration**: Tags are indexed for filtering and search

## Platform Integration Rules

### Permalink System
1. **Context Isolation**: Each permalink has unique context_id
2. **Tag Pre-population**: Permalinks can specify default tags
3. **Account Creation**: Streamlined signup for permalink users
4. **Tracking**: All ideas submitted via permalink are associated with context_id
5. **API Access**: External platforms can query ideas by context_id

### External Platform Rules
1. **Authentication**: API keys required for external platform access
2. **Rate Limiting**: Different limits for authenticated vs. anonymous access
3. **Data Access**: Platforms can only access their own context data
4. **Webhooks**: Optional notifications for idea status changes

## Notification Rules

### Notification Types and Triggers
1. **Campaign Events**:
   - Campaign invitation received
   - Campaign status changes (activated, completed)
   - Campaign deadline approaching
2. **Idea Events**:
   - Idea submitted (to campaign managers in mediated campaigns)
   - Idea approved/rejected
   - Idea accepted (to coin supporters)
   - Idea status changes (in_progress, complete)
3. **Coin Events**:
   - Coins allocated to your idea
   - Your allocated coins expended (idea accepted)
   - Coin balance changes

### Notification Delivery Rules
1. **Channels**: email, in-app, webhook (for external platforms)
2. **Preferences**: Users can configure per-notification-type preferences
3. **Batching**: Multiple similar notifications can be batched (configurable)
4. **Retry Logic**: Failed email deliveries retry with exponential backoff
5. **Unsubscribe**: Users can unsubscribe from specific notification types

## Security and Access Control Rules

### Authentication Rules
1. **Password Requirements**: Minimum 8 characters, mixed case, numbers
2. **Session Management**: JWT tokens with 24-hour expiration
3. **Account Lockout**: 5 failed attempts locks account for 15 minutes
4. **Password Reset**: Secure token valid for 1 hour

### Authorization Hierarchy
1. **System Admin**: Full system access, can create campaigns, manage users
2. **System Sponsor**: Read-only access to analytics and reports across all campaigns
3. **Campaign Manager**: Full access within assigned campaigns
4. **Campaign Member**: Limited access within joined campaigns

### Data Access Rules
1. **Campaign Isolation**: Users can only access campaigns they're members of
2. **Idea Visibility**: Ideas only visible to campaign members (except public campaigns)
3. **Personal Data**: Users can only modify their own profile and allocations
4. **Analytics Access**: Role-based access to different levels of analytics detail

## Validation and Constraints

### Data Integrity Rules
1. **Referential Integrity**: All foreign keys must reference valid records
2. **Coin Conservation**: Sum of allocated + available coins = total distributed coins
3. **Campaign Membership**: Cannot allocate coins without campaign membership
4. **Temporal Constraints**: End dates must be after start dates

### Business Logic Constraints
1. **Unique Campaign IDs**: Campaign identifiers must be unique across system
2. **Email Uniqueness**: User email addresses must be unique
3. **Tag Name Uniqueness**: Tag names must be unique within each campaign
4. **Allocation Limits**: Coin allocations must respect campaign policy limits

### Performance Constraints
1. **Pagination**: Large result sets must be paginated (max 100 items per page)
2. **Search Limits**: Search queries limited to prevent resource exhaustion
3. **Rate Limits**: API endpoints have rate limits to prevent abuse
4. **File Size Limits**: Uploaded assets limited to reasonable sizes

## Error Handling Rules

### Error Categories
1. **Validation Errors**: Invalid input data (400 Bad Request)
2. **Authentication Errors**: Invalid credentials (401 Unauthorized)
3. **Authorization Errors**: Insufficient permissions (403 Forbidden)
4. **Not Found Errors**: Resource doesn't exist (404 Not Found)
5. **Business Logic Errors**: Rule violations (422 Unprocessable Entity)
6. **System Errors**: Internal failures (500 Internal Server Error)

### Error Response Format
```json
{
  "error_code": "COIN_001",
  "message": "Insufficient coins for allocation",
  "details": {
    "requested_amount": 50,
    "available_balance": 30,
    "campaign_id": "uuid"
  },
  "timestamp": "2024-01-15T10:30:00Z",
  "request_id": "req_123456"
}
```

### Logging Requirements
1. **Error Logging**: All errors logged with full context
2. **Audit Logging**: All state changes logged for compliance
3. **Performance Logging**: Slow operations logged for optimization
4. **Security Logging**: Authentication events and permission checks logged