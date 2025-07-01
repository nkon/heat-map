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

### Individual Activity Management (2025-07-01)

**New Scripts and Workflows:**
- `download_individual_activities.py`: Downloads each activity as separate JSON file
- `consolidate_gps_data.py`: Merges individual activity files into unified GPS dataset
- Individual activity files saved with format: `activity_YYYYMMDD_ID_activityname.json`
- Automatic generation of `*_latest.json` files for compatibility

**Data Processing Pipeline:**
1. Download individual activities with rate limiting
2. Save each activity with GPS points in separate files
3. Consolidate all activities into unified GPS data dictionary
4. Generate heatmap from consolidated data

### New Test Scripts

- `check_rate_limit.py`: Real-time API rate limit status checking
- `get_refresh_token.py`: OAuth flow helper to obtain fresh tokens
- `wait_and_download.py`: Download with automatic rate limit handling

### Updated Integration

- `download_strava_data.py` updated to use new StravaClient parameters
- Rate limiting logic moved from manual delays to integrated rate limiter
- All Strava API calls now benefit from automatic token refresh and rate limiting
- `generate_heatmap_svg.py` now loads from `*_latest.json` files automatically

### Virtual Environment Setup

- Documented venv creation and activation process
- Confirmed compatibility with Python 3.9.6 and 3.12
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

**Large-Scale Data Processing (2025-07-01):**
- ✅ Successfully processed 93 individual activity files
- ✅ Consolidated 552,019 GPS points from 8+ years of activities
- ✅ Geographic coverage: North America (36.6°N-47.7°N, 122.5°W-90.5°W)
- ✅ Activity types: Cycling, hiking, running, nordic skiing, mountain biking
- ✅ Files successfully saved to `strava_data/` directory

**Heatmap Generation Success:**
- ✅ SVG heatmap generated successfully (1200x800px)
- ✅ Geographic boundaries loaded and filtered (71 boundary paths)
- ✅ GPS data properly projected with equirectangular projection
- ✅ Output file: `strava_heatmap.svg`

### 🔧 Production-Ready Improvements

**Enhanced Data Pipeline:**
- Individual activity download with timestamped filenames
- GPS data consolidation from individual files to unified format
- Automatic generation of `*_latest.json` compatibility files
- Robust error handling for missing or malformed activity files

**Robust Error Handling:**
- Server rate limit (429) detection and automatic retry
- Token expiration (401) handling with automatic refresh
- Data format validation and conversion between individual/consolidated formats
- Comprehensive error reporting and debugging information

### 📂 Current Project Status

**Production-Ready System:**
- ✅ 8+ years of Strava data successfully processed
- ✅ 552,019 GPS points consolidated and mapped
- ✅ High-quality SVG heatmap generated
- ✅ All authentication, rate limiting, and data processing issues resolved

**Data Processing Results:**
- Total activities processed: 93
- Geographic coverage: Western/Midwestern United States
- Activity date range: 2024-07 to 2025-06
- File format: Individual JSON files with consolidated GPS dataset
- Output quality: Professional-grade SVG with geographic boundaries

**Next Steps for Users:**
1. Use `python check_rate_limit.py` to monitor API usage
2. Run `python download_individual_activities.py` for new data
3. Use `python consolidate_gps_data.py` to update consolidated dataset
4. Generate updated heatmaps with `python generate_heatmap_svg.py`

## File Management System (2025-07-01)

### 📁 Individual Activity Files

**Individual Activity Format:**
- Format: `activity_YYYYMMDD_ACTIVITYID_activityname.json`
- Example: `activity_20250629_14957284575_ランチタイム ライド.json`
- Contains: Complete activity data including GPS points, metadata, and activity info
- Structure: `{"activity_id": int, "activity_type": str, "activity_name": str, "start_date": str, "gps_points": [[lat, lon], ...]}`

**Consolidated GPS Data Files:**
- Format: `gps_data.json` and `gps_data_latest.json`
- Structure: `{"activity_id": [[lat, lon], ...], ...}` (dictionary format)
- Contains: All GPS coordinates organized by activity ID
- Used by: `generate_heatmap_svg.py` for heatmap generation

**Athlete Info Files:**
- Format: `athlete_info_latest.json`
- Contains: User profile and account information
- Used by: `generate_heatmap_svg.py` for attribution

### 🔄 Data Processing Workflow

**Step 1: Individual Download**
```bash
python download_individual_activities.py
```
- Downloads each activity as separate JSON file
- Preserves complete activity metadata
- Safe for incremental updates

**Step 2: Data Consolidation**
```bash
python consolidate_gps_data.py
```
- Reads all `activity_*.json` files
- Extracts GPS points from each activity
- Creates consolidated dictionary: `{activity_id: [[lat,lon], ...]}`
- Saves as `gps_data.json` and `gps_data_latest.json`

**Step 3: Heatmap Generation**
```bash
python generate_heatmap_svg.py
```
- Loads consolidated GPS data
- Generates heatmap grid from all GPS points
- Renders SVG with geographic boundaries

### 🔄 File Loading Priority

Scripts automatically load files in this order:
1. **Latest files** (`*_latest.json`) - if available
2. **Config-specified files** - fallback option
3. **Error** - if no files found

This system ensures:
- ✅ Historical data preservation with individual activity files
- ✅ Easy access to current data via latest files
- ✅ Safe filename generation (handles Unicode activity names)
- ✅ Automatic file discovery by other scripts
- ✅ Robust data format conversion between individual and consolidated formats