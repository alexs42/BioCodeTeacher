import { test, expect } from '@playwright/test'
import { resolve } from 'path'

const REPO_PATH = process.env.TEST_REPO_PATH || resolve(__dirname, '..')

test.describe('CodeTeacher App - Initial Load', () => {
  test('should show setup modal on first visit', async ({ page }) => {
    await page.goto('/')
    await expect(page.getByText('Welcome to CodeTeacher')).toBeVisible()
    await expect(page.getByPlaceholder('sk-or-v1-...')).toBeVisible()
  })

  test('should show CodeTeacher header', async ({ page }) => {
    await page.goto('/')
    await expect(page.getByText('CodeTeacher').first()).toBeVisible()
  })

  test('should display model selection in setup', async ({ page }) => {
    await page.goto('/')
    const select = page.locator('select')
    await expect(select).toBeVisible()

    // Verify frontier models are listed
    await expect(select).toContainText('Claude Opus 4.6')
    await expect(select).toContainText('GPT-5.4')
    await expect(select).toContainText('Gemini 3.1 Pro')
    await expect(select).toContainText('Gemini 3.0 Flash')
  })

  test('Get Started button should be disabled without API key', async ({ page }) => {
    await page.goto('/')
    const button = page.getByRole('button', { name: /Get Started/i })
    await expect(button).toBeDisabled()
  })

  test('Get Started button should enable with API key', async ({ page }) => {
    await page.goto('/')
    await page.getByPlaceholder('sk-or-v1-...').fill('sk-or-v1-test123')
    const button = page.getByRole('button', { name: /Get Started/i })
    await expect(button).toBeEnabled()
  })
})

test.describe('CodeTeacher App - After Setup', () => {
  test.beforeEach(async ({ page }) => {
    // Set up localStorage with API key to skip setup modal
    await page.addInitScript(() => {
      localStorage.setItem('codeteacher-storage', JSON.stringify({
        state: {
          apiKey: 'sk-or-v1-test-key',
          githubToken: null,
          isDarkMode: true,
          selectedModel: 'anthropic/claude-opus-4.6',
          customModels: [],
        },
        version: 0,
      }))
    })
    await page.goto('/')
  })

  test('should not show setup modal when API key exists', async ({ page }) => {
    await expect(page.getByText('Welcome to CodeTeacher')).not.toBeVisible()
  })

  test('should show Open Repository button', async ({ page }) => {
    await expect(page.getByText('Open Repository')).toBeVisible()
  })

  test('should show settings button', async ({ page }) => {
    const settingsButton = page.getByTitle('Settings')
    await expect(settingsButton).toBeVisible()
  })

  test('should toggle dark/light mode', async ({ page }) => {
    // Should start in dark mode
    const html = page.locator('html')
    await expect(html).not.toHaveClass(/light/)

    // Click theme toggle
    const themeButton = page.getByTitle(/Light mode|Dark mode/)
    await themeButton.click()

    // Should now have 'light' class
    await expect(html).toHaveClass(/light/)
  })

  test('should open settings modal', async ({ page }) => {
    await page.getByTitle('Settings').click()
    await expect(page.getByText('AI Model Selection')).toBeVisible()
    await expect(page.getByText('Claude Opus 4.6')).toBeVisible()
  })

  test('settings should show all 4 frontier models', async ({ page }) => {
    await page.getByTitle('Settings').click()

    await expect(page.getByText('Claude Opus 4.6')).toBeVisible()
    await expect(page.getByText('GPT-5.4 (Thinking Medium)')).toBeVisible()
    await expect(page.getByText('Gemini 3.1 Pro')).toBeVisible()
    await expect(page.getByText('Gemini 3.0 Flash')).toBeVisible()
  })

  test('should select a different model', async ({ page }) => {
    await page.getByTitle('Settings').click()

    // Click on GPT-5.4
    await page.getByText('GPT-5.4 (Thinking Medium)').click()

    // The selection indicator (checkmark) should move
    const gpt54Card = page.locator('div').filter({ hasText: /GPT-5\.4 \(Thinking Medium\)/ }).first()
    await expect(gpt54Card).toBeVisible()
  })

  test('should add a custom model', async ({ page }) => {
    await page.getByTitle('Settings').click()
    await page.getByText('Add Custom Model').click()

    // Fill in custom model form
    await page.getByPlaceholder('e.g., anthropic/claude-3-opus').fill('test/custom-model')
    await page.getByPlaceholder('e.g., Claude 3 Opus').fill('My Custom Model')
    await page.getByPlaceholder('e.g., Anthropic').fill('TestProvider')

    await page.getByRole('button', { name: 'Add Model' }).click()

    // Custom model should appear
    await expect(page.getByText('My Custom Model')).toBeVisible()
  })

  test('should show repo input on Open Repository click', async ({ page }) => {
    await page.getByText('Open Repository').click()
    await expect(page.getByPlaceholder('Local path or GitHub URL...')).toBeVisible()
    await expect(page.getByRole('button', { name: 'Load' })).toBeVisible()
  })

  test('should close settings modal', async ({ page }) => {
    await page.getByTitle('Settings').click()
    await expect(page.getByText('AI Model Selection')).toBeVisible()

    await page.getByRole('button', { name: 'Done' }).click()
    await expect(page.getByText('AI Model Selection')).not.toBeVisible()
  })
})

test.describe('CodeTeacher App - Repository Loading', () => {
  test.beforeEach(async ({ page }) => {
    await page.addInitScript(() => {
      localStorage.setItem('codeteacher-storage', JSON.stringify({
        state: {
          apiKey: 'sk-or-v1-test-key',
          githubToken: null,
          isDarkMode: true,
          selectedModel: 'anthropic/claude-opus-4.6',
          customModels: [],
        },
        version: 0,
      }))
    })
    await page.goto('/')
  })

  test('should load a local repository', async ({ page }) => {
    await page.getByText('Open Repository').click()
    await page.getByPlaceholder('Local path or GitHub URL...').fill(REPO_PATH)
    await page.getByRole('button', { name: 'Load' }).click()

    // Wait for file tree to appear
    await expect(page.getByText('backend')).toBeVisible({ timeout: 10000 })
    await expect(page.getByText('frontend')).toBeVisible()
  })

  test('should show error for invalid path', async ({ page }) => {
    await page.getByText('Open Repository').click()
    await page.getByPlaceholder('Local path or GitHub URL...').fill('/nonexistent/path')
    await page.getByRole('button', { name: 'Load' }).click()

    // Should show error
    await expect(page.getByText(/not exist|failed/i)).toBeVisible({ timeout: 5000 })
  })
})

test.describe('CodeTeacher App - Code Browsing', () => {
  test.beforeEach(async ({ page }) => {
    await page.addInitScript(() => {
      localStorage.setItem('codeteacher-storage', JSON.stringify({
        state: {
          apiKey: 'sk-or-v1-test-key',
          githubToken: null,
          isDarkMode: true,
          selectedModel: 'anthropic/claude-opus-4.6',
          customModels: [],
        },
        version: 0,
      }))
    })
    await page.goto('/')

    // Load the CodeTeacher repo itself
    await page.getByText('Open Repository').click()
    await page.getByPlaceholder('Local path or GitHub URL...').fill(REPO_PATH)
    await page.getByRole('button', { name: 'Load' }).click()
    await expect(page.getByText('backend')).toBeVisible({ timeout: 10000 })
  })

  test('should display file tree with expandable directories', async ({ page }) => {
    // backend and frontend directories should be visible
    await expect(page.getByText('backend')).toBeVisible()
    await expect(page.getByText('frontend')).toBeVisible()
  })

  test('should close the repository', async ({ page }) => {
    await page.getByText('Close').click()
    // File tree should disappear
    await expect(page.getByText('Open Repository')).toBeVisible()
  })
})
