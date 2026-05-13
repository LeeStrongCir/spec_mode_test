// Spec: specs/001-register-login/spec.md
// Aggregate MSW handlers — imports per-module handler groups

import { authHandlers } from './handlers/auth'

export const handlers = [
  ...authHandlers,
]
