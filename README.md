# Power Manager Bot

A bot to monitor electricity usage data from a Nature.global Remo Lite device.

## Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Get your API token:**
   - Visit https://home.nature.global/ and log in
   - Generate an access token
   - Copy the token

3. **Configure environment:**
   ```bash
   cp .env.example .env
   ```
   Then edit `.env` and add your access token:
   ```
   NATURE_API_TOKEN=your_actual_token_here
   ```

4. **Run the bot:**
   ```bash
   python power_monitor.py
   ```

## API Information

- **Base URL:** https://api.nature.global
- **Authentication:** OAuth 2.0 Bearer token
- **Rate Limit:** 30 requests per 5 minutes
- **Documentation:** https://developer.nature.global/en/

## Notes

- The Remo Lite device only supports the Cloud API (no Local API)
- API responses are in JSON format
- Monitor rate limit headers: `X-Rate-Limit-Limit`, `X-Rate-Limit-Remaining`, `X-Rate-Limit-Reset`

