# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python application that downloads GPS data from Strava and generates SVG heatmaps visualizing activity routes. The application consists of two main scripts and several supporting modules.

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
python download_strava_data.py
```
- Downloads GPS data from Strava API
- Creates `config.json` on first run (needs manual configuration)
- Automatically handles token refresh and rate limiting
- Saves data to `strava_data/` directory

### Heatmap Generation
```bash
python generate_heatmap_svg.py
```
- Generates SVG heatmap from downloaded data
- Creates `strava_heatmap.svg` output file

### Testing and Development
```bash
# Test authentication and token refresh
python test_auth.py

# Test rate limiting functionality
python test_rate_limit.py

# Get new tokens with OAuth flow
python get_refresh_token.py

# Check rate limit status
python check_rate_limit.py

# Download with automatic rate limit handling
python wait_and_download.py
```

## Architecture

### Core Components

**Entry Points:**
- `download_strava_data.py`: Downloads GPS data from Strava API
- `generate_heatmap_svg.py`: Generates heatmaps from downloaded data

**Core Modules:**
- `strava_client.py`: Handles Strava API authentication, activity retrieval, and GPS data extraction
- `heatmap_generator.py`: Converts GPS points to heatmap grid using Bresenham line algorithm
- `map_data.py`: Downloads and caches geographic boundary data (world borders, US states) from external APIs
- `svg_renderer.py`: Creates SVG visualizations with equirectangular projection

### Data Flow

1. **Authentication**: OAuth flow with Strava API, stores tokens in `config.json`
2. **Download**: Fetches all activities, filters GPS-enabled ones, extracts coordinate streams
3. **Processing**: Maps GPS coordinates to grid using configurable resolution, traces paths between points
4. **Visualization**: Projects coordinates to SVG space, overlays boundaries, renders as paths

### Configuration

All settings managed through `config.json`:
- Strava API credentials (client_id, client_secret, access_token, refresh_token)
- File paths and directories
- SVG output dimensions and styling
- Track and boundary colors/widths

**Required config.json structure:**
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
  }
}
```

### Dependencies

- `requests`: HTTP client for API calls
- `numpy`: Numerical operations for heatmap grid
- Built-in libraries: `xml.etree.ElementTree`, `json`, `os`, `math`

## Implementation Notes

- Geographic data cached locally in `map_cache/` directory
- SVG uses equirectangular projection with aspect ratio correction
- Boundary detection uses coordinate intersection with activity bounds
- GPS tracks filtered by activity type (excludes indoor activities)

## Recent Improvements (2025-07-01)

### Enhanced Strava API Client

**Automatic Token Management:**
- `StravaClient` now supports refresh_token parameter and config_file path
- Automatic access token refresh on 401 errors using refresh tokens
- Updated tokens automatically saved back to config.json
- `_refresh_access_token()` and `_save_tokens_to_config()` methods added

**Advanced Rate Limiting:**
- `StravaRateLimiter` class implements Strava's official limits:
  - 15-minute limit: 100 requests
  - Daily limit: 1000 requests
- Automatic waiting when limits are reached with countdown display
- Real-time tracking of request counts and reset times
- Server-side rate limit handling (429 errors) with 60-second retry

**Error Handling:**
- Robust 401 (unauthorized) error handling with automatic token refresh
- 429 (rate limit) error handling with automatic retry
- Method name conflict resolution (`refresh_token` vs `refresh_token_method`)

### New Test Scripts

- `test_auth.py`: Tests authentication, token refresh, and basic API calls
- `test_rate_limit.py`: Tests rate limiting functionality and request tracking  
- `get_refresh_token.py`: OAuth flow helper to obtain fresh tokens

### Updated Integration

- `download_strava_data.py` updated to use new StravaClient parameters
- Rate limiting logic moved from manual delays to integrated rate limiter
- All Strava API calls now benefit from automatic token refresh and rate limiting

### Virtual Environment Setup

- Documented venv creation and activation process
- Confirmed compatibility with Python 3.9.6
- All dependencies (requests>=2.25.0, numpy>=1.21.0) properly installed

## Testing and Validation (2025-07-01)

### ✅ Comprehensive Testing Completed

**Authentication and Token Management:**
- ✅ New tokens obtained with correct `activity:read_all` scope
- ✅ Automatic token refresh functionality verified
- ✅ Token persistence to config.json confirmed

**Rate Limiting Resolution:**
- ✅ Identified and fixed infinite loop in `StravaRateLimiter.wait_if_needed()`
- ✅ Server-side rate limit detection and automatic waiting implemented
- ✅ Rate limit reset timing (every 15 minutes at :00, :15, :30, :45) confirmed

**Data Download Success:**
- ✅ Sample data download completed: 3 activities, 12,899 GPS points
- ✅ Files saved to `strava_data/` directory:
  - `gps_data.json` (603,452 bytes) - GPS coordinates in [lat, lon] format
  - `athlete_info.json` (846 bytes) - User profile information
- ✅ Rate limit usage tracked: 5/100 requests used

### 🔧 Production-Ready Improvements

**Enhanced download_strava_data.py:**
- Added pre-flight rate limit checking with automatic waiting
- Improved error handling with detailed traceback
- Added download summary with GPS point counts and rate limit usage
- Integrated server-side rate limit detection (429 errors)

**Robust Error Handling:**
- Server rate limit (429) detection and automatic retry
- Token expiration (401) handling with automatic refresh
- Comprehensive error reporting and debugging information

### 📂 Current Project Status

**Ready for Production:**
- ✅ All authentication and rate limiting issues resolved
- ✅ Sample GPS data successfully downloaded and saved
- ✅ Ready for full dataset download or heatmap generation

**Next Steps:**
1. Run `python download_strava_data.py` for full data download
2. Run `python generate_heatmap_svg.py` for heatmap creation
3. Use test scripts for debugging: `test_auth.py`, `test_rate_limit.py`

**Current Data:**
- Location: `strava_data/` directory
- Sample activities: 3 bike rides from Minnesota area
- GPS coverage: Mix of lunch rides and evening rides with high-resolution tracking

## File Management System (2025-07-01)

### 📁 Timestamped File Naming

**GPS Data Files:**
- Format: `gps_data_YYYYMMDD_HHMMSS.json`
- Example: `gps_data_20250630_203000.json`
- Contains: GPS coordinates in [latitude, longitude] format

**Athlete Info Files:**
- Format: `athlete_info_YYYYMMDD_HHMMSS.json` 
- Example: `athlete_info_20250630_203000.json`
- Contains: User profile and account information

**Latest File Versions:**
- `gps_data_latest.json` - Always points to most recent GPS data
- `athlete_info_latest.json` - Always points to most recent athlete info
- Used by `generate_heatmap_svg.py` for automatic file loading

### 🔄 File Loading Priority

Scripts automatically load files in this order:
1. **Latest files** (`*_latest.json`) - if available
2. **Config-specified files** - fallback option
3. **Error** - if no files found

This system ensures:
- ✅ Historical data preservation with timestamps
- ✅ Easy access to current data via latest files
- ✅ Safe filename generation (ASCII only, no special characters)
- ✅ Automatic file discovery by other scripts