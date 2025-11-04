/**
 * Test frontend project structure - Story 1.1
 * Tests for AC2: Frontend structure validation
 */

import { describe, it, expect } from 'vitest'
import { existsSync, statSync } from 'fs'
import { join } from 'path'

describe('Frontend Project Structure', () => {
  const srcPath = join(__dirname, '..')

  describe('AC2: Required directories exist', () => {
    it('should have src directory', () => {
      expect(existsSync(srcPath)).toBe(true)
      expect(statSync(srcPath).isDirectory()).toBe(true)
    })

    it('should have components directory', () => {
      const componentsPath = join(srcPath, 'components')
      expect(existsSync(componentsPath)).toBe(true)
      expect(statSync(componentsPath).isDirectory()).toBe(true)
    })

    it('should have views directory', () => {
      const viewsPath = join(srcPath, 'views')
      expect(existsSync(viewsPath)).toBe(true)
      expect(statSync(viewsPath).isDirectory()).toBe(true)
    })

    it('should have stores directory (Pinia)', () => {
      const storesPath = join(srcPath, 'stores')
      expect(existsSync(storesPath)).toBe(true)
      expect(statSync(storesPath).isDirectory()).toBe(true)
    })

    it('should have router directory', () => {
      const routerPath = join(srcPath, 'router')
      expect(existsSync(routerPath)).toBe(true)
      expect(statSync(routerPath).isDirectory()).toBe(true)
    })

    it('should have services directory', () => {
      const servicesPath = join(srcPath, 'services')
      expect(existsSync(servicesPath)).toBe(true)
      expect(statSync(servicesPath).isDirectory()).toBe(true)
    })

    it('should have types directory', () => {
      const typesPath = join(srcPath, 'types')
      expect(existsSync(typesPath)).toBe(true)
      expect(statSync(typesPath).isDirectory()).toBe(true)
    })
  })

  describe('AC2: Required core files exist', () => {
    it('should have main.ts entry point', () => {
      const mainPath = join(srcPath, 'main.ts')
      expect(existsSync(mainPath)).toBe(true)
      expect(statSync(mainPath).isFile()).toBe(true)
    })

    it('should have App.vue root component', () => {
      const appPath = join(srcPath, 'App.vue')
      expect(existsSync(appPath)).toBe(true)
      expect(statSync(appPath).isFile()).toBe(true)
    })

    it('should have router index.ts', () => {
      const routerIndexPath = join(srcPath, 'router', 'index.ts')
      expect(existsSync(routerIndexPath)).toBe(true)
      expect(statSync(routerIndexPath).isFile()).toBe(true)
    })
  })

  describe('AC3: Package.json dependencies', () => {
    it('should have package.json', () => {
      const packageJsonPath = join(__dirname, '..', '..', 'package.json')
      expect(existsSync(packageJsonPath)).toBe(true)
    })

    it('should include required dependencies', () => {
      const packageJsonPath = join(__dirname, '..', '..', 'package.json')
      const packageJson = require(packageJsonPath)

      const requiredDeps = ['vue', 'vue-router', 'pinia']
      const requiredDevDeps = ['vite', 'vitest', 'typescript', '@vue/test-utils']

      requiredDeps.forEach((dep) => {
        expect(packageJson.dependencies).toHaveProperty(dep)
      })

      requiredDevDeps.forEach((dep) => {
        expect(packageJson.devDependencies).toHaveProperty(dep)
      })
    })
  })

  describe('Configuration files', () => {
    it('should have vite.config.ts', () => {
      const viteConfigPath = join(__dirname, '..', '..', 'vite.config.ts')
      expect(existsSync(viteConfigPath)).toBe(true)
    })

    it('should have vitest.config.ts', () => {
      const vitestConfigPath = join(__dirname, '..', '..', 'vitest.config.ts')
      expect(existsSync(vitestConfigPath)).toBe(true)
    })

    it('should have tsconfig.json', () => {
      const tsconfigPath = join(__dirname, '..', '..', 'tsconfig.json')
      expect(existsSync(tsconfigPath)).toBe(true)
    })

    it('should have .gitignore', () => {
      const gitignorePath = join(__dirname, '..', '..', '.gitignore')
      expect(existsSync(gitignorePath)).toBe(true)
    })
  })
})
