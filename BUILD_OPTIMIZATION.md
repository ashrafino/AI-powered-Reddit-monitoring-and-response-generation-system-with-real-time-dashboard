# Build Optimization Guide

This document explains the build optimizations implemented to reduce Docker build times from ~30 minutes to under 5 minutes.

## 🚀 Quick Start (Fast Development)

For the fastest development experience, use the development compose file:

```bash
# Fast development build (no Docker builds required!)
./scripts/fast-build.sh

# Or manually:
docker-compose -f docker-compose.dev.yml up -d
```

This skips Docker builds entirely and runs services directly from base images with volume mounts.

## 📊 Build Time Comparison

| Method | Build Time | Use Case |
|--------|------------|----------|
| Original Dockerfile | ~30 minutes | Production |
| Optimized Dockerfile | ~5-8 minutes | Production |
| Development Mode | ~2-3 minutes | Development |

## 🔧 Optimizations Implemented

### 1. Multi-Stage Dockerfile
- **Builder stage**: Installs dependencies with build tools
- **Production stage**: Copies only runtime dependencies
- **Result**: Smaller final image, better caching

### 2. Improved Layer Caching
- Dependencies installed before copying source code
- Separate layers for system and Python packages
- Better cache hit rates on code changes

### 3. Development Mode
- Uses base Python image directly
- Installs packages at runtime with volume caching
- No Docker builds required for development

### 4. Build Context Optimization
- Added comprehensive `.dockerignore`
- Excludes unnecessary files from build context
- Faster context transfer to Docker daemon

### 5. Parallel Builds
- Enabled Docker BuildKit
- Parallel service builds in docker-compose
- Concurrent dependency installation

## 🛠️ Usage

### Development (Fastest)
```bash
# Start development environment
./scripts/fast-build.sh

# Or with options
./scripts/fast-build.sh --clean --pull
```

### Production
```bash
# Build for production
./scripts/fast-build.sh --prod

# Or manually
export DOCKER_BUILDKIT=1
docker-compose build --parallel
docker-compose up -d
```

### Build Script Options
- `--dev` (default): Development mode, no builds
- `--prod`: Production mode with optimized builds
- `--clean`: Clean volumes and rebuild
- `--pull`: Pull latest base images
- `--help`: Show help

## 📁 File Structure

```
├── Dockerfile                 # Optimized multi-stage production build
├── docker-compose.yml         # Production compose with build caching
├── docker-compose.dev.yml     # Development compose (no builds)
├── .dockerignore             # Optimized build context
├── scripts/fast-build.sh     # Build automation script
└── BUILD_OPTIMIZATION.md     # This guide
```

## 🔍 Troubleshooting

### Slow Builds
1. **Enable BuildKit**: `export DOCKER_BUILDKIT=1`
2. **Use development mode**: `./scripts/fast-build.sh`
3. **Clean build**: `./scripts/fast-build.sh --clean`
4. **Check .dockerignore**: Ensure unnecessary files are excluded

### Cache Issues
```bash
# Clear Docker cache
docker system prune -a

# Rebuild without cache
docker-compose build --no-cache
```

### Development Issues
```bash
# Check service logs
docker-compose -f docker-compose.dev.yml logs -f backend-dev

# Restart specific service
docker-compose -f docker-compose.dev.yml restart backend-dev
```

## 💡 Tips for Faster Development

1. **Use development mode** for daily development
2. **Keep requirements.txt stable** to leverage pip cache
3. **Use volume mounts** for live code reloading
4. **Separate frontend and backend** development when possible

## 🔄 Migration from Old Setup

If you're migrating from the old slow build:

1. **Stop old containers**: `docker-compose down -v`
2. **Clean system**: `docker system prune -a`
3. **Use new script**: `./scripts/fast-build.sh`

## 📈 Performance Monitoring

The development environment includes performance monitoring:
- Enable in dashboard: Click "Perf ON" button
- Monitor build times with the build script
- Check Docker stats: `docker stats`

## 🎯 Next Steps

For even faster builds, consider:
- Using Docker layer caching in CI/CD
- Pre-built base images with dependencies
- Local development without Docker (using virtual environments)

---

**Need help?** Check the logs or create an issue with your build output.