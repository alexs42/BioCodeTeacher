import { test, expect } from '@playwright/test'
import { resolve } from 'path'

const REPO_PATH = resolve(__dirname, '..')

test.describe('Backend API Health', () => {
  test('GET / should return service info', async ({ request }) => {
    const response = await request.get('http://localhost:8000/')
    expect(response.ok()).toBeTruthy()
    const data = await response.json()
    expect(data.status).toBe('ok')
    expect(data.service).toBe('CodeTeacher API')
  })

  test('GET /api/health should return healthy status', async ({ request }) => {
    const response = await request.get('http://localhost:8000/api/health')
    expect(response.ok()).toBeTruthy()
    const data = await response.json()
    expect(data.status).toBe('healthy')
    expect(data.features.streaming).toBe(true)
    expect(data.features.local_repos).toBe(true)
    expect(data.features.github_clone).toBe(true)
  })
})

test.describe('Backend API - Repository Management', () => {
  let repoId: string

  test('POST /api/repos/load should load local repo', async ({ request }) => {
    const response = await request.post('http://localhost:8000/api/repos/load', {
      data: { path: REPO_PATH }
    })
    expect(response.ok()).toBeTruthy()
    const data = await response.json()
    expect(data.success).toBe(true)
    expect(data.repo_id).toBeTruthy()
    expect(data.file_tree).toBeTruthy()
    expect(data.file_count).toBeGreaterThan(0)
    repoId = data.repo_id
  })

  test('POST /api/repos/load should reject invalid path', async ({ request }) => {
    const response = await request.post('http://localhost:8000/api/repos/load', {
      data: { path: '/nonexistent/path' }
    })
    expect(response.status()).toBe(400)
  })

  test('POST /api/repos/load should reject empty payload', async ({ request }) => {
    const response = await request.post('http://localhost:8000/api/repos/load', {
      data: {}
    })
    expect(response.status()).toBe(400)
  })
})

test.describe('Backend API - File Operations', () => {
  let repoId: string

  test.beforeAll(async ({ request }) => {
    const response = await request.post('http://localhost:8000/api/repos/load', {
      data: { path: REPO_PATH }
    })
    const data = await response.json()
    repoId = data.repo_id
  })

  test('GET /api/files/content should return file content', async ({ request }) => {
    const response = await request.get('http://localhost:8000/api/files/content', {
      params: { repo_id: repoId, file_path: 'backend/main.py' }
    })
    expect(response.ok()).toBeTruthy()
    const data = await response.json()
    expect(data.path).toBe('backend/main.py')
    expect(data.language).toBe('python')
    expect(data.content).toContain('FastAPI')
    expect(data.line_count).toBeGreaterThan(0)
  })

  test('GET /api/files/content should return 404 for missing file', async ({ request }) => {
    const response = await request.get('http://localhost:8000/api/files/content', {
      params: { repo_id: repoId, file_path: 'nonexistent.py' }
    })
    expect(response.status()).toBe(404)
  })

  test('GET /api/files/tree should return file tree', async ({ request }) => {
    const response = await request.get('http://localhost:8000/api/files/tree', {
      params: { repo_id: repoId }
    })
    expect(response.ok()).toBeTruthy()
    const data = await response.json()
    expect(data.file_tree).toBeTruthy()
    expect(data.file_count).toBeGreaterThan(0)
  })
})

test.describe('Backend API - Explain Endpoints (schema validation)', () => {
  test('POST /api/explain/line should require api_key', async ({ request }) => {
    const response = await request.post('http://localhost:8000/api/explain/line', {
      data: {
        repo_id: 'test',
        file_path: 'test.py',
        line_number: 1,
      }
    })
    expect(response.status()).toBe(422)
  })

  test('POST /api/explain/line should reject line_number 0', async ({ request }) => {
    const response = await request.post('http://localhost:8000/api/explain/line', {
      data: {
        api_key: 'test-key',
        repo_id: 'test',
        file_path: 'test.py',
        line_number: 0,
      }
    })
    expect(response.status()).toBe(422)
  })

  test('POST /api/explain/architecture should require api_key', async ({ request }) => {
    const response = await request.post('http://localhost:8000/api/explain/architecture', {
      data: {
        repo_id: 'test',
      }
    })
    expect(response.status()).toBe(422)
  })
})

test.describe('Backend API - Chat Endpoint (schema validation)', () => {
  test('POST /api/chat/ should require api_key', async ({ request }) => {
    const response = await request.post('http://localhost:8000/api/chat/', {
      data: {
        repo_id: 'test',
        message: 'hello',
      }
    })
    expect(response.status()).toBe(422)
  })
})
