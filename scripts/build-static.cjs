const fs = require('fs')
const path = require('path')
const { execSync } = require('child_process')

const apiRoute = path.resolve(__dirname, '..', 'src', 'app', 'api', 'analyze', 'route.ts')
const backup = apiRoute + '.bak'
const envFile = path.resolve(__dirname, '..', '.env.static')

try {
  // Backup API route
  if (fs.existsSync(apiRoute)) {
    fs.copyFileSync(apiRoute, backup)
    fs.unlinkSync(apiRoute)
    console.log('API route backed up and removed for static export')
  }

  // Build Next.js static export with Vercel API URL for Tauri
  execSync('npx next build', {
    cwd: path.resolve(__dirname, '..'),
    stdio: 'inherit',
    env: {
      ...process.env,
      NEXT_STATIC_EXPORT: 'true',
      NEXT_PUBLIC_VERCEL_URL: 'crypto-analysis-7ptemnims-rod773s-projects.vercel.app',
    },
  })

  // Ensure out/.nojekyll exists
  const outDir = path.resolve(__dirname, '..', 'out')
  if (fs.existsSync(outDir)) {
    fs.writeFileSync(path.join(outDir, '.nojekyll'), '')
    console.log('Created .nojekyll in out/')
  }
} finally {
  // Restore API route
  if (fs.existsSync(backup)) {
    fs.copyFileSync(backup, apiRoute)
    fs.unlinkSync(backup)
    console.log('API route restored')
  }
}
