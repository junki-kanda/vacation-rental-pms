# AGENTS.md

## Scope
These instructions apply to the entire repository.

## General
- Use `rg` for text searches instead of `grep -R`.
- Follow existing code style: PEP8 for Python and the configured ESLint/Prettier rules for TypeScript.
- Do not commit generated files or dependencies (e.g., `node_modules`, build outputs).

## Testing
- If backend code is modified, run:
  ```bash
  cd backend
  pytest
  ```
- If frontend code is modified, run:
  ```bash
  cd frontend
  npm run lint
  ```

## Commit
- Keep commits focused and descriptive.
- Run the appropriate tests before committing.
