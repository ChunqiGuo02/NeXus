# Architecture Reference

## Main modules
- src/components: presentation only
- src/domain: business logic
- src/data: database and persistence
- src/api: route handlers and API entry points

## Allowed dependencies
- api -> domain
- domain -> data
- components -> api
- components must not import data directly

## Forbidden shortcuts
- route handlers must not call the database directly
- presentation components must not contain mutation logic

## Verification commands
- test: pnpm test
- lint: pnpm lint
- build: pnpm build

## Project-specific pitfalls
- Keep all timestamps in UTC.
- Preserve existing error response shape.
- Any new route must follow the current validation pattern.