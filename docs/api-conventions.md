# API conventions

- Base path: `/api/v1`
- JSON fields: `snake_case`
- Timestamps: ISO 8601 UTC
- Pagination: `page`, `page_size`, response fields `items`, `total`, `page`, `page_size`
- Authentication: `Authorization: Bearer <access-token>`

Errors use:

```json
{
  "error": {
    "code": "resource_not_found",
    "message": "Resource was not found",
    "details": null,
    "request_id": "..."
  }
}
```

