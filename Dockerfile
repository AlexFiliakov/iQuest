# Multi-stage build for Python application
FROM python:3.11-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements files
COPY requirements*.txt ./

# Install Python dependencies
RUN pip install --user --no-cache-dir -r requirements.txt

# Runtime stage
FROM python:3.11-slim

# Install runtime dependencies for Qt
RUN apt-get update && apt-get install -y \
    libxcb-icccm4 \
    libxcb-image0 \
    libxcb-keysyms1 \
    libxcb-randr0 \
    libxcb-render-util0 \
    libxcb-xinerama0 \
    libxcb-xfixes0 \
    libxkbcommon-x11-0 \
    libglib2.0-0 \
    libgl1-mesa-glx \
    libdbus-1-3 \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 appuser

# Set working directory
WORKDIR /app

# Copy Python dependencies from builder
COPY --from=builder /root/.local /home/appuser/.local

# Copy application code
COPY --chown=appuser:appuser . .

# Set environment variables
ENV PATH=/home/appuser/.local/bin:$PATH
ENV QT_QPA_PLATFORM=offscreen
ENV PYTHONUNBUFFERED=1

# Switch to non-root user
USER appuser

# Add labels
LABEL org.opencontainers.image.title="Apple Health Monitor"
LABEL org.opencontainers.image.description="Monitor and analyze Apple Health data"
LABEL org.opencontainers.image.vendor="Apple Health Monitor Project"
LABEL org.opencontainers.image.licenses="MIT"

# Default command
CMD ["python", "-m", "src.main"]