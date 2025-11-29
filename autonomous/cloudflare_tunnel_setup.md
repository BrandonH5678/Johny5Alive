# Cloudflare Tunnel Setup for J5A

## Installation Status
- **Date:** 2025-11-29
- **cloudflared Version:** 2025.11.1
- **Location:** j5a-server (192.168.0.119)

## Current Configuration

### Quick Tunnel (Testing/Development)
Quick Tunnels provide temporary public URLs without a Cloudflare account.

**Start a Quick Tunnel:**
```bash
ssh j5a-server "cloudflared tunnel --protocol http2 --url http://localhost:11434"
```

**Current Test URL:** `https://february-rings-bronze-exp.trycloudflare.com`

**Note:** Quick Tunnel URLs are temporary and change each time the tunnel restarts.

### Exposed Services
| Service | Local Port | Purpose |
|---------|-----------|---------|
| Ollama API | 11434 | LLM inference (Qwen, Llama, etc.) |
| Web Server | 8000/8080 | Various web services |

## Known Limitations

### Quick Tunnel Bot Protection
Cloudflare applies bot protection to Quick Tunnels. Automated requests (curl, scripts) may receive 403 responses. Browser access works normally.

**Workarounds:**
1. Use browser for testing
2. Upgrade to Named Tunnel with Cloudflare account
3. Add custom tunnel configuration

### ICMP Proxy Warning
```
Group ID 1000 is not between ping group 1 to 0
```
This warning is informational only - ICMP proxy is not required for HTTP tunnels.

## Production Setup (Phase 2+)

For production use, set up a Named Tunnel:

1. Create Cloudflare account (free)
2. Login: `cloudflared login`
3. Create tunnel: `cloudflared tunnel create j5a-tunnel`
4. Configure: Create `~/.cloudflared/config.yml`
5. Install as service: `sudo cloudflared service install`

### Sample config.yml
```yaml
tunnel: j5a-tunnel
credentials-file: /home/johnny5/.cloudflared/<tunnel-id>.json

ingress:
  - hostname: ollama.yourdomain.com
    service: http://localhost:11434
  - hostname: api.yourdomain.com
    service: http://localhost:8000
  - service: http_status:404
```

## Testing Commands

```bash
# Check tunnel status
ssh j5a-server "pgrep -a cloudflared"

# View tunnel logs
ssh j5a-server "tail -f /tmp/cloudflared_quicktunnel.log"

# Test local Ollama
ssh j5a-server "curl -s http://localhost:11434/"

# List Ollama models
ssh j5a-server "curl -s http://localhost:11434/api/tags"
```

## Integration with J5A

The tunnel enables:
1. **Remote Access:** Access j5a-server services from anywhere
2. **DIY Platform:** Future hosting of Cal.com, customer portal
3. **API Exposure:** Controlled external access to J5A services
4. **Multi-Device:** iPad/mobile access to server resources

## Security Notes

- Quick Tunnels have no uptime guarantee
- For production, use Named Tunnels with access policies
- Consider Cloudflare Access for authentication
- Never expose sensitive services without proper auth
