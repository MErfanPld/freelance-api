# Collaborative Project Management — Backend Integration Contract

## Authentication

All endpoints require `Authorization: Bearer <access_token>` except auth routes.

User unique public ID is the existing UUID `id` field (string, 36 chars). Do **not** expose email in public lookup responses.

## New / Updated Endpoints

### Current user public ID
- `GET /api/v1/users/me/public-id`
- Auth required (Bearer access token).
- Response: `{ "id": "<uuid>" }` — only the authenticated user's own UUID.
- 401 if missing/invalid token.
- Does not accept a user id from path or query; cannot be used to look up another user.
- For profile display and copy-to-clipboard before sharing with a project owner.

### User public lookup
- `GET /api/v1/users/{user_id}/public`
- Response: `{ "id", "first_name", "last_name" }`
- 404 if not found / inactive. No email or private data.

### Project invitations & members
- `POST /api/v1/projects/{project_id}/invitations`  
  Body: `{ "user_id": "<uuid>", "role": "member" | "owner" }` (default member)  
  Owner only. 201, 400 self-invite, 409 duplicate active/pending.
- `POST /api/v1/projects/{project_id}/invitations/accept` — invitee only
- `POST /api/v1/projects/{project_id}/invitations/reject` — invitee only
- `DELETE /api/v1/projects/{project_id}/invitations/{member_id}` — cancel pending (owner)
- `GET /api/v1/projects/{project_id}/members?status=` — active members by default if omitted
- `POST /api/v1/projects/{project_id}/leave` — non-owner members
- `DELETE /api/v1/projects/{project_id}/members/{member_id}` — remove active non-owner (owner)

### Membership roles & statuses
- Roles: `owner`, `member`
- Statuses: `pending`, `active`, `rejected`, `left`, `removed`
- Project.user_id remains the canonical owner. Owner cannot leave or be removed.

### Projects
Existing CRUD preserved. List/get now include projects the user owns **or** is an active member of.  
Update/delete/archive restricted to owner.

Project statuses: `pending`, `in_progress`, `completed`, `cancelled` (use cancelled for archive).

### Tasks
- Create/Update accept optional `assignee_id`.
- Response includes `created_by_id`, `assignee_id`.
- Assignee must be an active project member.
- Access requires active membership (or ownership).

### Payments (income/expense)
Existing endpoints. Access now via active membership.  
Types: `income` | `expense`. Statuses: `paid` | `unpaid`.  
Amounts: Decimal with 2 places. Summary fields unchanged: total_income, total_expense, profit, etc.

### Notifications
Persisted for invitation events. (List/mark-read endpoints can be added later; records are created on invite/accept/reject.)

## Validation & errors
Consistent with existing API:  
`{ "success": false, "data": [...], "message": "..." }` for errors.  
HTTP 401/403/404/409/422 as appropriate. Cross-project access returns 404.

## Pagination
Unchanged: `page`, `page_size` → `{ items, total, page, page_size, pages }`.

## Migrations
Revision `a1b2c3d4e5f6_add_collaboration` adds `project_members`, `notifications`, and task assignee/creator columns.  
Run: `alembic upgrade head`.

## Breaking changes
None for existing personal workflows. New projects automatically create an active owner membership.
