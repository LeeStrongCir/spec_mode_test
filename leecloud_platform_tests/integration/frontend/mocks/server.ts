// Spec: specs/001-register-login/spec.md
// MSW Node server setup for Vitest integration tests

import { setupServer } from 'msw/node'
import { handlers } from './handlers'

export const server = setupServer(...handlers)
