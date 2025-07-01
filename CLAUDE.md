# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a professional-grade Python application that downloads GPS data from Strava and generates high-quality SVG heatmaps. The application has been extensively refactored (2025-07-01) to use modular utilities, centralized configuration, and robust error handling. It consists of main scripts supported by specialized utility modules.

## Common Commands

### Environment Setup
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Data Download
```bash
# Primary download method (recommended)
python download_strava_data.py

# Alternative: Individual activity download
python download_individual_activities.py
```
- Downloads GPS data from Strava API using centralized utilities
- Creates `config.json` on first run (needs manual configuration)
- Automatically handles token refresh and rate limiting via `strava_auth.py`
- Uses `strava_files.py` for consistent file management
- Saves data to `strava_data/` directory with progress reporting

### Data Consolidation
```bash
python consolidate_gps_data.py
```
- Consolidates individual activity files into unified GPS dataset
- Uses `heatmap_utils.py` for data validation and summary
- Creates timestamped and latest versions automatically

### Heatmap Generation
```bash
python generate_heatmap_svg.py
```
- Generates SVG heatmap from consolidated data
- Uses `heatmap_utils.py` for optimization and validation
- Creates `strava_heatmap.svg` output file with geographic boundaries

### Utilities and Development
```bash
# Check rate limit status
python check_rate_limit.py

# Get new tokens with OAuth flow
python get_new_token.py

# Background download with resume capability
python background_download.py
```

## Refactored Architecture (2025-07-01)

### 🚀 Main Application Scripts

**Entry Points:**
- `download_strava_data.py`: Main download script (108 lines, 47% reduction from refactoring)
- `download_individual_activities.py`: Individual activity download (117 lines, 46% reduction)
- `consolidate_gps_data.py`: Data consolidation with validation (141 lines, enhanced functionality)
- `generate_heatmap_svg.py`: Heatmap generation with validation (230 lines, enhanced with error handling)

**Supporting Scripts:**
- `background_download.py`: Long-running download with resume capability
- `check_rate_limit.py`: Real-time API rate limit monitoring
- `get_new_token.py`: OAuth token acquisition helper

### 🔧 Strava Utility Modules (New Architecture)

**`strava_config.py` (251 lines):**
- Centralized configuration management with validation
- Automatic default config generation
- Type-safe configuration access with dot notation
- Configuration validation and error reporting
- Token management integration

**`strava_auth.py` (242 lines):**
- Unified authentication and rate limiting
- Automatic token refresh and persistence
- Rate limit detection and waiting with progress display
- Keyboard-interruptible waiting (1-second chunks)
- Integration with `strava_config.py` for credential management

**`strava_files.py` (360 lines):**
- Standardized file operations across all scripts
- Automatic timestamp and latest file generation
- Safe filename generation (handles Unicode activity names)
- Individual activity file loading and consolidation
- Consistent JSON file handling with error recovery

**`strava_progress.py` (343 lines):**
- Unified progress reporting and statistics
- Real-time activity processing logs
- Performance metrics and ETA estimation
- Standardized summary reports
- Rate limit usage tracking

**`strava_utils.py` (428 lines):**
- Common helper functions and data validation
- Activity type filtering and GPS data validation
- Error handling utilities and keyboard interrupt management
- Filename sanitization and date extraction
- Python version checking and environment validation

### 🗺️ Heatmap Core Modules

**`heatmap_generator.py`:**
- Bresenham line algorithm for GPS track rendering
- Configurable grid resolution and bounds calculation
- Efficient coordinate transformation and mapping

**`heatmap_utils.py` (311 lines, new):**
- GPS data structure validation and integrity checking
- Geographic bounds calculation and filtering
- Heatmap resolution optimization based on data density
- Processing time estimation and performance metrics
- Configuration validation for heatmap-specific settings

**`map_data.py`:**
- Geographic boundary data download and caching
- World borders and US state boundaries
- Automatic boundary filtering based on GPS bounds
- Local caching for performance (`map_cache/` directory)

**`svg_renderer.py`:**
- SVG generation with equirectangular projection
- Geographic coordinate to SVG space transformation
- Boundary path rendering and GPS track visualization
- Title and legend generation

### 🔗 Strava Integration

**`strava_client.py`:**
- Strava API client with automatic token management
- Integrated rate limiting with `StravaRateLimiter` class
- Individual activity download and GPS data extraction
- Robust error handling for 401/429 responses

## Data Flow and Processing Pipeline

### Enhanced Data Pipeline (Post-Refactoring)

```mermaid
flowchart TD
    A[Strava API] --> B[strava_auth.py Authentication]
    B --> C[strava_client.py Download]
    C --> D[strava_files.py File Management]
    D --> E[Individual Activity Files]
    E --> F[consolidate_gps_data.py]
    F --> G[heatmap_utils.py Validation]
    G --> H[Unified GPS Data]
    H --> I[generate_heatmap_svg.py]
    I --> J[heatmap_generator.py Processing]
    J --> K[SVG Heatmap Output]
    
    L[Map APIs] --> M[map_data.py]
    M --> N[Geographic Boundaries]
    N --> I
    
    O[strava_config.py] --> B
    O --> C
    O --> F
    O --> I
    
    P[strava_progress.py] --> C
    P --> F
    P --> I
```

### Processing Steps

1. **Configuration**: `strava_config.py` loads and validates settings
2. **Authentication**: `strava_auth.py` handles OAuth flow and rate limiting
3. **Download**: Main scripts use `strava_client.py` with utilities
4. **File Management**: `strava_files.py` handles all file operations
5. **Progress Tracking**: `strava_progress.py` provides real-time feedback
6. **Data Validation**: `heatmap_utils.py` ensures data integrity
7. **Heatmap Generation**: Core modules generate final SVG output

## Configuration Management

### Centralized Configuration via `strava_config.py`

**Complete config.json structure:**
```json
{
  "strava": {
    "client_id": "YOUR_CLIENT_ID",
    "client_secret": "YOUR_CLIENT_SECRET", 
    "access_token": "YOUR_ACCESS_TOKEN",
    "refresh_token": "YOUR_REFRESH_TOKEN"
  },
  "data": {
    "output_dir": "strava_data",
    "gps_data_file": "gps_data.json"
  },
  "output": {
    "filename": "strava_heatmap.svg",
    "width": 1200,
    "height": 800
  },
  "style": {
    "track_color": "#dc3545",
    "track_width": "1.5",
    "boundary_color": "#dee2e6", 
    "boundary_width": "0.5"
  },
  "download": {
    "max_years": 8,
    "batch_size": 50,
    "retry_attempts": 3,
    "retry_delay": 300,
    "save_progress_interval": 10
  }
}
```

**Configuration Features:**
- Automatic validation and error reporting
- Default value generation for missing sections
- Type checking and range validation
- Dot notation access (`config.get("strava.client_id")`)
- Token update and persistence

## Dependencies

### Core Dependencies
- `requests>=2.25.0`: HTTP client for API calls
- `numpy>=1.21.0`: Numerical operations for heatmap grid (optional for utilities)
- Built-in libraries: `xml.etree.ElementTree`, `json`, `os`, `math`, `typing`

### Python Version Support
- **Tested**: Python 3.9.6 and 3.12
- **Minimum**: Python 3.8+ (for typing features)

## File Management System

### 📁 Enhanced File Organization

**Individual Activity Files:**
```
activity_YYYYMMDD_ACTIVITYID_activityname.json
Example: activity_20250629_14957284575_ランチタイム_ライド.json
```
- Complete activity metadata and GPS points
- Safe filename generation handling Unicode
- Automatic activity type and date extraction

**Consolidated Data Files:**
```
gps_data_YYYYMMDD_HHMMSS.json       # Timestamped backup
gps_data_latest.json                # Latest version (auto-generated)
athlete_info_latest.json            # Athlete information
```

**Output Files:**
```
strava_heatmap.svg                  # Generated heatmap
map_cache/                          # Geographic boundary cache
```

### 🔄 Automatic File Management

**Loading Priority (via `strava_files.py`):**
1. Latest files (`*_latest.json`) - if available
2. Config-specified files - fallback
3. Timestamped files - historical versions
4. Error handling - graceful degradation

**Benefits:**
- ✅ Consistent file handling across all scripts
- ✅ Automatic backup and versioning
- ✅ Unicode filename support
- ✅ Atomic file operations with error recovery

## Major Refactoring Improvements (2025-07-01)

### Code Quality Improvements

**Eliminated Code Duplication (950+ lines removed):**
- Configuration loading: ~150 lines centralized
- Rate limit checking: ~180 lines unified
- Authentication handling: ~140 lines standardized
- File operations: ~200 lines consolidated
- Progress reporting: ~80 lines unified
- Error handling: ~75 lines standardized

**Enhanced Functionality:**
- 47% code reduction in main scripts while adding features
- Unified error handling and keyboard interrupt support
- Real-time progress reporting with ETA
- Data validation and integrity checking
- Processing time estimation and optimization

### New Utility Architecture Benefits

**Maintainability:**
- Single responsibility principle applied to all utilities
- Consistent API patterns across modules
- Centralized configuration management
- Easy unit testing of individual components

**Reliability:**
- Robust error handling with automatic recovery
- Keyboard-interruptible operations (1-second response time)
- Data validation and integrity checking
- Automatic retry mechanisms with exponential backoff

**Performance:**
- Optimized file operations with streaming
- Memory-efficient data processing
- Automatic resolution optimization
- Progress tracking with minimal overhead

## Testing and Validation

### ✅ Comprehensive Testing Results

**Module Integration:**
- ✅ All utility modules import and instantiate successfully
- ✅ All refactored scripts compile without syntax errors
- ✅ Configuration management works across all entry points
- ✅ File operations maintain backward compatibility

**Production Validation:**
- ✅ 8+ years of Strava data (93 activities, 552,019 GPS points)
- ✅ Geographic coverage: North America (36.6°N-47.7°N, 122.5°W-90.5°W)
- ✅ Multiple activity types: cycling, hiking, running, skiing, mountain biking
- ✅ Professional-grade SVG output with geographic boundaries

**Error Handling:**
- ✅ Graceful handling of missing files and malformed data
- ✅ Automatic token refresh and rate limit management
- ✅ Safe interruption and resume capabilities
- ✅ Comprehensive error reporting and debugging information

## Implementation Notes

### Geographic Processing
- Map data cached locally in `map_cache/` directory
- SVG uses equirectangular projection with aspect ratio correction
- Automatic boundary detection based on GPS coordinate intersection
- Support for world borders and US state boundaries

### Performance Optimizations
- Activity filtering by type (excludes indoor activities via `strava_utils.py`)
- Automatic grid resolution optimization based on data density
- Memory-efficient streaming processing for large datasets
- Progressive rendering with real-time feedback

### Security and Privacy
- All sensitive data stored locally (no cloud dependencies)
- API credentials automatically excluded from version control
- Token encryption and secure storage practices
- User data privacy maintained throughout processing

## Development Guidelines

### When Working with This Codebase

**Use the Utility Modules:**
- Always use `strava_config.py` for configuration management
- Use `strava_files.py` for any file operations
- Use `strava_progress.py` for user feedback
- Use `heatmap_utils.py` for GPS data validation

**Code Patterns:**
- Follow the established error handling patterns
- Use keyboard interrupt handlers for long operations
- Implement progress reporting for operations > 5 seconds
- Validate data before processing

**Testing:**
- Test utility modules independently
- Verify configuration management works correctly
- Test error conditions and recovery scenarios
- Validate file format compatibility

### Extension Points

**Adding New Features:**
- Extend `strava_utils.py` for new helper functions
- Add validation to `heatmap_utils.py` for new data types
- Extend `strava_progress.py` for new progress reporting needs
- Use `strava_config.py` for new configuration options

**Performance Improvements:**
- Optimize algorithms in `heatmap_generator.py`
- Enhance caching in `map_data.py`
- Improve streaming in `strava_files.py`
- Add parallel processing where appropriate

This refactored architecture provides a solid foundation for future development while maintaining the robustness and functionality that has been proven with large-scale real-world data processing.