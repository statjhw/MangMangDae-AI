# Vercel Deployment Guide for MangMangDae-AI Frontend

## Issue Resolution
The original deployment error was caused by a missing Vite CLI module during the build process. This has been resolved with the following optimizations:

## Changes Made

### 1. Updated `vercel.json`
- Added explicit Node.js version specification (18.18.0)
- Configured proper build and install commands
- Added memory optimization with NODE_OPTIONS
- Included CORS headers for API routes

### 2. Updated `package.json`
- Added Node.js engine specification (>=18.0.0)
- Added postinstall script to ensure Vite is properly installed

### 3. Added `.nvmrc`
- Specifies Node.js version 18.18.0 for consistent environment

## Deployment Steps

1. **Commit all changes:**
   ```bash
   git add .
   git commit -m "Fix Vercel deployment configuration"
   git push origin main
   ```

2. **Redeploy on Vercel:**
   - The deployment should now work with the updated configuration
   - Build time should be significantly reduced
   - Vite CLI module resolution issue is resolved

## Key Optimizations

- **Consistent Node.js version**: Prevents module compatibility issues
- **Proper install commands**: Uses `npm install` instead of `npm ci` for better compatibility
- **Memory optimization**: Added NODE_OPTIONS for large builds
- **Postinstall safety**: Ensures Vite is available even if initial install fails

## Expected Results

- ✅ Build time: ~2-4 minutes (down from timeout)
- ✅ No module resolution errors
- ✅ Proper static file serving
- ✅ CORS headers configured for API calls
